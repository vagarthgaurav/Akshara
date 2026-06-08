"""
Tests for rasterizer.py.

Run as pytest for unit assertions:
    cd aks-generator && uv run pytest test/test_rasterizer.py -v

Run directly to generate a visual PNG grid:
    cd aks-generator && uv run python test/test_rasterizer.py [output.png] [--size N] [--bpp 1|2]

    --size 24          e-paper (default)
    --size 48 --bpp 2  LCD / AMOLED — smooth anti-aliased rendering
    --bpp 2            4-grey e-paper mode
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pytest

# aks-generator/ is the package root; tests run with cwd=aks-generator/
sys.path.insert(0, str(Path(__file__).parent.parent))

from rasterizer import Rasterizer, RasterizedCluster, _pack_canvas, rasterize_all
from shaper import Shaper
from cluster_enum import from_module
import scripts.kannada as _kan

_FONT = Path("/usr/share/fonts/truetype/noto/NotoSansKannada-Regular.ttf")
_SIZE = 24
_CFG = from_module(_kan)

# A handful of representative clusters for quick testing.
_TEST_CLUSTERS: list[tuple[str, tuple[int, ...]]] = [
    # standalone vowels
    ("ಅ",  (0x0C85,)),
    ("ಆ",  (0x0C86,)),
    ("ಇ",  (0x0C87,)),
    ("ಈ",  (0x0C88,)),
    ("ಉ",  (0x0C89,)),
    # bare consonants
    ("ಕ",  (0x0C95,)),
    ("ಖ",  (0x0C96,)),
    ("ರ",  (0x0CB0,)),
    ("ನ",  (0x0CA8,)),
    ("ಮ",  (0x0CAE,)),
    # consonant + vowel sign
    ("ಕಾ", (0x0C95, 0x0CBE)),   # kā
    ("ಕಿ", (0x0C95, 0x0CBF)),   # ki
    ("ಕೀ", (0x0C95, 0x0CC0)),   # kī
    ("ಕೆ", (0x0C95, 0x0CC6)),   # ke
    ("ಕೊ", (0x0C95, 0x0CCA)),   # ko
    # consonant + virama (halant form)
    ("ಕ್", (0x0C95, 0x0CCD)),
    ("ರ್", (0x0CB0, 0x0CCD)),
    # depth-1 conjuncts
    ("ಕ್ತ", (0x0C95, 0x0CCD, 0x0CA4)),   # kta
    ("ನ್ನ", (0x0CA8, 0x0CCD, 0x0CA8)),   # nna
    ("ರ್ಕ", (0x0CB0, 0x0CCD, 0x0C95)),   # rka
    # conjunct + vowel sign
    ("ಕ್ತಾ", (0x0C95, 0x0CCD, 0x0CA4, 0x0CBE)),  # ktā
    # modifier
    ("ಕಂ", (0x0C95, 0x0C82)),   # ka + anusvara
    ("ಕಃ", (0x0C95, 0x0C83)),   # ka + visarga
    # digits / ASCII
    ("1",  (0x0031,)),
    (".",  (0x002E,)),
]


@pytest.fixture(scope="module")
def rasterizer() -> Rasterizer:
    return Rasterizer(_FONT, _SIZE, bpp=1)


@pytest.fixture(scope="module")
def shaper() -> Shaper:
    return Shaper(_FONT, _CFG, _SIZE)


def _rast(rasterizer: Rasterizer, shaper: Shaper, cps: tuple[int, ...]) -> RasterizedCluster:
    shaped = shaper.shape(cps)
    assert shaped, f"Shaper produced no glyphs for {[hex(c) for c in cps]}"
    r = rasterizer.rasterize(cps, shaped)
    assert r is not None, f"Rasterizer returned None for {[hex(c) for c in cps]}"
    return r


class TestBitmapDimensions:
    def test_bare_consonant_nonzero(self, rasterizer, shaper):
        r = _rast(rasterizer, shaper, (0x0C95,))  # ಕ
        assert r.width > 0 and r.height > 0

    def test_bitmap_byte_count_1bpp(self, rasterizer, shaper):
        r = _rast(rasterizer, shaper, (0x0C95,))
        expected = math.ceil(r.width / 8) * r.height
        assert len(r.bitmap) == expected

    def test_height_within_bounds(self, rasterizer, shaper):
        # Glyph should fit within 2× the requested pixel size.
        for _, cps in _TEST_CLUSTERS:
            r = _rast(rasterizer, shaper, cps)
            assert r.height <= _SIZE * 2, f"{cps}: height {r.height} exceeds 2×size"

    def test_advance_positive(self, rasterizer, shaper):
        for _, cps in _TEST_CLUSTERS:
            r = _rast(rasterizer, shaper, cps)
            assert r.advance > 0, f"{cps}: advance={r.advance}"

    def test_conjunct_wider_than_single(self, rasterizer, shaper):
        single = _rast(rasterizer, shaper, (0x0C95,))        # ಕ
        conjunct = _rast(rasterizer, shaper, (0x0C95, 0x0CCD, 0x0CA4))  # ಕ್ತ
        # A shaped conjunct typically renders as one ligature glyph, so width
        # may not be additive — but advance should be ≥ single consonant.
        assert conjunct.advance >= single.advance

    def test_vowel_sign_changes_bitmap(self, rasterizer, shaper):
        bare = _rast(rasterizer, shaper, (0x0C95,))          # ಕ
        with_sign = _rast(rasterizer, shaper, (0x0C95, 0x0CBE))  # ಕಾ
        # kā must be wider than bare k.
        assert with_sign.width > bare.width


class TestPackCanvas:
    def test_1bpp_all_white(self):
        canvas = [[0, 0, 0, 0, 0, 0, 0, 0]]  # 8 pixels, all off
        result = _pack_canvas(canvas, 8, 1, bpp=1)
        assert result == bytes([0x00])

    def test_1bpp_all_black(self):
        canvas = [[255] * 8]
        result = _pack_canvas(canvas, 8, 1, bpp=1)
        assert result == bytes([0xFF])

    def test_1bpp_msb_first(self):
        canvas = [[255, 0, 0, 0, 0, 0, 0, 0]]  # only leftmost pixel set
        result = _pack_canvas(canvas, 8, 1, bpp=1)
        assert result == bytes([0x80])

    def test_1bpp_row_byte_alignment(self):
        # 9-pixel-wide row → 2 bytes
        canvas = [[255] * 9]
        result = _pack_canvas(canvas, 9, 1, bpp=1)
        assert len(result) == 2
        assert result[0] == 0xFF
        assert result[1] == 0x80  # only MSB of second byte set

    def test_2bpp_levels(self):
        # 4 pixels, one at each greyscale level: 0, 64, 128, 192
        canvas = [[0, 64, 128, 192]]
        result = _pack_canvas(canvas, 4, 1, bpp=2)
        assert len(result) == 1
        # level 0→0b00, 64→0b01, 128→0b10, 192→0b11 → 0b00_01_10_11 = 0x1B
        assert result[0] == 0b00011011

    def test_2bpp_max_level(self):
        canvas = [[255, 255, 255, 255]]
        result = _pack_canvas(canvas, 4, 1, bpp=2)
        assert result == bytes([0xFF])


class TestRasterizeAll:
    def test_count_matches_shaper(self):
        results = rasterize_all(_FONT, _CFG, _SIZE, bpp=1)
        # All 1317 shaped clusters should survive rasterization.
        assert len(results) >= 1300


# ── Visual PNG output (run as script) ────────────────────────────────────────

# 2bpp level → 8-bit greyscale (0=black, 255=white)
_2BPP_TO_GREY = [255, 170, 85, 0]


def _unpack_bitmap(r: RasterizedCluster, bpp: int) -> bytes:
    """Unpack a packed 1bpp or 2bpp bitmap to an 8-bit greyscale bytes object."""
    pixels = bytearray([255] * (r.width * r.height))
    if bpp == 1:
        pitch = math.ceil(r.width / 8)
        for py in range(r.height):
            for px in range(r.width):
                if r.bitmap[py * pitch + px // 8] & (0x80 >> (px % 8)):
                    pixels[py * r.width + px] = 0
    else:  # 2bpp: 4 pixels per byte, 2 bits each, MSB-first
        pitch = math.ceil(r.width / 4)
        for py in range(r.height):
            for px in range(r.width):
                byte = r.bitmap[py * pitch + px // 4]
                level = (byte >> (6 - 2 * (px % 4))) & 0x03
                pixels[py * r.width + px] = _2BPP_TO_GREY[level]
    return bytes(pixels)


def _render_png(output: Path, size: int, bpp: int) -> None:
    from PIL import Image, ImageDraw, ImageFont as PILFont

    rasterizer = Rasterizer(_FONT, size, bpp=bpp)
    shaper = Shaper(_FONT, _CFG, size)

    # Scale cell dimensions with font size so large sizes don't clip.
    CELL_W = max(60, size * 3)
    CELL_H = max(50, size * 2)
    LABEL_H = max(28, size // 2 * 2)  # room for two label lines
    BASELINE = int(CELL_H * 0.72)  # ~72% down the cell
    COLS = 5
    ROWS = math.ceil(len(_TEST_CLUSTERS) / COLS)
    IMG_W = COLS * CELL_W
    IMG_H = ROWS * (CELL_H + LABEL_H)

    img = Image.new("L", (IMG_W, IMG_H), 255)
    draw = ImageDraw.Draw(img)

    label_size = max(10, size // 3)
    try:
        label_font = PILFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", label_size)
    except OSError:
        label_font = PILFont.load_default()

    for idx, (label, cps) in enumerate(_TEST_CLUSTERS):
        col = idx % COLS
        row = idx // COLS
        cell_x = col * CELL_W
        cell_y = row * (CELL_H + LABEL_H)

        shaped = shaper.shape(cps)
        if not shaped:
            continue
        r = rasterizer.rasterize(cps, shaped)
        if r is None:
            continue

        glyph_img = Image.frombytes("L", (r.width, r.height),
                                    _unpack_bitmap(r, bpp), "raw", "L")

        paste_x = cell_x + (CELL_W - r.width) // 2
        paste_y = cell_y + BASELINE - r.height
        paste_y = max(cell_y, min(paste_y, cell_y + CELL_H - r.height))
        img.paste(glyph_img, (paste_x, paste_y))

        hex_parts = [f"{cp:04X}" for cp in cps]
        # Wrap to two lines if more than 2 codepoints to avoid overflowing cell.
        if len(hex_parts) <= 2:
            label_lines = [" ".join(hex_parts)]
        else:
            mid = math.ceil(len(hex_parts) / 2)
            label_lines = [" ".join(hex_parts[:mid]), " ".join(hex_parts[mid:])]
        for li, line in enumerate(label_lines):
            draw.text((cell_x + 2, cell_y + CELL_H + 1 + li * (label_size + 1)),
                      line, fill=80, font=label_font)

    for c in range(COLS + 1):
        draw.line([(c * CELL_W, 0), (c * CELL_W, IMG_H)], fill=200)
    for r_idx in range(ROWS + 1):
        y = r_idx * (CELL_H + LABEL_H)
        draw.line([(0, y), (IMG_W, y)], fill=200)

    img.save(output)
    print(f"Saved → {output}  (size={size}px  bpp={bpp})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render Akshara cluster grid to PNG")
    parser.add_argument("output", nargs="?", default="/tmp/akshara_rasterizer_test.png",
                        help="Output PNG path (default: /tmp/akshara_rasterizer_test.png)")
    parser.add_argument("--size", type=int, default=24,
                        help="Font size in pixels (default: 24; use 48+ for LCD/AMOLED)")
    parser.add_argument("--bpp", type=int, default=1, choices=[1, 2],
                        help="1=monochrome e-paper  2=4-grey e-paper/LCD (default: 1)")
    args = parser.parse_args()
    _render_png(Path(args.output), size=args.size, bpp=args.bpp)
