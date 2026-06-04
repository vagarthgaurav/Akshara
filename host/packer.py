"""
Akshara packer stage.

Writes a .aks binary from rasterized cluster data and validates the result
by re-parsing the file and spot-checking key entries.

File layout: header → rule table → cluster key table → bitmap store.
All multi-byte integers are little-endian.

Usage:
    python -m packer --font NotoSansKannada-Regular.ttf --script kannada --size 24 --bpp 1 --output out.aks
"""

from __future__ import annotations

import argparse
import importlib
import math
import struct
from dataclasses import dataclass
from pathlib import Path

import freetype

from cluster_enum import Cluster, ScriptConfig, from_module
from rasterizer import RasterizedCluster, rasterize_all

# ── Struct formats (all little-endian, packed) ────────────────────────────────

# Header: magic(4) version(1) script_id(1) weight(1) bpp(1) glyph_height(2)
#         baseline(1) _reserved(1) cluster_count(4) rule_offset(4)
#         lookup_offset(4) bitmap_offset(4)
_HDR_FMT = "<IBBBBHBBIIII"
_HDR_SIZE = struct.calcsize(_HDR_FMT)  # 28 bytes

_AKS_MAGIC = 0x414B5348  # "AKSH"
_AKS_VERSION = 1

# Rule table: 7×uint32 + uint8 + 3 padding bytes
_RULE_FMT = "<IIIIIIIBxxx"
_RULE_SIZE = struct.calcsize(_RULE_FMT)  # 32 bytes

# Key entry: cp[4](16) bitmap_off(4) advance(2) width(1) bearing_x(1)
_KEY_FMT = "<4IIHBB"
_KEY_SIZE = struct.calcsize(_KEY_FMT)  # 24 bytes


@dataclass(frozen=True)
class FontBox:
    """Global glyph box derived from FreeType face metrics at a given size."""
    glyph_height: int  # full box height in pixels (ascender + |descender|)
    baseline: int      # rows from box top to baseline (= ascender in pixels)


def get_font_box(font_path: str | Path, size: int) -> FontBox:
    """
    Read FreeType size metrics to determine the canonical glyph box.

    ascender and descender come back in 26.6 fixed-point (divide by 64
    for pixels). descender is negative in FreeType convention.
    """
    face = freetype.Face(str(font_path))
    face.set_pixel_sizes(0, size)
    m = face.size  # SizeMetrics object; values in 26.6 fixed-point
    ascender = m.ascender >> 6        # pixels above baseline
    descender = -(m.descender >> 6)   # pixels below baseline (make positive)
    return FontBox(
        glyph_height=ascender + descender,
        baseline=ascender,
    )


