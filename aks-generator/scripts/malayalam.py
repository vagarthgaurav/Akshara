"""
Malayalam script definition for Akshara cluster enumeration.

Codepoint ranges from Unicode Standard, Malayalam block (U+0D00–U+0D7F).
Rule table values match aks_rule_table_t in the .aks format spec.

Chillu note: U+0D7A–U+0D7F are encoded as atomic chillu codepoints in Unicode
(not as consonant + virama). They fall outside the consonant range, so the
segmenter treats them as single-codepoint clusters — correct behaviour, since
a chillu is a standalone consonant-final form that does not take vowel signs.
No segmenter extension needed; they just fall through to the single-codepoint
path and are precomputed as CHILLUS below.
"""

SCRIPT_ID: int = 0x05

# ── Rule table values (written verbatim to aks_rule_table_t in .aks header) ──

CONSONANT_RANGE: tuple[int, int] = (0x0D15, 0x0D39)  # KA..HA
VIRAMA: int = 0x0D4D  # MALAYALAM SIGN VIRAMA
VOWEL_SIGN_RANGE: tuple[int, int] = (0x0D3E, 0x0D4C)  # coarse range for segmenter
MODIFIER_RANGE: tuple[int, int] = (0x0D02, 0x0D03)  # anusvara..visarga
MAX_CONJUNCT_DEPTH: int = 2

# ── Enumerable codepoints (explicit lists; unassigned Unicode slots excluded) ─

# Independent vowels: U+0D05–U+0D14 (several slots unassigned)
INDEPENDENT_VOWELS: list[int] = [
    0x0D05,  # അ A
    0x0D06,  # ആ AA
    0x0D07,  # ഇ I
    0x0D08,  # ഈ II
    0x0D09,  # ഉ U
    0x0D0A,  # ഊ UU
    0x0D0B,  # ഋ VOCALIC R
    0x0D0C,  # ഌ VOCALIC L
    # 0x0D0D unassigned
    0x0D0E,  # എ E
    0x0D0F,  # ഏ EE
    0x0D10,  # ഐ AI
    # 0x0D11 unassigned
    0x0D12,  # ഒ O
    0x0D13,  # ഓ OO
    0x0D14,  # ഔ AU
]

# Consonants: U+0D15–U+0D39. The range is mostly contiguous; U+0D29 is unassigned.
CONSONANTS: list[int] = [
    *range(0x0D15, 0x0D29),  # KA(15)..NA(28)  — 20 consonants
    *range(0x0D2A, 0x0D3A),  # PA(2A)..HA(39)  — 16 consonants  (0x0D29 unassigned)
]

# Dependent vowel signs: U+0D3E–U+0D4C (virama U+0D4D excluded).
# U+0D45 and U+0D49 are unassigned.
VOWEL_SIGNS: list[int] = [
    *range(0x0D3E, 0x0D45),  # ാ ി ീ ു ൂ ൃ ൄ  (AA..VOCALIC_RR; 0x0D45 unassigned)
    *range(0x0D46, 0x0D49),  # െ േ ൈ           (E..AI; 0x0D49 unassigned)
    *range(0x0D4A, 0x0D4D),  # ൊ ോ ൌ           (O..AU; 0x0D4D is virama, excluded)
]

MODIFIERS: list[int] = [
    0x0D02,  # MALAYALAM SIGN ANUSVARA (ം) — nasalisation, extremely common
    # 0x0D03 VISARGA (ഃ) omitted — rare in native Malayalam, appears in Sanskrit loans
]

# Chillu letters: U+0D7A–U+0D7F. Atomic codepoints representing final consonant forms.
# These are standalone single-codepoint clusters; no vowel signs attach to them.
# Corpus analysis should confirm which are frequent enough to include.
CHILLUS: list[int] = [
    0x0D7A,  # ൺ CHILLU NN  (ണ്)
    0x0D7B,  # ൻ CHILLU N   (ന്)
    0x0D7C,  # ർ CHILLU RR  (ർ)
    0x0D7D,  # ൽ CHILLU L   (ൽ / ല്)
    0x0D7E,  # ൾ CHILLU LL  (ള്)
    0x0D7F,  # ൿ CHILLU K   (ക്) — rare, mainly in loanwords
]

