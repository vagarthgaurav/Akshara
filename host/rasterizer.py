"""
Akshara rasterizer stage.

Renders each shaped cluster (from shaper.py) into a packed bitmap using FreeType.
For 1bpp: FT_LOAD_TARGET_MONO gives hinted monochrome bitmaps directly.
For 2bpp: anti-aliased grey rendering, quantized to 4 levels.

All glyphs in a cluster are composited onto one canvas using max-blend so that
overlapping coverage (e.g. vowel sign over consonant) does not darken.

Usage:
    python -m rasterizer --font NotoSansKannada-Regular.ttf --script kannada --size 24 --bpp 1
    python -m rasterizer --font NotoSansKannada-Regular.ttf --script kannada --size 24 --bpp 1 --count
"""

from __future__ import annotations

import argparse
import importlib
import math
from dataclasses import dataclass
from pathlib import Path

import freetype

from cluster_enum import Cluster, ScriptConfig, from_module
from shaper import GlyphInfo, ShapedCluster, shape_all

# FreeType load flags: RENDER produces a bitmap in the glyph slot.
# TARGET_MONO requests hinted 1bpp monochrome rendering (bitmap.pixel_mode = 1).
# Default RENDER produces 8-bit anti-aliased grey (bitmap.pixel_mode = 2).
_FT_LOAD_RENDER = freetype.FT_LOAD_RENDER
_FT_LOAD_MONO = freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO

# FreeType pixel mode constants (FT_Pixel_Mode enum).
_FT_PIXEL_MODE_MONO = freetype.FT_PIXEL_MODES["FT_PIXEL_MODE_MONO"]
_FT_PIXEL_MODE_GRAY = freetype.FT_PIXEL_MODES["FT_PIXEL_MODE_GRAY"]


@dataclass
class RasterizedCluster:
    bitmap: bytes   # packed 1bpp or 2bpp, rows byte-aligned, MSB-first
    width: int      # bitmap width in pixels
    height: int     # bitmap height in pixels (content only, not full glyph box)
    bearing_x: int  # signed: pen x → left edge of bitmap (can be negative)
    bearing_y: int  # rows from content-top to baseline (positive = baseline below content-top)
    advance: int    # total horizontal advance in pixels


