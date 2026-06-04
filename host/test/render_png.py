"""
Desktop PNG renderer for .aks files.

Mimics the MCU pipeline in Python:
  UTF-8 string → segmenter (rule table from .aks) → binary search lookup
  → bitmap blit → PIL image

Run:
    cd host
    uv run python test/render_png.py /tmp/noto_kannada_regular_24.aks [output.png]
    uv run python test/render_png.py /tmp/noto_kannada_regular_24.aks out.png --bpp 2
    uv run pytest test/render_png.py -v          # headless assertions only
"""

from __future__ import annotations

import argparse
import math
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── Struct formats (must match packer.py) ────────────────────────────────────

_HDR_FMT  = "<IBBBBHBBIIII"
_RULE_FMT = "<IIIIIIIBxxx"
_KEY_FMT  = "<4IIHBB"
_HDR_SIZE  = struct.calcsize(_HDR_FMT)
_RULE_SIZE = struct.calcsize(_RULE_FMT)
_KEY_SIZE  = struct.calcsize(_KEY_FMT)
_AKS_MAGIC = 0x56414741

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AksHeader:
    bpp: int
    glyph_height: int
    baseline: int
    cluster_count: int
    lookup_offset: int
    bitmap_offset: int

@dataclass(frozen=True)
class RuleTable:
    consonant_start: int
    consonant_end: int
    virama: int
    vowel_sign_start: int
    vowel_sign_end: int
    modifier_start: int
    modifier_end: int
    max_conjunct_depth: int

@dataclass(frozen=True)
class KeyEntry:
    cp: tuple[int, int, int, int]   # zero-padded to 4
    bitmap_off: int
    advance: int
    width: int
    bearing_x: int                  # stored as uint8; cast to int8 for use


# ── .aks reader ───────────────────────────────────────────────────────────────

