"""
Akshara cluster enumerator.

Generates all valid akshara (orthographic syllable) codepoint sequences
for a given script. Output feeds shaper.py (HarfBuzz) and packer.py.

Usage:
    python -m cluster_enum --script kannada
    python -m cluster_enum --script kannada --count
"""

from __future__ import annotations

import argparse
import importlib
from dataclasses import dataclass
from types import ModuleType

# Maximum codepoints per cluster key entry (aks_key_entry_t.cp array length).
# Depth-2+ conjuncts (5+ codepoints) exceed this limit and are handled by
# the MCU segmenter's OOV fallback path rather than precomputed entries.
_KEY_MAX_CP = 4

Cluster = tuple[int, ...]

# Common ASCII punctuation included for mixed-script e-reader text.
_ASCII_PUNCTUATION: tuple[int, ...] = (
    0x002C,  # ,
    0x002E,  # .
    0x003F,  # ?
    0x0021,  # !
    0x003B,  # ;
    0x003A,  # :
    0x0022,  # "
    0x0027,  # '
    0x002D,  # -
    0x0028,  # (
    0x0029,  # )
    0x002F,  # /
)


@dataclass(frozen=True)
class ScriptConfig:
    """All enumeration parameters for one Indic script."""
    script_id: int
    independent_vowels: tuple[int, ...]
    consonants: tuple[int, ...]
    consonant_range: tuple[int, int]   # (start, end) for aks_rule_table_t
    virama: int
    vowel_signs: tuple[int, ...]
    vowel_sign_range: tuple[int, int]  # coarse range for segmenter rule table
    modifiers: tuple[int, ...]
    modifier_range: tuple[int, int]    # (start, end) for aks_rule_table_t
    max_conjunct_depth: int
    common_consonants: tuple[int, ...]
    digits: tuple[int, ...] = ()       # script-native digit codepoints (optional)


def from_module(mod: ModuleType) -> ScriptConfig:
    """Build a ScriptConfig from a script constants module (e.g. scripts.kannada)."""
    required = (
        "SCRIPT_ID", "INDEPENDENT_VOWELS", "CONSONANTS", "CONSONANT_RANGE",
        "VIRAMA", "VOWEL_SIGNS", "VOWEL_SIGN_RANGE", "MODIFIERS", "MODIFIER_RANGE",
        "MAX_CONJUNCT_DEPTH", "COMMON_CONSONANTS",
    )
    missing = [attr for attr in required if not hasattr(mod, attr)]
    if missing:
        raise AttributeError(f"Script module {mod.__name__!r} missing: {missing}")

    return ScriptConfig(
        script_id=mod.SCRIPT_ID,
        independent_vowels=tuple(mod.INDEPENDENT_VOWELS),
        consonants=tuple(mod.CONSONANTS),
        consonant_range=tuple(mod.CONSONANT_RANGE),  # type: ignore[arg-type]
        virama=mod.VIRAMA,
        vowel_signs=tuple(mod.VOWEL_SIGNS),
        vowel_sign_range=tuple(mod.VOWEL_SIGN_RANGE),  # type: ignore[arg-type]
        modifiers=tuple(mod.MODIFIERS),
        modifier_range=tuple(mod.MODIFIER_RANGE),  # type: ignore[arg-type]
        max_conjunct_depth=mod.MAX_CONJUNCT_DEPTH,
        common_consonants=tuple(mod.COMMON_CONSONANTS),
        digits=tuple(getattr(mod, "DIGITS", [])),
    )


def enumerate_clusters(cfg: ScriptConfig) -> list[Cluster]:
    """
    Return a sorted, deduplicated list of all valid cluster codepoint sequences.

    Clusters are variable-length tuples of Unicode codepoints with no zero-padding.
    Every cluster fits within _KEY_MAX_CP codepoints (the .aks key entry limit).
    """
    seen: set[Cluster] = set()
    common = frozenset(cfg.common_consonants)

    def add(cluster: Cluster) -> None:
        if len(cluster) <= _KEY_MAX_CP:
            seen.add(cluster)

    # 1. Standalone independent vowels (single-codepoint clusters).
    for v in cfg.independent_vowels:
        add((v,))

    # 2. Standalone virama — needed for OOV fallback of unrecognised conjuncts.
    #    When a conjunct is missing from the .aks, the fallback renders each
    #    codepoint individually: consonant + virama glyph + consonant.
    add((cfg.virama,))

    # 3. Simple consonant clusters.
    for c in cfg.consonants:
        add((c,))                 # bare consonant
        add((c, cfg.virama))      # explicit halant / half-form

        for m in cfg.modifiers:
            add((c, m))

        for vs in cfg.vowel_signs:
            add((c, vs))
            for m in cfg.modifiers:
                add((c, vs, m))   # consonant + vowel_sign + modifier (e.g. ಬೆಂ)

    # 4. Depth-1 conjuncts: C1 + virama + C2 [+ vowel_sign | + modifier].
    #
    #    Frequency filter: BOTH consonants must be in COMMON_CONSONANTS.
    #    "Either common" would admit too many near-zero-occurrence pairs and
    #    blow past the ~1000-cluster MCU memory target.
    #
    #    C1 + virama + C2 + vowel_sign + modifier = 5 codepoints; exceeds
    #    _KEY_MAX_CP and is intentionally omitted.
    for c1 in cfg.consonants:
        if c1 not in common:
            continue
        for c2 in cfg.consonants:
            if c2 not in common:
                continue

            base: Cluster = (c1, cfg.virama, c2)
            add(base)

            for vs in cfg.vowel_signs:
                add(base + (vs,))

    # Depth-2+ conjuncts (C + virama + C + virama + C = 5+ codepoints) exceed
    # _KEY_MAX_CP and cannot be stored as key entries. The MCU segmenter still
    # absorbs them per max_conjunct_depth, then takes the OOV fallback path.

    # 5. Digits and common ASCII punctuation.
    for cp in range(0x0030, 0x003A):   # ASCII 0–9
        add((cp,))
    for cp in cfg.digits:              # script-native digits (e.g. Kannada ೦–೯)
        add((cp,))
    for cp in _ASCII_PUNCTUATION:
        add((cp,))

    return sorted(seen)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enumerate Akshara clusters for a given script",
    )
    parser.add_argument(
        "--script", required=True,
        choices=["kannada", "tamil", "devanagari"],
        help="Target script",
    )
    parser.add_argument(
        "--count", action="store_true",
        help="Print cluster count only and exit",
    )
    args = parser.parse_args()

    mod = importlib.import_module(f"scripts.{args.script}")
    cfg = from_module(mod)
    clusters = enumerate_clusters(cfg)

    if args.count:
        print(f"{len(clusters)} clusters")
        return

    for cluster in clusters:
        codepoints = " ".join(f"U+{cp:04X}" for cp in cluster)
        chars = "".join(chr(cp) for cp in cluster)
        print(f"{chars}\t{codepoints}")


if __name__ == "__main__":
    main()