# Consonant + modifier clusters with corpus-attested vowel-sign combinations.
# Populated after corpus analysis — left empty here as a placeholder.
# Format: (consonant, vowel_signs, modifiers)
MODIFIER_CLUSTERS: list[tuple[int, list[int], list[int]]] = [
    # High-frequency anusvara clusters; vowel sign lists to be filled from corpus.
    # Examples from Malayalam phonology (anusvara after vowel sign is common):
    # ക + ാ + ം  (kāṃ),  ന + ി + ം  (niṃ),  മ + ു + ം  (muṃ), etc.
    (0x0D2F, [0x0D41, 0x0D3E, 0x0D3F], [0x0D02]),  # യ — യും യാം യിം  (23,688 381 322)
    (0x0D32, [0x0D41, 0x0D3F, 0x0D3E, 0x0D48], [0x0D02]),  # ല — ലും ലിം ലാം ലൈം  (12,499 644 458 299)
    (0x0D35, [0x0D41], [0x0D02]),  # വ — വും  (10,262)
    (0x0D33, [0x0D41, 0x0D3F], [0x0D02]),  # ള — ളും ളിം  (7,774 157)
    (0x0D28, [0x0D41, 0x0D3E], [0x0D02]),  # ന — നും നാം  (6,695 376)
    (0x0D30, [0x0D41, 0x0D3E], [0x0D02]),  # ര — രും രാം  (4,602 278)
    (0x0D1F, [0x0D41, 0x0D40, 0x0D48], [0x0D02]),  # ട — ടും ടീം ടൈം  (2,850 308 140)
    (0x0D15, [0x0D41, 0x0D3E, 0x0D4B, 0x0D3F], [0x0D02]),  # ക — കും കാം കോം കിം  (1,906 432 191 128)
    (0x0D24, [0x0D41, 0x0D3E], [0x0D02]),  # ത — തും താം  (2,239 248)
    (0x0D31, [0x0D41, 0x0D3E, 0x0D3F, 0x0D42], [0x0D02]),  # റ — റും റാം റിം റൂം  (1,436 425 136 105)
    (0x0D38, [0x0D41, 0x0D3F, 0x0D3E], [0x0D02]),  # സ — സും സിം സാം  (827 754 461)
    (0x0D34, [0x0D41], [0x0D02]),  # ഴ — ഴും  (1,312)
    (0x0D2E, [0x0D41, 0x0D3E], [0x0D02]),  # മ — മും മാം  (795 197)
    (0x0D2C, [0x0D3E, 0x0D4B, 0x0D46], [0x0D02]),  # ബ — ബാം ബോം ബെം  (336 217 211)
    (0x0D23, [0x0D41, 0x0D3E], [0x0D02]),  # ണ — ണും ണാം  (239 228)
    (0x0D39, [0x0D4B, 0x0D3F, 0x0D3E], [0x0D02]),  # ഹ — ഹോം ഹിം ഹാം  (159 147 122)
    (0x0D21, [0x0D41, 0x0D3F], [0x0D02]),  # ഡ — ഡും ഡിം  (221 117)
    (0x0D1C, [0x0D3F], [0x0D02]),  # ജ — ജിം  (132)
    (0x0D2B, [0x0D41], [0x0D02]),  # ഫ — ഫും  (129)
    (0x0D26, [0x0D3E], [0x0D02]),  # ദ — ദാം  (124)
    (0x0D17, [0x0D41], [0x0D02]),  # ഗ — ഗും  (106)
]

