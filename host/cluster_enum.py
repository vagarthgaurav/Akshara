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
# Format v2: cp[6] — supports depth-2 conjuncts + vowel sign (max 6 codepoints).
# Devanagari depth-3 + vowel sign (8 codepoints) will require cp[8] (format v3).
_KEY_MAX_CP = 6

Cluster = tuple[int, ...]

# Common ASCII punctuation included for mixed-script e-reader text.
_ASCII_PUNCTUATION: tuple[int, ...] = (
    0x0020,  # (space)
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
    digits: tuple[int, ...] = ()
    # atomic single-codepoint standalone consonant finals (e.g. Malayalam chillus U+0D7A–U+0D7F).
    # these fall outside the consonant range so the segmenter treats them as single-codepoint
    # clusters naturally; listing them here ensures they are precomputed in the .aks key table.
    chillus: tuple[int, ...] = ()
    # attested pairs to precompute: (c1, c2, vowel_signs, modifiers)
    # vowel_signs and modifiers are per-pair attested lists; empty = no extra forms.
    # Scripts using the old (c1, c2) 2-tuple format get all cfg.vowel_signs and no
    # modifiers (see from_module).
    conjunct_pairs: tuple[tuple[int, int, tuple[int, ...], tuple[int, ...]], ...] = ()
    # depth-2 conjunct triples: (c1, c2, c3, vowel_signs, modifiers)
    # cluster = c1 + virama + c2 + virama + c3 [+ vs] — 5 or 6 codepoints.
    # Gated on max_conjunct_depth >= 2. Vowel sign + modifier together would
    # be 7 codepoints and exceed _KEY_MAX_CP; at most one is stored per triple.
    conjunct_triples: tuple[tuple[int, int, int, tuple[int, ...], tuple[int, ...]], ...] = ()
    # explicit (consonant, vowel_signs, modifiers) entries for C + VS + modifier clusters.
    # Use for common words where a specific consonant+VS is frequently followed by
    # anusvara (U+0C82) or visarga (U+0C83). modifiers lists which to include.
    modifier_clusters: tuple[tuple[int, tuple[int, ...], tuple[int, ...]], ...] = ()


def _normalize_conjunct_pairs(
    raw: list,
    all_vowel_signs: list[int],
) -> tuple[tuple[int, int, tuple[int, ...], tuple[int, ...]], ...]:
    """
    Normalise CONJUNCT_PAIRS to the 4-tuple canonical form
    (c1, c2, vowel_signs, modifiers).

    Old 2-tuple (Tamil/Devanagari): falls back to all_vowel_signs, no modifiers.
    Old 3-tuple (Kannada before modifier support): uses per-pair VS, no modifiers.
    New 4-tuple (Kannada): uses per-pair VS and per-pair modifiers.
    """
    out: list[tuple[int, int, tuple[int, ...], tuple[int, ...]]] = []
    for pair in raw:
        if len(pair) == 4:
            c1, c2, vs, mods = pair
            out.append((int(c1), int(c2), tuple(int(v) for v in vs), tuple(int(m) for m in mods)))
        elif len(pair) == 3:
            c1, c2, vs = pair
            out.append((int(c1), int(c2), tuple(int(v) for v in vs), ()))
        else:
            c1, c2 = pair
            out.append((int(c1), int(c2), tuple(int(v) for v in all_vowel_signs), ()))
    return tuple(out)


def _normalize_conjunct_triples(
    raw: list,
) -> tuple[tuple[int, int, int, tuple[int, ...], tuple[int, ...]], ...]:
    """
    Normalise CONJUNCT_TRIPLES to canonical (c1, c2, c3, vowel_signs, modifiers).
    """
    out: list[tuple[int, int, int, tuple[int, ...], tuple[int, ...]]] = []
    for entry in raw:
        if len(entry) == 5:
            c1, c2, c3, vs, mods = entry
            out.append((int(c1), int(c2), int(c3),
                        tuple(int(v) for v in vs),
                        tuple(int(m) for m in mods)))
        else:
            c1, c2, c3 = entry[:3]
            out.append((int(c1), int(c2), int(c3), (), ()))
    return tuple(out)


def _parse_modifier_clusters(
    mod: ModuleType,
) -> tuple[tuple[int, tuple[int, ...], tuple[int, ...]], ...]:
    """
    Read MODIFIER_CLUSTERS (new 3-tuple format) or fall back to ANUSVARA_CLUSTERS
    (old 2-tuple format, defaulting modifiers to [anusvara]).
    """
    raw = getattr(mod, "MODIFIER_CLUSTERS", None)
    if raw is not None:
        return tuple(
            (int(c), tuple(int(v) for v in vs), tuple(int(m) for m in mods))
            for c, vs, mods in raw
        )
    raw = getattr(mod, "ANUSVARA_CLUSTERS", [])
    return tuple(
        (int(c), tuple(int(v) for v in vs), (0x0C82,))
        for c, vs in raw
    )


def from_module(mod: ModuleType) -> ScriptConfig:
    """Build a ScriptConfig from a script constants module (e.g. scripts.kannada)."""
    required = (
        "SCRIPT_ID", "INDEPENDENT_VOWELS", "CONSONANTS", "CONSONANT_RANGE",
        "VIRAMA", "VOWEL_SIGNS", "VOWEL_SIGN_RANGE", "MODIFIERS", "MODIFIER_RANGE",
        "MAX_CONJUNCT_DEPTH",
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
        digits=tuple(getattr(mod, "DIGITS", [])),
        chillus=tuple(getattr(mod, "CHILLUS", [])),
        conjunct_pairs=_normalize_conjunct_pairs(
            getattr(mod, "CONJUNCT_PAIRS", []),
            getattr(mod, "VOWEL_SIGNS", []),
        ),
        conjunct_triples=_normalize_conjunct_triples(
            getattr(mod, "CONJUNCT_TRIPLES", []),
        ),
        modifier_clusters=_parse_modifier_clusters(mod),
    )


def enumerate_clusters(cfg: ScriptConfig) -> list[Cluster]:
    """
    Return a sorted, deduplicated list of all valid cluster codepoint sequences.

    Clusters are variable-length tuples of Unicode codepoints with no zero-padding.
    Every cluster fits within _KEY_MAX_CP codepoints (the .aks key entry limit).
    """
    seen: set[Cluster] = set()

    def add(cluster: Cluster) -> None:
        if len(cluster) <= _KEY_MAX_CP:
            seen.add(cluster)

    # 1. Standalone independent vowels (single-codepoint clusters).
    for v in cfg.independent_vowels:
        add((v,))

    # 2. Standalone virama and modifiers — needed for OOV fallback.
    #    Conjunct fallback: consonant + virama glyph + consonant.
    #    C+VS+modifier fallback: (C+VS) glyph + standalone modifier glyph.
    add((cfg.virama,))
    for m in cfg.modifiers:
        add((m,))

    # 3. Simple consonant clusters.
    for c in cfg.consonants:
        add((c,))                 # bare consonant
        add((c, cfg.virama))      # explicit halant / half-form

        for m in cfg.modifiers:
            add((c, m))

        for vs in cfg.vowel_signs:
            add((c, vs))

    # 4. Explicit C + VS + modifier clusters from MODIFIER_CLUSTERS.
    for c, vs_list, mods in cfg.modifier_clusters:
        for vs in vs_list:
            for m in mods:
                add((c, vs, m))

    # 5. Conjuncts: C1 + virama + C2 [+ vowel_sign] [+ modifier], from the attested
    #    pair list. Gated on max_conjunct_depth >= 1.
    #
    #    C1 + virama + C2 + vowel_sign + modifier = 5 codepoints; exceeds _KEY_MAX_CP
    #    and is intentionally omitted (OOV fallback handles it on the MCU).
    for c1, c2, pair_vs, pair_mods in (cfg.conjunct_pairs if cfg.max_conjunct_depth >= 1 else ()):
        base: Cluster = (c1, cfg.virama, c2)
        add(base)
        for vs in pair_vs:
            add(base + (vs,))
        for m in pair_mods:
            add(base + (m,))

    # 5b. Depth-2 conjunct triples: C1 + virama + C2 + virama + C3 [+ vs|mod].
    #     5 codepoints bare, 6 with vowel sign or modifier (fits _KEY_MAX_CP=6).
    #     VS + modifier together = 7 codepoints; exceeds limit, so only one is stored.
    for c1, c2, c3, pair_vs, pair_mods in (cfg.conjunct_triples if cfg.max_conjunct_depth >= 2 else ()):
        base: Cluster = (c1, cfg.virama, c2, cfg.virama, c3)
        add(base)
        for vs in pair_vs:
            add(base + (vs,))
        for m in pair_mods:
            add(base + (m,))

    # 6. Digits, chillus, and common ASCII punctuation.
    for cp in range(0x0030, 0x003A):   # ASCII 0–9
        add((cp,))
    for cp in cfg.digits:              # script-native digits (e.g. Kannada ೦–೯)
        add((cp,))
    for cp in cfg.chillus:             # atomic standalone consonant finals (e.g. Malayalam ൺ–ൿ)
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
        choices=["kannada", "tamil", "devanagari", "malayalam"],
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