class AksReader:
    """
    Loads a .aks file into memory, mirroring the MCU akshara_init() behaviour.

    Key table is fully loaded (as on MCU). Bitmaps are read on demand.
    """

    def __init__(self, path: str | Path) -> None:
        self._data = Path(path).read_bytes()
        self._hdr, self._rules = self._parse_header()
        self._keys: list[KeyEntry] = self._load_key_table()

    def _parse_header(self) -> tuple[AksHeader, RuleTable]:
        d = self._data
        if len(d) < _HDR_SIZE:
            raise ValueError("file too small for header")

        magic, version, _sid, _weight, bpp, gh, baseline, _, count, _, lut_off, bmap_off = \
            struct.unpack_from(_HDR_FMT, d, 0)

        if magic != _AKS_MAGIC:
            raise ValueError(f"bad magic: 0x{magic:08X}")

        rule_off = _HDR_SIZE
        cs, ce, virama, vs_s, vs_e, mod_s, mod_e, depth = \
            struct.unpack_from(_RULE_FMT, d, rule_off)

        hdr = AksHeader(bpp=bpp, glyph_height=gh, baseline=baseline,
                        cluster_count=count, lookup_offset=lut_off,
                        bitmap_offset=bmap_off)
        rules = RuleTable(consonant_start=cs, consonant_end=ce, virama=virama,
                          vowel_sign_start=vs_s, vowel_sign_end=vs_e,
                          modifier_start=mod_s, modifier_end=mod_e,
                          max_conjunct_depth=depth)
        return hdr, rules

    def _load_key_table(self) -> list[KeyEntry]:
        d = self._data
        off = self._hdr.lookup_offset
        entries: list[KeyEntry] = []
        for _ in range(self._hdr.cluster_count):
            cp0, cp1, cp2, cp3, bmap_off, adv, w, bx = \
                struct.unpack_from(_KEY_FMT, d, off)
            off += _KEY_SIZE
            entries.append(KeyEntry(
                cp=(cp0, cp1, cp2, cp3),
                bitmap_off=bmap_off,
                advance=adv,
                width=w,
                bearing_x=bx if bx < 128 else bx - 256,  # uint8 → int8
            ))
        return entries

    def lookup(self, cluster: tuple[int, ...]) -> KeyEntry | None:
        """Binary search for a cluster. Returns None on miss (OOV)."""
        # Zero-pad to 4 elements.
        key = tuple(list(cluster) + [0] * (4 - len(cluster)))

        lo, hi = 0, len(self._keys) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            e = self._keys[mid]
            if e.cp == key:
                return e
            if e.cp < key:
                lo = mid + 1
            else:
                hi = mid - 1
        return None

    def bitmap_pixels(self, entry: KeyEntry) -> list[list[int]]:
        """
        Decode a bitmap entry to an 8-bit greyscale 2D list (rows × cols).

        0 = black ink, 255 = white background.
        """
        h = self._hdr
        bpp = h.bpp
        w = entry.width
        gh = h.glyph_height
        abs_off = h.bitmap_offset + entry.bitmap_off

        if bpp == 1:
            stride = math.ceil(w / 8)
        else:
            stride = math.ceil(w / 4)

        buf = self._data[abs_off: abs_off + stride * gh]
        pixels: list[list[int]] = []

        for row in range(gh):
            row_buf = buf[row * stride: (row + 1) * stride]
            row_pixels: list[int] = []
            for col in range(w):
                if bpp == 1:
                    bit = (row_buf[col // 8] >> (7 - col % 8)) & 1
                    row_pixels.append(0 if bit else 255)
                else:
                    byte = row_buf[col // 4]
                    level = (byte >> (6 - 2 * (col % 4))) & 0x03
                    # 0=white, 3=black (inverted from pack_canvas which uses 0=black)
                    row_pixels.append(255 - level * 85)
            pixels.append(row_pixels)
        return pixels

    @property
    def header(self) -> AksHeader:
        return self._hdr

    @property
    def rules(self) -> RuleTable:
        return self._rules


# ── Reference segmenter (mirrors MCU segmenter.c spec) ───────────────────────

def segment(text: str, rules: RuleTable) -> list[tuple[int, ...]]:
    """
    Segment a UTF-8 string into akshara clusters.

    Grammar (from spec):
        cluster = consonant (virama consonant)* vowel_sign? modifier?
                | any_other_codepoint   ← single-codepoint cluster

    Greedy left-to-right parse; virama is checked before the coarse
    vowel_sign range because the range includes virama.
    """
    cps = [ord(c) for c in text]
    clusters: list[tuple[int, ...]] = []
    i = 0

    def is_consonant(cp: int) -> bool:
        return rules.consonant_start <= cp <= rules.consonant_end

    def is_vowel_sign(cp: int) -> bool:
        # Virama is inside the coarse range but handled separately above.
        return (rules.vowel_sign_start <= cp <= rules.vowel_sign_end
                and cp != rules.virama)

    def is_modifier(cp: int) -> bool:
        return rules.modifier_start <= cp <= rules.modifier_end

    while i < len(cps):
        cp = cps[i]

        if is_consonant(cp):
            current = [cp]
            i += 1

            # Absorb (virama + consonant) pairs up to max_conjunct_depth.
            depth = 0
            while (depth < rules.max_conjunct_depth
                   and i < len(cps) and cps[i] == rules.virama
                   and i + 1 < len(cps) and is_consonant(cps[i + 1])):
                current += [cps[i], cps[i + 1]]
                i += 2
                depth += 1

            # Terminal virama (halant form) — absorb but stop here.
            if i < len(cps) and cps[i] == rules.virama:
                current.append(cps[i])
                i += 1
                clusters.append(tuple(current))
                continue

            # Optional vowel sign.
            if i < len(cps) and is_vowel_sign(cps[i]):
                current.append(cps[i])
                i += 1

            # Optional modifier.
            if i < len(cps) and is_modifier(cps[i]):
                current.append(cps[i])
                i += 1

            clusters.append(tuple(current))

        else:
            # Independent vowel, digit, punctuation, etc.
            clusters.append((cp,))
            i += 1

    return clusters


# ── Renderer ──────────────────────────────────────────────────────────────────

# PAD between rendered lines and after each side.
_LINE_PAD = 6
# Width reserved for the index label column.
_LABEL_COL = 36

def render_string(
    reader: AksReader,
    text: str,
) -> tuple[Image.Image, int, int]:
    """
    Render one string to a PIL greyscale image.

    Returns (image, rendered_width, oov_count).
    rendered_width is the actual pen advance (not image width).
    """
    h = reader.header
    rules = reader.rules
    clusters = segment(text, rules)

    # First pass: measure total width and collect entries.
    pen_x = 0
    draws: list[tuple[int, KeyEntry]] = []  # (x, entry)
    oov = 0
    for cluster in clusters:
        entry = reader.lookup(cluster)
        if entry is None:
            # OOV: try each codepoint individually, but keep consonant+sign pairs
            # together — standalone vowel signs have no .aks entry, only C+sign pairs do.
            rules = reader.rules
            cps = list(cluster)
            j = 0
            while j < len(cps):
                cp = cps[j]
                is_cons = rules.consonant_start <= cp <= rules.consonant_end
                next_cp = cps[j + 1] if j + 1 < len(cps) else None
                next_is_sign = next_cp is not None and (
                    (rules.vowel_sign_start <= next_cp <= rules.vowel_sign_end
                     and next_cp != rules.virama)
                    or (rules.modifier_start <= next_cp <= rules.modifier_end)
                )
                if is_cons and next_is_sign:
                    e = reader.lookup((cp, next_cp))
                    if e is not None:
                        draws.append((pen_x, e))
                        pen_x += e.advance
                        j += 2
                        continue
                e = reader.lookup((cp,))
                if e is not None:
                    draws.append((pen_x, e))
                    pen_x += e.advance
                else:
                    # Totally unknown — advance by a space-width estimate.
                    pen_x += h.glyph_height // 2
                    oov += 1
                j += 1
        else:
            draws.append((pen_x, entry))
            pen_x += entry.advance

    img_w = max(pen_x, 1)
    img_h = h.glyph_height
    img = Image.new("L", (img_w, img_h), 255)

    for x, entry in draws:
        px_grid = reader.bitmap_pixels(entry)
        glyph_img = Image.new("L", (entry.width, h.glyph_height), 255)
        for row_idx, row in enumerate(px_grid):
            for col_idx, val in enumerate(row):
                glyph_img.putpixel((col_idx, row_idx), val)
        dest_x = x + entry.bearing_x
        img.paste(glyph_img, (max(0, dest_x), 0))

    return img, pen_x, oov


def render_grid(
    reader: AksReader,
    strings: list[tuple[str, str]],   # (label, text)
    output: Path,
    scale: int = 1,
) -> None:
    """
    Render a grid of strings, one per row: index | Kannada text | label.
    """
    h = reader.header
    row_h = h.glyph_height + _LINE_PAD * 2

    # Measure max rendered width for grid sizing.
    max_render_w = 0
    rendered_rows: list[tuple[Image.Image, int, int, str]] = []
    for label, text in strings:
        img, w, oov = render_string(reader, text)
        max_render_w = max(max_render_w, w)
        rendered_rows.append((img, w, oov, label))

    label_font_size = max(9, h.glyph_height // 3)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            label_font_size,
        )
    except OSError:
        font = ImageFont.load_default()

    render_col_w = max_render_w + _LINE_PAD * 2
    label_col_w = 200
    total_w = _LABEL_COL + render_col_w + label_col_w
    total_h = row_h * len(strings) + _LINE_PAD

    canvas = Image.new("L", (total_w * scale, total_h * scale), 255)
    draw = ImageDraw.Draw(canvas)

    for row_idx, (img, w, oov, label) in enumerate(rendered_rows):
        y = row_idx * row_h + _LINE_PAD

        # Row separator line.
        if row_idx > 0:
            draw.line(
                [(0, row_idx * row_h * scale),
                 (total_w * scale, row_idx * row_h * scale)],
                fill=220,
            )

        # Index number.
        draw.text(
            (2 * scale, (y + h.glyph_height // 4) * scale),
            str(row_idx + 1),
            fill=140,
            font=font,
        )

        # Rendered Kannada text (upscaled by paste with resize).
        if scale == 1:
            canvas.paste(img, (_LABEL_COL, y))
        else:
            big = img.resize((img.width * scale, img.height * scale),
                             resample=Image.NEAREST)
            canvas.paste(big, (_LABEL_COL * scale, y * scale))

        # Label text.
        oov_note = f" ({oov} OOV)" if oov else ""
        draw.text(
            ((_LABEL_COL + render_col_w + 4) * scale, (y + h.glyph_height // 4) * scale),
            label + oov_note,
            fill=80,
            font=font,
        )

    canvas.save(output)
    print(f"Saved → {output}  ({len(strings)} strings, {total_w}×{total_h}px)")


# ── Test strings ──────────────────────────────────────────────────────────────

# 25 real Kannada strings covering: bare consonants, vowel signs, conjuncts,
# modifiers, digits mixed with script, and common vocabulary.
TEST_STRINGS: list[tuple[str, str]] = [
    ("Kannada (script name)",  "ಕನ್ನಡ"),
    ("India",                  "ಭಾರತ"),
    ("Hello/Namaskara",        "ನಮಸ್ಕಾರ"),
    ("Thank you",              "ಧನ್ಯವಾದ"),
    ("Bengaluru",              "ಬೆಂಗಳೂರು"),
    ("Mysore",                 "ಮೈಸೂರು"),
    ("Hubli",                  "ಹುಬ್ಬಳ್ಳಿ"),
    ("Ramayana",               "ರಾಮಾಯಣ"),
    ("Mahabharata",            "ಮಹಾಭಾರತ"),
    ("Sanskrit",               "ಸಂಸ್ಕೃತ"),
    ("Love",                   "ಪ್ರೀತಿ"),
    ("Science",                "ವಿಜ್ಞಾನ"),
    ("Technology",             "ತಂತ್ರಜ್ಞಾನ"),
    ("Akshara (letter)",       "ಅಕ್ಷರ"),
    ("Literature",             "ಸಾಹಿತ್ಯ"),
    ("Music",                  "ಸಂಗೀತ"),
    ("Water",                  "ನೀರು"),
    ("Sun",                    "ಸೂರ್ಯ"),
    ("Moon",                   "ಚಂದ್ರ"),
    ("Earth",                  "ಭೂಮಿ"),
    ("Sky",                    "ಆಕಾಶ"),
    ("Forest",                 "ಕಾಡು"),
    ("River",                  "ನದಿ"),
    ("Gold",                   "ಚಿನ್ನ"),
    ("Silver",                 "ಬೆಳ್ಳಿ"),
    ("Mixed: num + script",    "೧೨೩ ಕನ್ನಡ"),
    ("Mixed: num + script",    "123 ಕನ್ನಡ"),
    ("Punctuation",            "ಕನ್ನಡ, ಭಾರತ."),
]


# ── pytest assertions (run without PIL output) ────────────────────────────────

import pytest  # noqa: E402  (late import so script mode still works without pytest)

_AKS_PATH = Path("/tmp/noto_kannada_regular_24.aks")


@pytest.fixture(scope="module")
def reader() -> AksReader:
    if not _AKS_PATH.exists():
        pytest.skip(f".aks file not found: {_AKS_PATH}")
    return AksReader(_AKS_PATH)


class TestSegmenter:
    def _rules(self, reader: AksReader) -> RuleTable:
        return reader.rules

    def test_bare_consonant(self, reader):
        clusters = segment("ಕ", reader.rules)
        assert clusters == [(0x0C95,)]

    def test_consonant_vowel_sign(self, reader):
        clusters = segment("ಕಾ", reader.rules)
        assert clusters == [(0x0C95, 0x0CBE)]

    def test_conjunct(self, reader):
        # ಕ್ತ = KA VIRAMA TA
        clusters = segment("ಕ್ತ", reader.rules)
        assert clusters == [(0x0C95, 0x0CCD, 0x0CA4)]

    def test_conjunct_with_vowel(self, reader):
        # ಕ್ತಾ = KA VIRAMA TA AA-sign
        clusters = segment("ಕ್ತಾ", reader.rules)
        assert clusters == [(0x0C95, 0x0CCD, 0x0CA4, 0x0CBE)]

    def test_modifier(self, reader):
        # ಕಂ = KA anusvara
        clusters = segment("ಕಂ", reader.rules)
        assert clusters == [(0x0C95, 0x0C82)]

    def test_halant_form(self, reader):
        # ಕ್ = KA VIRAMA (halant)
        clusters = segment("ಕ್", reader.rules)
        assert clusters == [(0x0C95, 0x0CCD)]

    def test_independent_vowel(self, reader):
        clusters = segment("ಅ", reader.rules)
        assert clusters == [(0x0C85,)]

    def test_multi_cluster_word(self, reader):
        # ಕನ್ನಡ = KA | NA VIRAMA NA | DA
        clusters = segment("ಕನ್ನಡ", reader.rules)
        assert len(clusters) == 3
        assert clusters[0] == (0x0C95,)          # ಕ
        assert clusters[1] == (0x0CA8, 0x0CCD, 0x0CA8)  # ನ್ನ
        assert clusters[2] == (0x0CA1,)           # ಡ

    def test_ascii_passthrough(self, reader):
        clusters = segment("abc", reader.rules)
        assert clusters == [(0x61,), (0x62,), (0x63,)]


class TestLookup:
    def test_known_cluster_found(self, reader):
        entry = reader.lookup((0x0C95,))  # ಕ bare consonant
        assert entry is not None
        assert entry.advance > 0
        assert entry.width > 0

    def test_oov_returns_none(self, reader):
        # A codepoint sequence that is not in the Kannada .aks
        entry = reader.lookup((0x0041,))  # Latin A — not in .aks
        assert entry is None

    def test_bitmap_correct_size(self, reader):
        entry = reader.lookup((0x0C95,))
        assert entry is not None
        pixels = reader.bitmap_pixels(entry)
        assert len(pixels) == reader.header.glyph_height
        assert all(len(row) == entry.width for row in pixels)

    def test_bitmap_has_ink(self, reader):
        entry = reader.lookup((0x0C95,))
        assert entry is not None
        pixels = reader.bitmap_pixels(entry)
        # At least one black pixel expected for a visible glyph.
        assert any(px < 128 for row in pixels for px in row)


class TestRenderStrings:
    @pytest.mark.parametrize("label,text", TEST_STRINGS)
    def test_renders_without_error(self, reader, label, text):
        img, width, oov = render_string(reader, text)
        assert img is not None
        assert width > 0, f"{label!r}: zero width render"

    def test_word_width_increases_with_length(self, reader):
        _, short_w, _ = render_string(reader, "ಕ")
        _, long_w, _ = render_string(reader, "ಕನ್ನಡ")
        assert long_w > short_w

    def test_known_strings_zero_oov(self, reader):
        # Words whose clusters are all guaranteed enumerated:
        # no conjuncts, or conjuncts where both consonants are in COMMON_CONSONANTS
        # (ರ ದ ತ ಕ ಗ ನ ಮ).  Words with SA/YA/HA-based conjuncts are intentionally
        # absent here — those are covered by the cluster enumerator's frequency cutoff.
        zero_oov = [
            "ಕನ್ನಡ",   # ಕ | ನ್ನ | ಡ  — ನ+ನ both in COMMON_CONSONANTS
            "ಭಾರತ",    # ಭಾ | ರಾ | ತ  — no conjuncts
            "ಬೆಂಗಳೂರು", # ಬೆಂ | ಗ | ಳೂ | ರು — no conjuncts
            "ನೀರು",    # ನೀ | ರು      — no conjuncts
            "ಕಾಡು",    # ಕಾ | ಡು      — no conjuncts
        ]
        for text in zero_oov:
            _, _, oov = render_string(reader, text)
            assert oov == 0, f"{text!r} had {oov} OOV clusters"


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render Kannada strings from a .aks file to PNG"
    )
    parser.add_argument("aks", help="Path to .aks file")
    parser.add_argument(
        "output", nargs="?",
        default="/tmp/akshara_render.png",
        help="Output PNG path (default: /tmp/akshara_render.png)",
    )
    parser.add_argument(
        "--scale", type=int, default=2, metavar="N",
        help="Pixel scale factor for readability (default: 2)",
    )
    args = parser.parse_args()

    reader = AksReader(args.aks)
    h = reader.header
    print(f"Loaded: {args.aks}")
    print(f"  glyph_height={h.glyph_height}px  baseline={h.baseline}px  "
          f"bpp={h.bpp}  clusters={h.cluster_count}")

    render_grid(reader, TEST_STRINGS, Path(args.output), scale=args.scale)


if __name__ == "__main__":
    # When run as script the sys.argv[0] check avoids confusing pytest.
    if len(sys.argv) > 1 and sys.argv[1] not in ("-v", "--co", "-p"):
        main()
    else:
        print("Usage: python test/render_png.py <path.aks> [output.png] [--scale N]")
        print("       cd host && uv run pytest test/render_png.py -v")
