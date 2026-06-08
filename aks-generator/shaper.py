"""
Akshara shaper stage.

Feeds each cluster (codepoint sequence from cluster_enum.py) through HarfBuzz
and returns the glyph run for that cluster: a list of GlyphInfo in pixel units
at the requested size.

Usage:
    python -m shaper --font NotoSansKannada-Regular.ttf --script kannada --size 24
    python -m shaper --font NotoSansKannada-Regular.ttf --script kannada --size 24 --count
"""

from __future__ import annotations

import argparse
import importlib
from dataclasses import dataclass
from pathlib import Path

import uharfbuzz as hb

from cluster_enum import Cluster, ScriptConfig, enumerate_clusters, from_module

# Maps AKS_SCRIPT_* id → (4-letter OpenType script tag, BCP-47 language tag).
# HarfBuzz uses these for mandatory feature selection (akhn, half, pstf, …).
_SCRIPT_HB: dict[int, tuple[str, str]] = {
    0x01: ("Knda", "kn"),
    0x02: ("Taml", "ta"),
    0x03: ("Deva", "hi"),
    0x04: ("Telu", "te"),
    0x05: ("Mlym", "ml"),
}


@dataclass(frozen=True)
class GlyphInfo:
    glyph_id: int
    x_offset: int   # pixels, rounded
    y_offset: int   # pixels, rounded (positive = up in HarfBuzz convention)
    x_advance: int  # pixels, rounded


ShapedCluster = list[GlyphInfo]


class Shaper:
    """
    HarfBuzz shaper for one font face at a fixed pixel size.

    HarfBuzz operates in design units; we convert to pixels via size/upem.
    The font scale is set to upem so that raw position values are in design
    units and the conversion is a single multiply.
    """

    def __init__(self, font_path: str | Path, cfg: ScriptConfig, size: int) -> None:
        script_tag, lang_tag = _SCRIPT_HB.get(cfg.script_id, ("Latn", "en"))

        blob = hb.Blob.from_file_path(str(font_path))
        face = hb.Face(blob)
        self._font = hb.Font(face)
        self._upem: int = face.upem
        self._px_scale: float = size / self._upem

        # Design-unit scale: positions come back in font design units.
        self._font.scale = (self._upem, self._upem)

        self._script_tag = script_tag
        self._lang_tag = lang_tag

    def shape(self, cluster: Cluster) -> ShapedCluster:
        """
        Shape one cluster and return its glyph run in pixel units.

        guess_segment_properties() is called so HarfBuzz auto-detects the
        Unicode script from the codepoints; the language is then overridden
        because OpenType feature selection depends on the BCP-47 language tag.

        Returns an empty list if HarfBuzz produces no glyphs (e.g. all
        codepoints are absent from the font's cmap).
        """
        buf = hb.Buffer()
        buf.add_codepoints(list(cluster))
        buf.guess_segment_properties()
        buf.language = self._lang_tag

        hb.shape(self._font, buf)

        s = self._px_scale
        result: ShapedCluster = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            result.append(GlyphInfo(
                glyph_id=info.codepoint,   # after shaping, .codepoint holds glyph id
                x_offset=round(pos.x_offset * s),
                y_offset=round(pos.y_offset * s),
                x_advance=round(pos.x_advance * s),
            ))
        return result


def shape_all(
    font_path: str | Path,
    cfg: ScriptConfig,
    size: int,
    clusters: list[Cluster] | None = None,
) -> list[tuple[Cluster, ShapedCluster]]:
    """
    Shape every cluster for a script. Returns (cluster, glyph_run) pairs.

    If clusters is None, calls cluster_enum.enumerate_clusters to generate them.
    Clusters for which HarfBuzz produces no output are silently dropped; the
    packer will mark them absent so the MCU takes the OOV fallback path.
    """
    if clusters is None:
        clusters = enumerate_clusters(cfg)

    shaper = Shaper(font_path, cfg, size)
    results: list[tuple[Cluster, ShapedCluster]] = []
    for cluster in clusters:
        shaped = shaper.shape(cluster)
        if shaped:
            results.append((cluster, shaped))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Shape Akshara clusters via HarfBuzz")
    parser.add_argument("--font", required=True, help="Path to TTF/OTF font file")
    parser.add_argument(
        "--script", required=True,
        choices=["kannada", "tamil", "devanagari", "malayalam", "telugu"],
    )
    parser.add_argument("--size", type=int, default=24, help="Pixel size")
    parser.add_argument(
        "--count", action="store_true",
        help="Print shaped cluster count only and exit",
    )
    args = parser.parse_args()

    mod = importlib.import_module(f"scripts.{args.script}")
    cfg = from_module(mod)
    results = shape_all(args.font, cfg, args.size)

    if args.count:
        print(f"{len(results)} shaped clusters")
        return

    for cluster, glyphs in results:
        cps = " ".join(f"U+{cp:04X}" for cp in cluster)
        glyph_str = " ".join(
            f"[gid={g.glyph_id} dx={g.x_offset} dy={g.y_offset} adv={g.x_advance}]"
            for g in glyphs
        )
        print(f"{cps}\t→\t{glyph_str}")


if __name__ == "__main__":
    main()