# Attested conjunct pairs.
# Malayalam has a large conjunct inventory. This seed list covers phonologically
# productive and graphically common pairs (gemination + liquid/nasal clusters).
# Vowel-sign lists are left empty — corpus analysis should fill them in.
# The bare conjunct (no VS, no modifier) is always precomputed.
CONJUNCT_PAIRS: list[tuple[int, int, list[int], list[int]]] = [
 (0x0D15, 0x0D15, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41, 0x0D42, 0x0D46, 0x0D47, 0x0D4A, 0x0D4B], [0x0D02]),  # ക്ക — 181,722 occ, 9 VS, 13,231 anusv
    (0x0D28, 0x0D28, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41, 0x0D42, 0x0D46, 0x0D47, 0x0D48, 0x0D4A, 0x0D4B], [0x0D02]),  # ന്ന — 179,443 occ, 10 VS, 14,298 anusv
    (0x0D24, 0x0D24, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41, 0x0D42, 0x0D46, 0x0D47, 0x0D4A, 0x0D4B], [0x0D02]),  # ത്ത — 142,339 occ, 9 VS, 2,439 anusv
    (0x0D1F, 0x0D1F, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41, 0x0D42, 0x0D46, 0x0D47, 0x0D4B], [0x0D02]),  # ട്ട — 68,268 occ, 8 VS, 2,732 anusv
    (0x0D1A, 0x0D1A, [0x0D3E, 0x0D3F, 0x0D41, 0x0D46, 0x0D47, 0x0D4A, 0x0D4B], [0x0D02]),  # ച്ച — 67,932 occ, 7 VS, 914 anusv
    (0x0D2A, 0x0D2A, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41, 0x0D42, 0x0D46, 0x0D47, 0x0D4A, 0x0D4B], [0x0D02]),  # പ്പ — 62,741 occ, 9 VS, 2,562 anusv
    (0x0D19, 0x0D19, [0x0D3E, 0x0D3F, 0x0D41, 0x0D47, 0x0D4B], [0x0D02]),  # ങ്ങ — 54,587 occ, 5 VS, 429 anusv
    (0x0D31, 0x0D31, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41, 0x0D42, 0x0D46, 0x0D47, 0x0D48, 0x0D4A, 0x0D4B], [0x0D02]),  # റ്റ — 50,498 occ, 10 VS, 2,485 anusv
    (0x0D23, 0x0D1F, [0x0D3E, 0x0D3F, 0x0D41, 0x0D46, 0x0D47, 0x0D4B], [0x0D02]),  # ണ്ട — 48,175 occ, 6 VS, 2,469 anusv
    (0x0D2A, 0x0D30, [0x0D3E, 0x0D3F, 0x0D40, 0x0D47, 0x0D48, 0x0D4A, 0x0D4B], [0x0D02]),  # പ്ര — 45,894 occ, 7 VS, 775 anusv
    (0x0D32, 0x0D32, [0x0D3E, 0x0D3F, 0x0D41, 0x0D42, 0x0D46, 0x0D47, 0x0D4A, 0x0D4B], [0x0D02]),  # ല്ല — 33,404 occ, 8 VS, 2,467 anusv
    (0x0D28, 0x0D31, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41, 0x0D46, 0x0D47, 0x0D48, 0x0D4B], [0x0D02]),  # ന്റ — 30,968 occ, 8 VS, 160 anusv
    (0x0D24, 0x0D30, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41, 0x0D47], [0x0D02]),  # ത്ര — 30,517 occ, 5 VS, 3,166 anusv
    (0x0D33, 0x0D33, [0x0D3E, 0x0D3F, 0x0D41, 0x0D42], [0x0D02]),  # ള്ള — 28,664 occ, 4 VS, 625 anusv
    (0x0D28, 0x0D24, [0x0D3E, 0x0D3F, 0x0D41, 0x0D46, 0x0D4A, 0x0D4B], [0x0D02]),  # ന്ത — 28,287 occ, 6 VS, 971 anusv
    (0x0D15, 0x0D37, [0x0D3E, 0x0D3F, 0x0D40, 0x0D46, 0x0D47, 0x0D4B], [0x0D02]),  # ക്ഷ — 22,801 occ, 6 VS, 1,594 anusv
    (0x0D1E, 0x0D1E, [0x0D3E, 0x0D3F, 0x0D41, 0x0D46], [0x0D02]),  # ഞ്ഞ — 20,170 occ, 4 VS, 127 anusv
    (0x0D38, 0x0D25, [0x0D3E, 0x0D3F], []),  # സ്ഥ — 16,391 occ, 2 VS
    (0x0D19, 0x0D15, [0x0D3E, 0x0D3F, 0x0D41, 0x0D46, 0x0D47, 0x0D4B], [0x0D02]),  # ങ്ക — 15,055 occ, 6 VS, 161 anusv
    (0x0D2E, 0x0D2A, [0x0D3E, 0x0D3F, 0x0D41, 0x0D42, 0x0D4B], [0x0D02]),  # മ്പ — 14,215 occ, 5 VS, 137 anusv
    (0x0D2E, 0x0D2E, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41, 0x0D42, 0x0D47], [0x0D02]),  # മ്മ — 12,801 occ, 6 VS, 129 anusv
    (0x0D24, 0x0D2F, [0x0D3E, 0x0D41, 0x0D47], [0x0D02]),  # ത്യ — 11,894 occ, 3 VS, 479 anusv
    (0x0D38, 0x0D31, [], []),  # സ്റ — 11,284 occ, 0 VS
    (0x0D30, 0x0D2F, [0x0D3E], [0x0D02]),  # ര്യ — 10,706 occ, 1 VS, 1,910 anusv
    (0x0D28, 0x0D26, [0x0D3F, 0x0D41, 0x0D47], []),  # ന്ദ — 10,677 occ, 3 VS
    (0x0D38, 0x0D35, [0x0D3E, 0x0D3F, 0x0D40], [0x0D02]),  # സ്വ — 10,071 occ, 3 VS, 157 anusv
    (0x0D26, 0x0D2F, [0x0D3E, 0x0D41, 0x0D4B], [0x0D02]),  # ദ്യ — 9,847 occ, 3 VS, 1,586 anusv
    (0x0D2F, 0x0D2F, [0x0D3E, 0x0D3F, 0x0D41, 0x0D47], [0x0D02]),  # യ്യ — 9,487 occ, 4 VS, 732 anusv
    (0x0D15, 0x0D30, [0x0D3E, 0x0D3F, 0x0D40, 0x0D42, 0x0D46, 0x0D48, 0x0D4B], [0x0D02]),  # ക്ര — 8,520 occ, 7 VS, 325 anusv
    (0x0D1F, 0x0D30, [0x0D3E, 0x0D3F, 0x0D40, 0x0D46, 0x0D47, 0x0D48, 0x0D4B], [0x0D02]),  # ട്ര — 7,973 occ, 7 VS, 403 anusv
    (0x0D2F, 0x0D15, [], []),  # യ്ക — 7,848 occ, 0 VS
    (0x0D35, 0x0D2F, [0x0D3E, 0x0D42, 0x0D4B], []),  # വ്യ — 7,810 occ, 3 VS
    (0x0D26, 0x0D27, [0x0D3E, 0x0D3F, 0x0D40, 0x0D47], [0x0D02]),  # ദ്ധ — 7,633 occ, 4 VS, 152 anusv
    (0x0D28, 0x0D27, [0x0D3F, 0x0D41], [0x0D02]),  # ന്ധ — 7,203 occ, 2 VS, 426 anusv
    (0x0D1E, 0x0D1A, [0x0D3E, 0x0D3F, 0x0D41, 0x0D47], [0x0D02]),  # ഞ്ച — 7,147 occ, 4 VS, 255 anusv
    (0x0D2F, 0x0D24, [0x0D3E, 0x0D3F, 0x0D41], []),  # യ്ത — 7,137 occ, 3 VS
    (0x0D17, 0x0D30, [0x0D3E, 0x0D3F, 0x0D40, 0x0D42, 0x0D47], [0x0D02]),  # ഗ്ര — 7,081 occ, 5 VS, 295 anusv
    (0x0D15, 0x0D24, [0x0D3E, 0x0D3F], [0x0D02]),  # ക്ത — 6,966 occ, 2 VS, 131 anusv
    (0x0D26, 0x0D30, [0x0D3E, 0x0D40, 0x0D4B], [0x0D02]),  # ദ്ര — 6,931 occ, 3 VS, 376 anusv
    (0x0D38, 0x0D24, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41], []),  # സ്ത — 6,820 occ, 4 VS
    (0x0D26, 0x0D26, [0x0D3E, 0x0D3F, 0x0D40, 0x0D47], [0x0D02]),  # ദ്ദ — 6,770 occ, 4 VS, 129 anusv
    (0x0D27, 0x0D2F, [0x0D3E], [0x0D02]),  # ധ്യ — 6,354 occ, 1 VS, 214 anusv
    (0x0D36, 0x0D30, [0x0D3F, 0x0D40, 0x0D47], []),  # ശ്ര — 6,135 occ, 3 VS
    (0x0D23, 0x0D23, [0x0D3E, 0x0D3F, 0x0D40, 0x0D41, 0x0D42], [0x0D02]),  # ണ്ണ — 5,488 occ, 5 VS, 873 anusv
    (0x0D37, 0x0D1F, [0x0D3E, 0x0D3F], [0x0D02]),  # ഷ്ട — 5,273 occ, 2 VS, 226 anusv
    (0x0D16, 0x0D2F, [0x0D3E], [0x0D02]),  # ഖ്യ — 4,770 occ, 1 VS, 129 anusv
    (0x0D36, 0x0D2F, [0x0D3E], [0x0D02]),  # ശ്യ — 4,541 occ, 1 VS, 627 anusv
    (0x0D28, 0x0D2F, [0x0D3E, 0x0D41, 0x0D42], [0x0D02]),  # ന്യ — 4,415 occ, 3 VS, 457 anusv
    (0x0D37, 0x0D2F, [0x0D3E], [0x0D02]),  # ഷ്യ — 4,316 occ, 1 VS, 436 anusv
    (0x0D24, 0x0D38, [0x0D3E], [0x0D02]),  # ത്സ — 3,964 occ, 1 VS, 175 anusv
    (0x0D1C, 0x0D2F, [0x0D3E, 0x0D4B], [0x0D02]),  # ജ്യ — 3,955 occ, 2 VS, 312 anusv
    (0x0D34, 0x0D1A, [], []),  # ഴ്ച — 3,556 occ, 0 VS
    (0x0D24, 0x0D35, [], [0x0D02]),  # ത്വ — 3,336 occ, 0 VS, 958 anusv
    (0x0D38, 0x0D38, [0x0D3E, 0x0D3F, 0x0D41], [0x0D02]),  # സ്സ — 3,128 occ, 3 VS, 143 anusv
    (0x0D15, 0x0D1F, [0x0D3F, 0x0D4B], []),  # ക്ട — 3,102 occ, 2 VS
    (0x0D36, 0x0D35, [0x0D3E], []),  # ശ്വ — 3,096 occ, 1 VS
    (0x0D24, 0x0D25, [0x0D3E, 0x0D3F], [0x0D02]),  # ത്ഥ — 2,734 occ, 2 VS, 120 anusv
    (0x0D15, 0x0D2F, [0x0D3E, 0x0D41, 0x0D42], [0x0D02]),  # ക്യ — 2,634 occ, 3 VS, 229 anusv
    (0x0D2C, 0x0D30, [0x0D3E, 0x0D3F, 0x0D41, 0x0D47, 0x0D4B], []),  # ബ്ര — 2,604 occ, 5 VS
    (0x0D17, 0x0D2F, [0x0D3E], [0x0D02]),  # ഗ്യ — 2,590 occ, 1 VS, 196 anusv
    (0x0D2D, 0x0D2F, [0x0D3E], []),  # ഭ്യ — 2,189 occ, 1 VS
    (0x0D15, 0x0D38, [0x0D3F], []),  # ക്സ — 2,149 occ, 1 VS
    (0x0D28, 0x0D35, [0x0D47], []),  # ന്വ — 2,133 occ, 1 VS
    (0x0D28, 0x0D2E, [0x0D3E], []),  # ന്മ — 2,078 occ, 1 VS
    (0x0D38, 0x0D2A, [0x0D3E, 0x0D3F, 0x0D40, 0x0D46, 0x0D4B], []),  # സ്പ — 2,074 occ, 5 VS
    (0x0D32, 0x0D2F, [0x0D3E, 0x0D41], [0x0D02]),  # ല്യ — 1,816 occ, 2 VS, 308 anusv
    (0x0D23, 0x0D21, [0x0D3F], []),  # ണ്ഡ — 1,789 occ, 1 VS
    (0x0D15, 0x0D32, [0x0D3E, 0x0D3F, 0x0D4B], []),  # ക്ല — 1,761 occ, 3 VS
    (0x0D38, 0x0D15, [0x0D3E, 0x0D42, 0x0D4B], []),  # സ്ക — 1,744 occ, 3 VS
    (0x0D2A, 0x0D32, [0x0D3E, 0x0D3F, 0x0D47, 0x0D4B], []),  # പ്ല — 1,694 occ, 4 VS
    (0x0D38, 0x0D2F, [0x0D42], [0x0D02]),  # സ്യ — 1,539 occ, 1 VS, 171 anusv
    (0x0D37, 0x0D23, [0x0D41], []),  # ഷ്ണ — 1,489 occ, 1 VS
    (0x0D24, 0x0D2E, [0x0D3E], []),  # ത്മ — 1,360 occ, 1 VS
    (0x0D2E, 0x0D2F, [0x0D3E, 0x0D42], [0x0D02]),  # മ്യ — 1,350 occ, 2 VS, 277 anusv
    (0x0D38, 0x0D2E, [0x0D3E, 0x0D3F], []),  # സ്മ — 1,321 occ, 2 VS
    (0x0D36, 0x0D1A, [0x0D3E, 0x0D3F], []),  # ശ്ച — 1,317 occ, 2 VS
    (0x0D35, 0x0D35, [0x0D3E, 0x0D40], [0x0D02]),  # വ്വ — 1,265 occ, 2 VS, 122 anusv
    (0x0D2B, 0x0D30, [0x0D3E, 0x0D3F, 0x0D40], []),  # ഫ്ര — 1,265 occ, 3 VS
    (0x0D2C, 0x0D32, [0x0D3E, 0x0D3F, 0x0D4B], []),  # ബ്ല — 1,239 occ, 3 VS
    (0x0D21, 0x0D30, [0x0D3F, 0x0D48, 0x0D4B], []),  # ഡ്ര — 1,213 occ, 3 VS
    (0x0D17, 0x0D32, [0x0D3E, 0x0D40, 0x0D42, 0x0D4B], []),  # ഗ്ല — 1,185 occ, 4 VS
    (0x0D2C, 0x0D26, [0x0D41], []),  # ബ്ദ — 1,049 occ, 1 VS
    (0x0D15, 0x0D35, [0x0D3E, 0x0D3F], []),  # ക്വ — 959 occ, 2 VS
    (0x0D38, 0x0D32, [0x0D3E, 0x0D3F, 0x0D40], [0x0D02]),  # സ്ല — 935 occ, 3 VS, 495 anusv
    (0x0D34, 0x0D38, [0x0D3F, 0x0D41], []),  # ഴ്സ — 930 occ, 2 VS
    (0x0D38, 0x0D1F, [], []),  # സ്ട — 900 occ, 0 VS
    (0x0D1C, 0x0D1E, [0x0D3E], []),  # ജ്ഞ — 883 occ, 1 VS
    (0x0D1C, 0x0D1C, [0x0D3F, 0x0D40], []),  # ജ്ജ — 853 occ, 2 VS
    (0x0D1A, 0x0D1B, [], []),  # ച്ഛ — 850 occ, 0 VS
    (0x0D2A, 0x0D2F, [0x0D42], []),  # പ്യ — 823 occ, 1 VS
    (0x0D1E, 0x0D1C, [0x0D3F, 0x0D41], []),  # ഞ്ജ — 807 occ, 2 VS
    (0x0D26, 0x0D18, [0x0D3E], []),  # ദ്ഘ — 761 occ, 1 VS
    (0x0D36, 0x0D36, [0x0D3F, 0x0D42, 0x0D47], []),  # ശ്ശ — 747 occ, 3 VS
    (0x0D1F, 0x0D35, [0x0D3F, 0x0D40], []),  # ട്വ — 729 occ, 2 VS
    (0x0D2A, 0x0D24, [0x0D3F], [0x0D02]),  # പ്ത — 688 occ, 1 VS, 100 anusv
    (0x0D38, 0x0D2C, [0x0D41], []),  # സ്ബ — 671 occ, 1 VS
    (0x0D26, 0x0D35, [0x0D3E, 0x0D40], []),  # ദ്വ — 612 occ, 2 VS
    (0x0D2A, 0x0D31, [], []),  # പ്റ — 612 occ, 0 VS
    (0x0D36, 0x0D28, [], [0x0D02]),  # ശ്ന — 587 occ, 0 VS, 137 anusv
    (0x0D35, 0x0D30, [], []),  # വ്ര — 543 occ, 0 VS
    (0x0D32, 0x0D2A, [], []),  # ല്പ — 535 occ, 0 VS
    (0x0D36, 0x0D2E, [0x0D40], []),  # ശ്മ — 523 occ, 1 VS
    (0x0D37, 0x0D2E, [0x0D3F], []),  # ഷ്മ — 522 occ, 1 VS
    (0x0D39, 0x0D2F, [], []),  # ഹ്യ — 506 occ, 0 VS
    (0x0D23, 0x0D2F, [], []),  # ണ്യ — 466 occ, 0 VS
    (0x0D2F, 0x0D2A, [], []),  # യ്പ — 464 occ, 0 VS
    (0x0D17, 0x0D17, [], []),  # ഗ്ഗ — 460 occ, 0 VS
    (0x0D17, 0x0D26, [0x0D3E], []),  # ഗ്ദ — 447 occ, 1 VS
    (0x0D39, 0x0D2E, [0x0D3E], []),  # ഹ്മ — 433 occ, 1 VS
    (0x0D2C, 0x0D2C, [0x0D3F], []),  # ബ്ബ — 429 occ, 1 VS
    (0x0D2F, 0x0D2E, [], []),  # യ്മ — 426 occ, 0 VS
    (0x0D24, 0x0D15, [0x0D3E], []),  # ത്ക — 422 occ, 1 VS
    (0x0D21, 0x0D2F, [0x0D42], []),  # ഡ്യ — 411 occ, 1 VS
    (0x0D24, 0x0D2A, [0x0D3E], []),  # ത്പ — 395 occ, 1 VS
    (0x0D38, 0x0D30, [0x0D3E], []),  # സ്ര — 390 occ, 1 VS
    (0x0D38, 0x0D28, [0x0D47], []),  # സ്ന — 377 occ, 1 VS
    (0x0D21, 0x0D35, [], []),  # ഡ്വ — 366 occ, 0 VS
    (0x0D21, 0x0D1C, [0x0D3F], []),  # ഡ്ജ — 343 occ, 1 VS
    (0x0D2C, 0x0D2F, [0x0D42], []),  # ബ്യ — 328 occ, 1 VS
    (0x0D2B, 0x0D31, [], []),  # ഫ്റ — 323 occ, 0 VS
    (0x0D17, 0x0D27, [], []),  # ഗ്ധ — 322 occ, 0 VS
    (0x0D34, 0x0D24, [], []),  # ഴ്ത — 319 occ, 0 VS
    (0x0D37, 0x0D20, [0x0D3F], []),  # ഷ്ഠ — 319 occ, 1 VS
    (0x0D2F, 0x0D21, [], []),  # യ്ഡ — 306 occ, 0 VS
    (0x0D1F, 0x0D2F, [0x0D42], []),  # ട്യ — 298 occ, 1 VS
    (0x0D15, 0x0D21, [], []),  # ക്ഡ — 296 occ, 0 VS
    (0x0D17, 0x0D28, [0x0D3F], []),  # ഗ്ന — 295 occ, 1 VS
    (0x0D1F, 0x0D38, [], []),  # ട്സ — 294 occ, 0 VS
    (0x0D37, 0x0D15, [], []),  # ഷ്ക — 287 occ, 0 VS
    (0x0D2A, 0x0D28, [], []),  # പ്ന — 286 occ, 0 VS
    (0x0D31, 0x0D2F, [0x0D42], []),  # റ്യ — 281 occ, 1 VS
    (0x0D32, 0x0D15, [], []),  # ല്ക — 277 occ, 0 VS
    (0x0D34, 0x0D28, [0x0D3E], []),  # ഴ്ന — 275 occ, 1 VS
    (0x0D25, 0x0D2F, [], []),  # ഥ്യ — 266 occ, 0 VS
    (0x0D24, 0x0D2D, [0x0D41], []),  # ത്ഭ — 259 occ, 1 VS
    (0x0D21, 0x0D2E, [0x0D3F], []),  # ഡ്മ — 249 occ, 1 VS
    (0x0D2B, 0x0D32, [0x0D3E], []),  # ഫ്ല — 239 occ, 1 VS
    (0x0D15, 0x0D31, [], []),  # ക്റ — 218 occ, 0 VS
    (0x0D2E, 0x0D30, [0x0D3E], []),  # മ്ര — 217 occ, 1 VS
    (0x0D2F, 0x0D28, [], []),  # യ്ന — 216 occ, 0 VS
    (0x0D2B, 0x0D17, [0x0D3E], []),  # ഫ്ഗ — 208 occ, 1 VS
    (0x0D2E, 0x0D2C, [], []),  # മ്ബ — 199 occ, 0 VS
    (0x0D31, 0x0D38, [], []),  # റ്സ — 198 occ, 0 VS
    (0x0D2D, 0x0D30, [0x0D3E], []),  # ഭ്ര — 195 occ, 1 VS
    (0x0D2F, 0x0D38, [], []),  # യ്സ — 191 occ, 0 VS
    (0x0D27, 0x0D30, [], []),  # ധ്ര — 181 occ, 0 VS
    (0x0D21, 0x0D21, [0x0D3F], []),  # ഡ്ഡ — 177 occ, 1 VS
    (0x0D1C, 0x0D35, [], []),  # ജ്വ — 177 occ, 0 VS
    (0x0D15, 0x0D28, [], []),  # ക്ന — 164 occ, 0 VS
    (0x0D38, 0x0D2B, [], []),  # സ്ഫ — 163 occ, 0 VS
    (0x0D39, 0x0D28, [], []),  # ഹ്ന — 163 occ, 0 VS
    (0x0D28, 0x0D25, [], []),  # ന്ഥ — 163 occ, 0 VS
    (0x0D37, 0x0D2A, [], []),  # ഷ്പ — 161 occ, 0 VS
    (0x0D38, 0x0D1C, [0x0D3F], []),  # സ്ജ — 158 occ, 1 VS
    (0x0D1C, 0x0D2E, [], []),  # ജ്മ — 157 occ, 0 VS
    (0x0D2A, 0x0D37, [], []),  # പ്ഷ — 156 occ, 0 VS
    (0x0D1A, 0x0D35, [], []),  # ച്വ — 153 occ, 0 VS
    (0x0D39, 0x0D35, [0x0D3E], []),  # ഹ്വ — 151 occ, 1 VS
    (0x0D2C, 0x0D38, [], []),  # ബ്സ — 151 occ, 0 VS
    (0x0D23, 0x0D20, [], []),  # ണ്ഠ — 147 occ, 0 VS
    (0x0D38, 0x0D21, [], []),  # സ്ഡ — 147 occ, 0 VS
    (0x0D26, 0x0D2E, [], []),  # ദ്മ — 140 occ, 0 VS
    (0x0D1A, 0x0D2F, [], []),  # ച്യ — 139 occ, 0 VS
    (0x0D27, 0x0D35, [], []),  # ധ്വ — 137 occ, 0 VS
    (0x0D36, 0x0D32, [], []),  # ശ്ല — 129 occ, 0 VS
    (0x0D2B, 0x0D2F, [0x0D42], []),  # ഫ്യ — 124 occ, 1 VS
    (0x0D21, 0x0D38, [], []),  # ഡ്സ — 120 occ, 0 VS
    (0x0D25, 0x0D35, [0x0D3F], []),  # ഥ്വ — 117 occ, 1 VS
    (0x0D2F, 0x0D31, [], []),  # യ്റ — 107 occ, 0 VS
    (0x0D39, 0x0D32, [], []),  # ഹ്ല — 107 occ, 0 VS
    (0x0D17, 0x0D35, [], []),  # ഗ്വ — 105 occ, 0 VS
    (0x0D19, 0x0D1F, [], []),  # ങ്ട — 103 occ, 0 VS
    (0x0D31, 0x0D2E, [], []),  # റ്മ — 103 occ, 0 VS
    (0x0D39, 0x0D31, [], []),  # ഹ്റ — 102 occ, 0 VS
    (0x0D28, 0x0D2A, [], []),  # ന്പ — 100 occ, 0 VS
]