def _pad_bitmap(
    r: RasterizedCluster,
    box: FontBox,
    bpp: int,
) -> bytes:
    """
    Expand a content-cropped bitmap to the full glyph box height.

    r.bearing_y = rows from content top to baseline.
    box.baseline = rows from box top to baseline.
    top_pad    = rows to prepend (blank rows above content).
    bot_pad    = rows to append (blank rows below content).

    If content extends outside the box (shouldn't happen with correct font
    metrics), it is silently clipped.
    """
    top_pad = box.baseline - r.bearing_y
    bot_pad = box.glyph_height - top_pad - r.height

    # Clamp in case a glyph overflows the ascender/descender bounds.
    content_start = max(0, -top_pad)        # first row of r.bitmap to include
    content_rows = min(r.height - content_start,
                       box.glyph_height - max(0, top_pad))
    top_pad = max(0, top_pad)
    bot_pad = max(0, bot_pad)

    if bpp == 1:
        row_stride = math.ceil(r.width / 8)
    else:
        row_stride = math.ceil(r.width / 4)

    blank_row = bytes(row_stride)
    result = bytearray()
    result += blank_row * top_pad
    for row_idx in range(content_start, content_start + content_rows):
        start = row_idx * row_stride
        result += r.bitmap[start: start + row_stride]
    result += blank_row * bot_pad

    # Ensure exact height (rounding can leave us 1 row short/over).
    expected = row_stride * box.glyph_height
    if len(result) < expected:
        result += blank_row * ((expected - len(result)) // row_stride)
    return bytes(result[:expected])


def _cluster_sort_key(cluster: Cluster) -> tuple[int, int, int, int]:
    """Lexicographic uint32[4] sort key (zero-pads to 4 elements)."""
    padded = list(cluster) + [0] * (4 - len(cluster))
    return tuple(padded[:4])  # type: ignore[return-value]


def pack(
    font_path: str | Path,
    cfg: ScriptConfig,
    size: int,
    bpp: int,
    weight: int,
    rasterized: list[tuple[Cluster, RasterizedCluster]],
    output: str | Path,
) -> int:
    """
    Write a .aks binary file. Returns the number of clusters written.

    weight: 0 = Regular, 1 = Bold.
    """
    output = Path(output)
    box = get_font_box(font_path, size)

    # Sort by codepoint sequence (lexicographic uint32[4] comparison).
    sorted_clusters = sorted(rasterized, key=lambda pair: _cluster_sort_key(pair[0]))

    # ── Build bitmap store and key table in one pass ─────────────────────────
    key_entries: list[bytes] = []
    bitmap_store = bytearray()

    for cluster, r in sorted_clusters:
        bitmap = _pad_bitmap(r, box, bpp)
        bitmap_off = len(bitmap_store)
        bitmap_store += bitmap

        cp = list(cluster) + [0] * (4 - len(cluster))
        # bearing_x stored as uint8 (MCU casts to int8_t for signed use).
        bearing_x_u8 = r.bearing_x & 0xFF
        entry = struct.pack(
            _KEY_FMT,
            cp[0], cp[1], cp[2], cp[3],
            bitmap_off,
            r.advance,
            r.width,
            bearing_x_u8,
        )
        key_entries.append(entry)

    cluster_count = len(key_entries)

    # ── Compute section offsets ───────────────────────────────────────────────
    rule_offset = _HDR_SIZE
    lookup_offset = rule_offset + _RULE_SIZE
    bitmap_offset = lookup_offset + cluster_count * _KEY_SIZE

    # ── Pack header ───────────────────────────────────────────────────────────
    header = struct.pack(
        _HDR_FMT,
        _AKS_MAGIC,
        _AKS_VERSION,
        cfg.script_id,
        weight,
        bpp,
        box.glyph_height,
        box.baseline,
        0,               # _reserved
        cluster_count,
        rule_offset,
        lookup_offset,
        bitmap_offset,
    )

    # ── Pack rule table ───────────────────────────────────────────────────────
    rule_table = struct.pack(
        _RULE_FMT,
        cfg.consonant_range[0],
        cfg.consonant_range[1],
        cfg.virama,
        cfg.vowel_sign_range[0],
        cfg.vowel_sign_range[1],
        cfg.modifier_range[0],
        cfg.modifier_range[1],
        cfg.max_conjunct_depth,
    )

    # ── Write file ────────────────────────────────────────────────────────────
    with output.open("wb") as f:
        f.write(header)
        f.write(rule_table)
        for entry in key_entries:
            f.write(entry)
        f.write(bitmap_store)

    return cluster_count


def validate(path: str | Path) -> None:
    """
    Re-parse a .aks file and assert structural invariants.

    Raises ValueError with a descriptive message on any inconsistency.
    """
    path = Path(path)
    data = path.read_bytes()
    file_size = len(data)

    if file_size < _HDR_SIZE:
        raise ValueError(f"file too small for header: {file_size} bytes")

    (magic, version, script_id, weight, bpp,
     glyph_height, baseline, _reserved,
     cluster_count, rule_offset, lookup_offset, bitmap_offset) = struct.unpack_from(
        _HDR_FMT, data, 0,
    )

    if magic != _AKS_MAGIC:
        raise ValueError(f"bad magic: 0x{magic:08X} (expected 0x{_AKS_MAGIC:08X})")
    if version != _AKS_VERSION:
        raise ValueError(f"unsupported version: {version}")
    if bpp not in (1, 2):
        raise ValueError(f"invalid bpp: {bpp}")
    if baseline >= glyph_height:
        raise ValueError(f"baseline {baseline} >= glyph_height {glyph_height}")

    expected_lookup = _HDR_SIZE + _RULE_SIZE
    if lookup_offset != expected_lookup:
        raise ValueError(f"lookup_offset {lookup_offset} != expected {expected_lookup}")

    expected_bitmap = lookup_offset + cluster_count * _KEY_SIZE
    if bitmap_offset != expected_bitmap:
        raise ValueError(
            f"bitmap_offset {bitmap_offset} != expected {expected_bitmap}"
        )

    if file_size < bitmap_offset:
        raise ValueError(
            f"file truncated: {file_size} bytes, bitmap store starts at {bitmap_offset}"
        )

    # Spot-check first, middle, and last key entries.
    check_indices = {0, cluster_count // 2, cluster_count - 1} if cluster_count else set()
    for idx in sorted(check_indices):
        off = lookup_offset + idx * _KEY_SIZE
        cp0, cp1, cp2, cp3, bmap_off, advance, width, bearing_x = struct.unpack_from(
            _KEY_FMT, data, off,
        )
        abs_off = bitmap_offset + bmap_off
        if abs_off >= file_size:
            raise ValueError(
                f"key[{idx}]: bitmap_off {bmap_off} points past end of file"
            )
        if width == 0:
            raise ValueError(f"key[{idx}]: width is 0")
        if advance == 0:
            raise ValueError(f"key[{idx}]: advance is 0")
        # Verify the bitmap bytes for this entry are present.
        if bpp == 1:
            row_stride = math.ceil(width / 8)
        else:
            row_stride = math.ceil(width / 4)
        bitmap_bytes = row_stride * glyph_height
        if abs_off + bitmap_bytes > file_size:
            raise ValueError(
                f"key[{idx}]: bitmap at offset {abs_off} + {bitmap_bytes} bytes "
                f"exceeds file size {file_size}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Pack Akshara clusters into a .aks binary")
    parser.add_argument("--font", required=True, help="Path to TTF/OTF font file")
    parser.add_argument(
        "--script", required=True,
        choices=["kannada", "tamil", "devanagari"],
    )
    parser.add_argument("--size", type=int, default=24, help="Pixel size")
    parser.add_argument("--bpp", type=int, default=1, choices=[1, 2], help="Bits per pixel")
    parser.add_argument("--weight", type=int, default=0, choices=[0, 1],
                        help="0=Regular 1=Bold")
    parser.add_argument("--output", required=True, help="Output .aks file path")
    args = parser.parse_args()

    mod = importlib.import_module(f"scripts.{args.script}")
    cfg = from_module(mod)

    print(f"Rasterizing clusters…")
    rasterized = rasterize_all(args.font, cfg, args.size, args.bpp)
    print(f"  {len(rasterized)} clusters rasterized")

    count = pack(
        font_path=args.font,
        cfg=cfg,
        size=args.size,
        bpp=args.bpp,
        weight=args.weight,
        rasterized=rasterized,
        output=args.output,
    )

    file_size = Path(args.output).stat().st_size
    print(f"  {count} clusters written → {args.output} ({file_size:,} bytes)")

    print("Validating…")
    validate(args.output)
    print("  OK")


if __name__ == "__main__":
    main()
