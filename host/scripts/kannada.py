"""
Kannada script definition for Akshara cluster enumeration.

Codepoint ranges from Unicode Standard, Kannada block (U+0C80–U+0CFF).
Rule table values match aks_rule_table_t in the .aks format spec.
"""

SCRIPT_ID: int = 0x01

# ── Rule table values (written verbatim to aks_rule_table_t in .aks header) ──

CONSONANT_RANGE: tuple[int, int] = (0x0C95, 0x0CB9)  # KA..HA
VIRAMA: int = 0x0CCD                                   # KANNADA SIGN VIRAMA
VOWEL_SIGN_RANGE: tuple[int, int] = (0x0CBE, 0x0CCD)  # coarse range for segmenter
MODIFIER_RANGE: tuple[int, int] = (0x0C82, 0x0C83)    # anusvara..visarga
MAX_CONJUNCT_DEPTH: int = 2

# ── Enumerable codepoints (explicit lists; unassigned Unicode slots excluded) ─

# Independent vowels: U+0C85–U+0C94 (U+0C8D and U+0C91 are unassigned)
INDEPENDENT_VOWELS: list[int] = [
    0x0C85, 0x0C86, 0x0C87, 0x0C88, 0x0C89, 0x0C8A, 0x0C8B, 0x0C8C,  # A..VOCALIC L
    0x0C8E, 0x0C8F, 0x0C90,                                             # E, EE, AI
    0x0C92, 0x0C93, 0x0C94,                                             # O, OO, AU
]

# Consonants: U+0C95–U+0CB9 (U+0CA9 and U+0CB4 are unassigned)
CONSONANTS: list[int] = [
    *range(0x0C95, 0x0CA9),  # KA(95)..NA(A8)  — 20 consonants
    *range(0x0CAA, 0x0CB4),  # PA(AA)..LLA(B3) — 10 consonants
    *range(0x0CB5, 0x0CBA),  # VA(B5)..HA(B9)  —  5 consonants
]

# Dependent vowel signs (three non-contiguous sub-ranges; virama U+0CCD excluded)
VOWEL_SIGNS: list[int] = [
    *range(0x0CBE, 0x0CC5),  # AA..VOCALIC_RR  (U+0CC5 unassigned)
    *range(0x0CC6, 0x0CC9),  # E..AI           (U+0CC9 unassigned)
    *range(0x0CCA, 0x0CCD),  # O..AU           (U+0CCD is virama, excluded here)
]

MODIFIERS: list[int] = [
    0x0C82,  # KANNADA SIGN ANUSVARA (ಂ)
    0x0C83,  # KANNADA SIGN VISARGA  (ಃ)
]

# High-frequency consonants eligible for conjunct enumeration.
# Both consonants in a pair must appear here for the conjunct to be enumerated.
# Tier 1: ರ ದ ತ ಕ ಗ ನ ಮ — most frequent by corpus analysis.
# Tier 2: ಪ ಸ ಲ ಬ ವ ಹ ಯ — next most frequent; covers ಪ್ರ, ಸ್ಕ, ಲ್ಲ, ಬ್ಬ, ವ್ಯ, ಹ್ರ, ಕ್ಯ.
# Tier 3: ಷ ಶ ಣ ಧ — covers ಕ್ಷ (ಅಕ್ಷರ, ದಕ್ಷ), ರ್ಶ (ದರ್ಶನ), ಣ and ಧ conjuncts.
# Rare ಘ ಙ ಝ ಱ excluded.
COMMON_CONSONANTS: list[int] = [
    # Tier 1
    0x0CB0,  # ರ RA
    0x0CA6,  # ದ DA
    0x0CA4,  # ತ TA
    0x0C95,  # ಕ KA
    0x0C97,  # ಗ GA
    0x0CA8,  # ನ NA
    0x0CAE,  # ಮ MA
    # Tier 2
    0x0CAA,  # ಪ PA
    0x0CB8,  # ಸ SA
    0x0CB2,  # ಲ LA
    0x0CB3,  # ಳ LLA
    0x0CAC,  # ಬ BA
    0x0CB5,  # ವ VA
    0x0CB9,  # ಹ HA
    0x0CAF,  # ಯ YA
    0x0C9C,  # ಜ JA  
    0x0C9E,  # ಞ NYA 
    # Tier 3
    0x0CB7,  # ಷ SSA
    0x0CB6,  # ಶ SHA
    0x0CA3,  # ಣ NNA
    0x0CA7,  # ಧ DHA
]

# Script-native digits: U+0CE6 ೦ … U+0CEF ೯ (KANNADA DIGIT ZERO..NINE)
DIGITS: list[int] = list(range(0x0CE6, 0x0CF0))