# Depth-2 conjunct triples: (c1, c2, c3, vowel_signs, modifiers).
# cluster = c1 + virama + c2 + virama + c3 [+ vowel_sign] — 5 or 6 codepoints.
# VS + modifier together = 7 codepoints; exceeds KEY_MAX_CP, so only one per entry.
# Corpus-derived from AI4Bharat IndicCorp v2 Malayalam (ml.txt, 100K sentences).
# Threshold: ≥ 5 triple occurrences; VS included if ≥ 3 co-occurrences with the triple.
# 190 distinct triples; sorted by descending corpus frequency.
CONJUNCT_TRIPLES: list[tuple[int, int, int, list[int], list[int]]] = [
    (0x0D38, 0x0D31, 0x0D31, [0x0D3F, 0x0D47, 0x0D3E, 0x0D41, 0x0D4B, 0x0D40, 0x0D48, 0x0D46], []),  # സ്റ്റ — 11179 occ
    (0x0D28, 0x0D24, 0x0D30, [0x0D3F, 0x0D3E], []),  # ന്ത്ര — 8892 occ
    (0x0D2F, 0x0D15, 0x0D15, [0x0D41, 0x0D3E, 0x0D3F, 0x0D46, 0x0D4A], []),  # യ്ക്ക — 7778 occ
    (0x0D28, 0x0D26, 0x0D30, [0x0D40, 0x0D3F], []),  # ന്ദ്ര — 5746 occ
    (0x0D28, 0x0D24, 0x0D2F, [0x0D3E], []),  # ന്ത്യ — 5527 occ
    (0x0D38, 0x0D24, 0x0D30, [0x0D40, 0x0D3F], []),  # സ്ത്ര — 2692 occ
    (0x0D37, 0x0D1F, 0x0D30, [0x0D40], []),  # ഷ്ട്ര — 2325 occ
    (0x0D15, 0x0D37, 0x0D2F, [], []),  # ക്ഷ്യ — 1200 occ
    (0x0D38, 0x0D1F, 0x0D30, [0x0D47, 0x0D3F, 0x0D40, 0x0D3E, 0x0D4B], []),  # സ്ട്ര — 764 occ
    (0x0D26, 0x0D27, 0x0D2F, [0x0D3E], []),  # ദ്ധ്യ — 628 occ
    (0x0D2A, 0x0D31, 0x0D31, [0x0D3F], []),  # പ്റ്റ — 611 occ
    (0x0D15, 0x0D37, 0x0D2E, [0x0D3F], []),  # ക്ഷ്മ — 390 occ
    (0x0D24, 0x0D30, 0x0D2F, [], []),  # ത്ര്യ — 368 occ
    (0x0D2E, 0x0D2A, 0x0D2F, [0x0D42, 0x0D3E], []),  # മ്പ്യ — 365 occ
    (0x0D2B, 0x0D31, 0x0D31, [0x0D3F], []),  # ഫ്റ്റ — 320 occ
    (0x0D34, 0x0D24, 0x0D24, [0x0D3F, 0x0D41], []),  # ഴ്ത്ത — 318 occ
    (0x0D24, 0x0D38, 0x0D2F, [], []),  # ത്സ്യ — 309 occ
    (0x0D31, 0x0D31, 0x0D2F, [0x0D42, 0x0D3E], []),  # റ്റ്യ — 276 occ
    (0x0D15, 0x0D1F, 0x0D30, [0x0D3F, 0x0D4B], []),  # ക്ട്ര — 265 occ
    (0x0D34, 0x0D1A, 0x0D1A, [], []),  # ഴ്ച്ച — 216 occ
    (0x0D15, 0x0D31, 0x0D31, [0x0D3F, 0x0D40], []),  # ക്റ്റ — 211 occ
    (0x0D38, 0x0D24, 0x0D2F, [0x0D3E], []),  # സ്ത്യ — 183 occ
    (0x0D2E, 0x0D2E, 0x0D2F, [0x0D42], []),  # മ്മ്യ — 181 occ
    (0x0D38, 0x0D2A, 0x0D30, [0x0D3F], []),  # സ്പ്ര — 175 occ
    (0x0D15, 0x0D15, 0x0D21, [], []),  # ക്ക്ഡ — 168 occ
    (0x0D31, 0x0D31, 0x0D38, [], []),  # റ്റ്സ — 141 occ
    (0x0D28, 0x0D27, 0x0D2F, [], []),  # ന്ധ്യ — 141 occ
    (0x0D2E, 0x0D2A, 0x0D30, [], []),  # മ്പ്ര — 140 occ
    (0x0D2C, 0x0D32, 0x0D2F, [0x0D41, 0x0D42], []),  # ബ്ല്യ — 132 occ
    (0x0D28, 0x0D27, 0x0D30, [0x0D3E], []),  # ന്ധ്ര — 130 occ
    (0x0D34, 0x0D28, 0x0D28, [], []),  # ഴ്ന്ന — 117 occ
    (0x0D2F, 0x0D2A, 0x0D2A, [0x0D4B], []),  # യ്പ്പ — 114 occ
    (0x0D32, 0x0D32, 0x0D2F, [0x0D3E], []),  # ല്ല്യ — 107 occ
    (0x0D38, 0x0D15, 0x0D15, [0x0D3E], []),  # സ്ക്ക — 104 occ
    (0x0D24, 0x0D25, 0x0D2F, [], []),  # ത്ഥ്യ — 102 occ
    (0x0D38, 0x0D15, 0x0D30, [0x0D40], []),  # സ്ക്ര — 90 occ
    (0x0D2F, 0x0D31, 0x0D31, [], []),  # യ്റ്റ — 88 occ
    (0x0D31, 0x0D31, 0x0D2E, [0x0D4B, 0x0D46], []),  # റ്റ്മ — 84 occ
    (0x0D15, 0x0D38, 0x0D2A, [], []),  # ക്സ്പ — 82 occ
    (0x0D17, 0x0D26, 0x0D27, [], []),  # ഗ്ദ്ധ — 79 occ
    (0x0D23, 0x0D21, 0x0D2F, [], []),  # ണ്ഡ്യ — 79 occ
    (0x0D1E, 0x0D1A, 0x0D35, [], []),  # ഞ്ച്വ — 78 occ
    (0x0D1F, 0x0D1F, 0x0D38, [], []),  # ട്ട്സ — 70 occ
    (0x0D32, 0x0D15, 0x0D15, [0x0D41], []),  # ല്ക്ക — 67 occ
    (0x0D1A, 0x0D1A, 0x0D21, [0x0D3F], []),  # ച്ച്ഡ — 67 occ
    (0x0D2F, 0x0D24, 0x0D24, [], []),  # യ്ത്ത — 60 occ
    (0x0D2F, 0x0D38, 0x0D2C, [0x0D41], []),  # യ്സ്ബ — 59 occ
    (0x0D24, 0x0D15, 0x0D15, [0x0D3E], []),  # ത്ക്ക — 57 occ
    (0x0D28, 0x0D26, 0x0D2F, [], []),  # ന്ദ്യ — 56 occ
    (0x0D1F, 0x0D1F, 0x0D2E, [0x0D46], []),  # ട്ട്മ — 56 occ
    (0x0D31, 0x0D31, 0x0D32, [], []),  # റ്റ്ല — 55 occ
    (0x0D31, 0x0D31, 0x0D28, [], []),  # റ്റ്ന — 55 occ
    (0x0D24, 0x0D24, 0x0D35, [], []),  # ത്ത്വ — 55 occ
    (0x0D1A, 0x0D1A, 0x0D2A, [0x0D3F], []),  # ച്ച്പ — 52 occ
    (0x0D15, 0x0D38, 0x0D31, [], []),  # ക്സ്റ — 52 occ
    (0x0D1F, 0x0D1F, 0x0D2B, [0x0D4B], []),  # ട്ട്ഫ — 51 occ
    (0x0D28, 0x0D28, 0x0D2F, [0x0D3E], []),  # ന്ന്യ — 51 occ
]

# Script-native digits: U+0D66 ൦ … U+0D6F ൯ (MALAYALAM DIGIT ZERO..NINE)
DIGITS: list[int] = list(range(0x0D66, 0x0D70))