class Rasterizer:
    """FreeType rasterizer for one font face at a fixed pixel size and bpp."""

    def __init__(self, font_path: str | Path, size: int, bpp: int) -> None:
        if bpp not in (1, 2):
            raise ValueError(f"bpp must be 1 or 2, got {bpp}")
        self._face = freetype.Face(str(font_path))
        self._face.set_pixel_sizes(0, size)
        self._bpp = bpp
        self._load_flags = _FT_LOAD_MONO if bpp == 1 else _FT_LOAD_RENDER

    def _render_glyph(
        self, glyph_id: int,
    ) -> tuple[list[list[int]], int, int]:
        """
        Render one glyph to an 8-bit 2D list (rows × cols, values 0–255).

        Returns (pixels, bitmap_left, bitmap_top).
        bitmap_top is pixels above baseline (FreeType convention: positive = up).
        Returns empty pixels list if the glyph has no ink (e.g. space).
        """
        self._face.load_glyph(glyph_id, self._load_flags)
        ft = self._face.glyph
        bm = ft.bitmap
        rows, cols = bm.rows, bm.width

        if rows == 0 or cols == 0:
            return [], ft.bitmap_left, ft.bitmap_top

        buf = bytes(bm.buffer)
        pixels: list[list[int]] = [[0] * cols for _ in range(rows)]
        pitch = abs(bm.pitch)

        if bm.pixel_mode == _FT_PIXEL_MODE_MONO:
            # 1bpp: ceil(cols/8) bytes per row, MSB = leftmost pixel.
            for row in range(rows):
                base = row * pitch
                for col in range(cols):
                    if buf[base + col // 8] & (0x80 >> (col % 8)):
                        pixels[row][col] = 255
        elif bm.pixel_mode == _FT_PIXEL_MODE_GRAY:
            for row in range(rows):
                base = row * pitch
                for col in range(cols):
                    pixels[row][col] = buf[base + col]

        return pixels, ft.bitmap_left, ft.bitmap_top

    def rasterize(
        self, cluster: Cluster, shaped: ShapedCluster,
    ) -> RasterizedCluster | None:
        """
        Composite all glyphs in a shaped cluster into one packed bitmap.

        Coordinate conventions:
          - pen starts at (0, 0); baseline is at y=0.
          - HarfBuzz x_offset/y_offset: positive = right/up.
          - Screen/canvas y: positive = downward.
          - Canvas top-left of each glyph:
              cx = pen_x + glyph.x_offset + ft.bitmap_left
              cy = -(glyph.y_offset + ft.bitmap_top)

        Returns None if all glyphs are invisible (e.g. whitespace-only cluster).
        """
        if not shaped:
            return None

        # Render all glyphs first so we only call FreeType once per glyph.
        rendered: list[tuple[list[list[int]], int, int]] = [
            self._render_glyph(g.glyph_id) for g in shaped
        ]

        # Pass 1: bounding box in pen-relative canvas coordinates.
        pen_x = 0
        min_x: float = float("inf")
        min_y: float = float("inf")
        max_x: float = float("-inf")
        max_y: float = float("-inf")

        for (pixels, bx, by), glyph in zip(rendered, shaped):
            if not pixels:
                pen_x += glyph.x_advance
                continue
            rows, cols = len(pixels), len(pixels[0])
            gx = pen_x + glyph.x_offset + bx
            gy = -(glyph.y_offset + by)  # screen y of glyph bitmap top
            min_x = min(min_x, gx)
            min_y = min(min_y, gy)
            max_x = max(max_x, gx + cols)
            max_y = max(max_y, gy + rows)
            pen_x += glyph.x_advance

        if min_x == float("inf"):
            return None  # all glyphs invisible (e.g. whitespace cluster)

        canvas_w = int(max_x - min_x)
        canvas_h = int(max_y - min_y)
        if canvas_w <= 0 or canvas_h <= 0:
            return None

        # Pass 2: composite glyphs onto 8-bit greyscale canvas via max-blend.
        canvas = [[0] * canvas_w for _ in range(canvas_h)]
        pen_x = 0
        for (pixels, bx, by), glyph in zip(rendered, shaped):
            if not pixels:
                pen_x += glyph.x_advance
                continue
            gx = int(pen_x + glyph.x_offset + bx - min_x)
            gy = int(-(glyph.y_offset + by) - min_y)
            for ri, row in enumerate(pixels):
                cy = gy + ri
                if cy < 0 or cy >= canvas_h:
                    continue
                for ci, val in enumerate(row):
                    cx = gx + ci
                    if cx < 0 or cx >= canvas_w:
                        continue
                    if val > canvas[cy][cx]:
                        canvas[cy][cx] = val
            pen_x += glyph.x_advance

        total_advance = sum(g.x_advance for g in shaped)
        bitmap = _pack_canvas(canvas, canvas_w, canvas_h, self._bpp)
        # Baseline is at screen y=0; content top is at screen y=min_y.
        # bearing_y = rows from content top down to baseline in the content bitmap.
        bearing_y = int(-min_y)
        return RasterizedCluster(
            bitmap=bitmap,
            width=canvas_w,
            height=canvas_h,
            bearing_x=int(min_x),
            bearing_y=bearing_y,
            advance=total_advance,
        )


def _pack_canvas(
    canvas: list[list[int]], w: int, h: int, bpp: int,
) -> bytes:
    """
    Pack an 8-bit greyscale canvas to 1bpp or 2bpp.
    Rows are byte-aligned; bits are MSB-first within each byte.
    """
    result = bytearray()
    if bpp == 1:
        pitch = math.ceil(w / 8)
        for row in canvas:
            row_bytes = bytearray(pitch)
            for col, val in enumerate(row):
                if val >= 128:
                    row_bytes[col // 8] |= 0x80 >> (col % 8)
            result.extend(row_bytes)
    else:  # bpp == 2: 4 pixels per byte, two bits each, MSB-first
        # Quantize 0–255 → 0–3: 0→0, 1–85→1, 86–170→2, 171–255→3
        pitch = math.ceil(w / 4)
        for row in canvas:
            row_bytes = bytearray(pitch)
            for col, val in enumerate(row):
                level = val >> 6  # 0–63→0, 64–127→1, 128–191→2, 192–255→3
                shift = 6 - 2 * (col % 4)
                row_bytes[col // 4] |= level << shift
            result.extend(row_bytes)
    return bytes(result)


def rasterize_all(
    font_path: str | Path,
    cfg: ScriptConfig,
    size: int,
    bpp: int,
    shaped: list[tuple[Cluster, ShapedCluster]] | None = None,
) -> list[tuple[Cluster, RasterizedCluster]]:
    """
    Rasterize every shaped cluster. Returns (cluster, rasterized) pairs.

    If shaped is None, runs shape_all first to generate the shaped clusters.
    Clusters producing no visible bitmap (e.g. whitespace) are silently dropped.
    """
    if shaped is None:
        shaped = shape_all(font_path, cfg, size)

    rasterizer = Rasterizer(font_path, size, bpp)
    results: list[tuple[Cluster, RasterizedCluster]] = []
    for cluster, shaped_cluster in shaped:
        rast = rasterizer.rasterize(cluster, shaped_cluster)
        if rast is not None:
            results.append((cluster, rast))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Rasterize Akshara clusters via FreeType")
    parser.add_argument("--font", required=True, help="Path to TTF/OTF font file")
    parser.add_argument(
        "--script", required=True,
        choices=["kannada", "tamil", "devanagari"],
    )
    parser.add_argument("--size", type=int, default=24, help="Pixel size")
    parser.add_argument("--bpp", type=int, default=1, choices=[1, 2], help="Bits per pixel")
    parser.add_argument(
        "--count", action="store_true",
        help="Print rasterized cluster count only and exit",
    )
    args = parser.parse_args()

    mod = importlib.import_module(f"scripts.{args.script}")
    cfg = from_module(mod)
    results = rasterize_all(args.font, cfg, args.size, args.bpp)

    if args.count:
        print(f"{len(results)} rasterized clusters")
        return

    total_bytes = sum(len(r.bitmap) for _, r in results)
    print(f"{len(results)} clusters, {total_bytes} bitmap bytes total")
    print(f"avg bitmap: {total_bytes / len(results):.1f} bytes" if results else "")

    for cluster, rast in results[:20]:
        cps = " ".join(f"U+{cp:04X}" for cp in cluster)
        print(
            f"{cps}  {rast.width}×{rast.height}px  "
            f"bx={rast.bearing_x}  adv={rast.advance}  "
            f"{len(rast.bitmap)}B"
        )
    if len(results) > 20:
        print(f"  … {len(results) - 20} more")


if __name__ == "__main__":
    main()
