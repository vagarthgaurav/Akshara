"""
Kannada script definition for Akshara cluster enumeration.

Codepoint ranges from Unicode Standard, Kannada block (U+0C80–U+0CFF).
Rule table values match aks_rule_table_t in the .aks format spec.
"""

SCRIPT_ID: int = 0x01

# ── Rule table values (written verbatim to aks_rule_table_t in .aks header) ──

CONSONANT_RANGE: tuple[int, int] = (0x0C95, 0x0CB9)  # KA..HA
VIRAMA: int = 0x0CCD  # KANNADA SIGN VIRAMA
VOWEL_SIGN_RANGE: tuple[int, int] = (0x0CBE, 0x0CCD)  # coarse range for segmenter
MODIFIER_RANGE: tuple[int, int] = (0x0C82, 0x0C83)  # anusvara..visarga
MAX_CONJUNCT_DEPTH: int = 2

# ── Enumerable codepoints (explicit lists; unassigned Unicode slots excluded) ─

# Independent vowels: U+0C85–U+0C94 (U+0C8D and U+0C91 are unassigned)
INDEPENDENT_VOWELS: list[int] = [
    0x0C85,
    0x0C86,
    0x0C87,
    0x0C88,
    0x0C89,
    0x0C8A,
    0x0C8B,
    0x0C8C,  # A..VOCALIC L
    0x0C8E,
    0x0C8F,
    0x0C90,  # E, EE, AI
    0x0C92,
    0x0C93,
    0x0C94,  # O, OO, AU
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
    0x0C82,  # KANNADA SIGN ANUSVARA (ಂ) — standalone form, needed for OOV fallback
    # 0x0C83 KANNADA SIGN VISARGA (ಃ) omitted — too rare to justify the flash cost
]

# Consonants whose (consonant + vowel_sign + modifier) clusters appear in common text.
# Each entry is (consonant, vowel_signs, modifiers): generates C + VS + M for each
# listed VS × modifier combination. Anusvara = U+0C82, visarga = U+0C83.
# Bare C + modifier (no VS) is already covered by the simple-cluster loop via MODIFIERS.

MODIFIER_CLUSTERS: list[tuple[int, list[int], list[int]]] = [
    (0x0C95, [0x0CCA, 0x0CC7, 0x0CBE, 0x0CC6, 0x0CC1, 0x0CBF, 0x0CCC], [0x0C82]),  # ಕ — ಕೊಂ ಕೇಂ ಕಾಂ ಕೆಂ ಕುಂ ಕಿಂ ಕೌಂ  (60,607 20,281 19,739 15,856 4,701 3,765 1,278)
    (0x0CB0, [0x0CBF, 0x0CCA, 0x0CC6, 0x0CC7, 0x0CBE], [0x0C82]),  # ರ — ರಿಂ ರೊಂ ರೆಂ ರೇಂ ರಾಂ  (49,096 7,114 4,922 3,282 2,729)
    (0x0CB9, [0x0CCA, 0x0CBF, 0x0CC6, 0x0CBE], [0x0C82]),  # ಹ — ಹೊಂ ಹಿಂ ಹೆಂ ಹಾಂ  (30,810 27,747 1,855 974)
    (0x0CA6, [0x0CBF, 0x0CCA, 0x0CC6, 0x0CC1, 0x0CBE], [0x0C82, 0x0C83]),  # ದ — ದಿಂ ದೊಂ ದೆಂ ದುಂ ದಾಂ ದುಃ  (42,448 9,017 4,055 1,319 915 835)
    (0x0CAE, [0x0CC1, 0x0CBE, 0x0CC6, 0x0CBF], [0x0C82]),  # ಮ — ಮುಂ ಮಾಂ ಮೆಂ ಮಿಂ  (43,552 5,655 3,668 1,718)
    (0x0C97, [0x0CCA, 0x0CC1, 0x0CBE, 0x0CBF, 0x0CC6], [0x0C82]),  # ಗ — ಗೊಂ ಗುಂ ಗಾಂ ಗಿಂ ಗೆಂ  (27,021 9,243 7,157 6,968 1,246)
    (0x0CAF, [0x0CBF, 0x0CCA, 0x0CC6, 0x0CBE], [0x0C82]),  # ಯ — ಯಿಂ ಯೊಂ ಯೆಂ ಯಾಂ  (34,541 10,182 3,485 3,186)
    (0x0CA8, [0x0CBF, 0x0CBE, 0x0CC6, 0x0CCA, 0x0CCB], [0x0C82]),  # ನ — ನಿಂ ನಾಂ ನೆಂ ನೊಂ ನೋಂ  (27,495 4,492 3,699 3,588 1,531)
    (0x0CB8, [0x0CBF, 0x0CBE, 0x0CCB, 0x0CC6, 0x0CC1, 0x0CCC], [0x0C82]),  # ಸ — ಸಿಂ ಸಾಂ ಸೋಂ ಸೆಂ ಸುಂ ಸೌಂ  (12,549 7,946 6,024 5,607 3,833 1,710)
    (0x0CA4, [0x0CC1, 0x0CBF, 0x0CBE, 0x0CCA, 0x0CC6], [0x0C82]),  # ತ — ತುಂ ತಿಂ ತಾಂ ತೊಂ ತೆಂ  (11,758 11,004 5,752 3,937 1,890)
    (0x0CB3, [0x0CBF, 0x0CCA, 0x0CC6, 0x0CBE], [0x0C82]),  # ಳ — ಳಿಂ ಳೊಂ ಳೆಂ ಳಾಂ  (22,988 5,472 2,881 1,640)
    (0x0CB5, [0x0CC6, 0x0CCA, 0x0CBF, 0x0CBE, 0x0CC7], [0x0C82]),  # ವ — ವೆಂ ವೊಂ ವಿಂ ವಾಂ ವೇಂ  (15,587 5,941 4,994 1,505 1,005)
    (0x0CAC, [0x0CC6, 0x0CBE, 0x0CBF], [0x0C82]),  # ಬ — ಬೆಂ ಬಾಂ ಬಿಂ  (22,650 3,390 2,735)
    (0x0CB2, [0x0CBF, 0x0CC6, 0x0CBE, 0x0CC8], [0x0C82]),  # ಲ — ಲಿಂ ಲೆಂ ಲಾಂ ಲೈಂ  (9,369 3,124 1,990 1,478)
    (0x0C9F, [0x0CC1, 0x0CBF, 0x0CC6], [0x0C82]),  # ಟ — ಟುಂ ಟಿಂ ಟೆಂ  (8,931 3,830 1,525)
    (0x0C9A, [0x0CBF, 0x0CBE, 0x0CC6], [0x0C82]),  # ಚ — ಚಿಂ ಚಾಂ ಚೆಂ  (4,560 2,213 1,481)
    (0x0CB6, [0x0CBE], [0x0C82]),  # ಶ — ಶಾಂ  (5,537)
    (0x0CAA, [0x0CBE, 0x0CBF], [0x0C82]),  # ಪ — ಪಾಂ ಪಿಂ  (3,152 2,256)
    (0x0CA1, [0x0CBE, 0x0CC6, 0x0CBF], [0x0C82]),  # ಡ — ಡಾಂ ಡೆಂ ಡಿಂ  (1,537 1,123 1,056)
    (0x0C9C, [0x0CBF, 0x0CC7], [0x0C82]),  # ಜ — ಜಿಂ ಜೇಂ  (1,329 909)
    (0x0CAD, [0x0CBE], [0x0C82]),  # ಭ — ಭಾಂ  (1,289)
    (0x0C96, [0x0CBE], [0x0C82]),  # ಖ — ಖಾಂ  (808)
]

# Attested conjunct pairs to precompute.
# Each entry is (c1, c2, vowel_signs, modifiers): c1 + virama + c2, precomputing
# only the vowel-sign and modifier forms that appear in the corpus. The bare
# conjunct (no VS, no modifier) is always included. Empty lists mean only the bare
# conjunct is precomputed. MODIFIERS is applied to all simple clusters; per-conjunct
# modifier lists here let you selectively add anusvara/visarga to high-frequency conjuncts.
CONJUNCT_PAIRS: list[tuple[int, int, list[int], list[int]]] = [
    (0x0CB2, 0x0CB2, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC2, 0x0CC6, 0x0CC7, 0x0CCA, 0x0CCB], [0x0C82]),  # ಲ್ಲ — 790,859 occ, 8 VS, 6,026 anusv
    (0x0CA4, 0x0CA4, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC1, 0x0CC2, 0x0CC6, 0x0CC7, 0x0CCA], [0x0C82]),  # ತ್ತ — 641,808 occ, 8 VS, 7,025 anusv
    (0x0CA8, 0x0CA8, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC2, 0x0CC6, 0x0CC7, 0x0CC8, 0x0CCA, 0x0CCB], [0x0C82]),  # ನ್ನ — 610,676 occ, 9 VS, 6,540 anusv
    (0x0CA6, 0x0CA6, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC1, 0x0CC2, 0x0CC6, 0x0CC7], [0x0C82]),  # ದ್ದ — 366,656 occ, 7 VS, 4,101 anusv
    (0x0CAA, 0x0CB0, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC6, 0x0CC7, 0x0CCA, 0x0CCB, 0x0CCC], [0x0C82]),  # ಪ್ರ — 314,673 occ, 8 VS, 5,586 anusv
    (0x0C95, 0x0C95, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC2, 0x0CC6, 0x0CC7, 0x0CCA], [0x0C82]),  # ಕ್ಕ — 215,427 occ, 7 VS, 8,957 anusv
    (0x0CA4, 0x0CB0, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC1, 0x0CC6, 0x0CCB], [0x0C82]),  # ತ್ರ — 172,019 occ, 6 VS, 900 anusv
    (0x0C95, 0x0CB7, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC6, 0x0CC7], [0x0C82]),  # ಕ್ಷ — 157,973 occ, 5 VS, 1,109 anusv
    (0x0C9F, 0x0C9F, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6], [0x0C82]),  # ಟ್ಟ — 154,955 occ, 4 VS, 1,150 anusv
    (0x0CB7, 0x0C9F, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6, 0x0CC7, 0x0CCA], [0x0C82]),  # ಷ್ಟ — 105,736 occ, 6 VS, 1,094 anusv
    (0x0CB8, 0x0CA5, [0x0CBE, 0x0CBF, 0x0CC6], []),  # ಸ್ಥ — 98,329 occ, 3 VS
    (0x0CB3, 0x0CB3, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6], []),  # ಳ್ಳ — 88,741 occ, 4 VS
    (0x0CAE, 0x0CAE, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6, 0x0CC7], [0x0C82]),  # ಮ್ಮ — 88,116 occ, 5 VS, 1,138 anusv
    (0x0CB8, 0x0CA4, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6], [0x0C82]),  # ಸ್ತ — 86,959 occ, 4 VS, 1,085 anusv
    (0x0C95, 0x0CB0, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC6, 0x0CC8, 0x0CCA, 0x0CCB], [0x0C82]),  # ಕ್ರ — 81,173 occ, 7 VS, 2,265 anusv
    (0x0C9A, 0x0C9A, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6], []),  # ಚ್ಚ — 81,017 occ, 4 VS
    (0x0C97, 0x0CB0, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC6, 0x0CC7], [0x0C82]),  # ಗ್ರ — 73,661 occ, 5 VS, 5,884 anusv
    (0x0CB5, 0x0CAF, [0x0CBE], [0x0C82]),  # ವ್ಯ — 70,395 occ, 1 VS, 929 anusv
    (0x0CA6, 0x0CAF, [0x0CBE, 0x0CC1, 0x0CCB], [0x0C82]),  # ದ್ಯ — 69,746 occ, 3 VS, 4,025 anusv
    (0x0CA4, 0x0CAF, [0x0CBE, 0x0CC1, 0x0CC6, 0x0CC7], [0x0C82]),  # ತ್ಯ — 69,659 occ, 4 VS, 8,219 anusv
    (0x0CA7, 0x0CAF, [0x0CBE, 0x0CC6], []),  # ಧ್ಯ — 64,625 occ, 2 VS
    (0x0CB0, 0x0CAF, [0x0CBE], [0x0C82]),  # ರ್ಯ — 64,223 occ, 1 VS, 1,455 anusv
    (0x0CA6, 0x0CB0, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC1, 0x0CC6, 0x0CCB], []),  # ದ್ರ — 62,532 occ, 6 VS
    (0x0C95, 0x0CA4, [0x0CBE, 0x0CBF], []),  # ಕ್ತ — 60,504 occ, 2 VS
    (0x0CA6, 0x0CA7, [0x0CBE, 0x0CBF], [0x0C82]),  # ದ್ಧ — 55,664 occ, 2 VS, 2,263 anusv
    (0x0CAA, 0x0CAA, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6], [0x0C82]),  # ಪ್ಪ — 51,794 occ, 4 VS, 2,550 anusv
    (0x0CB8, 0x0CB5, [0x0CBE, 0x0CBF, 0x0CC0], [0x0C82]),  # ಸ್ವ — 51,082 occ, 3 VS, 1,809 anusv
    (0x0CA8, 0x0CAF, [0x0CBE, 0x0CC2], []),  # ನ್ಯ — 50,627 occ, 2 VS
    (0x0CB8, 0x0C9F, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC1, 0x0CC6, 0x0CC7, 0x0CCB], [0x0C82]),  # ಸ್ಟ — 49,416 occ, 7 VS, 1,337 anusv
    (0x0CB0, 0x0CAE, [0x0CBE, 0x0CBF], []),  # ರ್ಮ — 47,783 occ, 2 VS
    (0x0CAC, 0x0CAC, [0x0CBE, 0x0CBF, 0x0CC1], [0x0C82]),  # ಬ್ಬ — 46,775 occ, 3 VS, 5,050 anusv
    (0x0C9F, 0x0CB0, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC6, 0x0CC7, 0x0CC8, 0x0CCA, 0x0CCB], [0x0C82]),  # ಟ್ರ — 44,930 occ, 8 VS, 1,749 anusv
    (0x0CB0, 0x0C95, [0x0CBE, 0x0CBF], []),  # ರ್ಕ — 44,407 occ, 2 VS
    (0x0CB0, 0x0CA5, [0x0CBF], []),  # ರ್ಥ — 43,905 occ, 1 VS
    (0x0C97, 0x0C97, [0x0CBF, 0x0CC1, 0x0CC6], []),  # ಗ್ಗ — 42,815 occ, 3 VS
    (0x0CB0, 0x0CB5, [0x0CBE, 0x0CBF, 0x0CC6, 0x0CC7], []),  # ರ್ವ — 41,931 occ, 4 VS
    (0x0CA3, 0x0CA3, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6], []),  # ಣ್ಣ — 40,862 occ, 4 VS
    (0x0C96, 0x0CAF, [0x0CBE, 0x0CC6], []),  # ಖ್ಯ — 40,758 occ, 2 VS
    (0x0CB0, 0x0CB7, [0x0CBF], []),  # ರ್ಷ — 40,103 occ, 1 VS
    (0x0C9C, 0x0CAF, [0x0CBE, 0x0CCB], []),  # ಜ್ಯ — 36,516 occ, 2 VS
    (0x0CB6, 0x0CB0, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC7], [0x0C82]),  # ಶ್ರ — 34,036 occ, 4 VS, 837 anusv
    (0x0CB8, 0x0CAA, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC6, 0x0CC7, 0x0CCB], [0x0C82]),  # ಸ್ಪ — 33,198 occ, 6 VS, 1,694 anusv
    (0x0CB8, 0x0CAF, [0x0CBE, 0x0CC6], [0x0C82]),  # ಸ್ಯ — 32,136 occ, 2 VS, 1,109 anusv
    (0x0CB6, 0x0CB5, [0x0CBE, 0x0CC7], []),  # ಶ್ವ — 30,975 occ, 2 VS
    (0x0CB0, 0x0CA4, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6], []),  # ರ್ತ — 29,580 occ, 4 VS
    (0x0CB2, 0x0CAA, [0x0CBF], []),  # ಲ್ಪ — 28,809 occ, 1 VS
    (0x0CA1, 0x0CA1, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6], []),  # ಡ್ಡ — 28,460 occ, 4 VS
    (0x0CB0, 0x0C97, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC6], []),  # ರ್ಗ — 27,690 occ, 4 VS
    (0x0CB8, 0x0C95, [0x0CBE, 0x0CBF, 0x0CC2, 0x0CC3, 0x0CCB], [0x0C82]),  # ಸ್ಕ — 26,837 occ, 5 VS, 841 anusv
    (0x0CB0, 0x0CA3, [0x0CBE, 0x0CBF], []),  # ರ್ಣ — 24,603 occ, 2 VS
    (0x0CB0, 0x0CB6, [0x0CBF, 0x0CC6], []),  # ರ್ಶ — 24,426 occ, 2 VS
    (0x0CA8, 0x0CB8, [0x0CBE, 0x0CBF], []),  # ನ್ಸ — 23,409 occ, 2 VS
    (0x0CA4, 0x0CB5, [], []),  # ತ್ವ — 22,973 occ, 0 VS
    (0x0CB0, 0x0CA8, [0x0CBE, 0x0CBF, 0x0CC6], []),  # ರ್ನ — 21,717 occ, 3 VS
    (0x0C9C, 0x0C9E, [0x0CBE, 0x0CC6], []),  # ಜ್ಞ — 21,289 occ, 2 VS
    (0x0CB2, 0x0CAF, [0x0CBE, 0x0CC1, 0x0CC2], [0x0C82]),  # ಲ್ಯ — 21,157 occ, 3 VS, 2,644 anusv
    (0x0CAC, 0x0CB0, [0x0CBE, 0x0CBF, 0x0CC6, 0x0CC7], [0x0C82]),  # ಬ್ರ — 20,299 occ, 4 VS, 877 anusv
    (0x0C95, 0x0CB8, [0x0CBE, 0x0CBF], []),  # ಕ್ಸ — 20,185 occ, 2 VS
    (0x0CB0, 0x0C9F, [0x0CBF], []),  # ರ್ಟ — 19,924 occ, 1 VS
    (0x0CB0, 0x0CA7, [0x0CBE, 0x0CBF, 0x0CC6], []),  # ರ್ಧ — 19,712 occ, 3 VS
    (0x0CAC, 0x0CAF, [0x0CBE], [0x0C82]),  # ಬ್ಯ — 19,395 occ, 1 VS, 9,254 anusv
    (0x0C97, 0x0CAF, [0x0CBE, 0x0CC2], []),  # ಗ್ಯ — 18,680 occ, 2 VS
    (0x0CA4, 0x0CB8, [0x0CBE, 0x0CC6], []),  # ತ್ಸ — 18,389 occ, 2 VS
    (0x0C95, 0x0CAF, [0x0CBE, 0x0CC1, 0x0CC2], [0x0C82]),  # ಕ್ಯ — 18,121 occ, 3 VS, 1,548 anusv
    (0x0CB0, 0x0C9C, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6], []),  # ರ್ಜ — 18,078 occ, 4 VS
    (0x0CB0, 0x0CA6, [0x0CBF, 0x0CC7], []),  # ರ್ದ — 16,977 occ, 2 VS
    (0x0CB8, 0x0CB8, [0x0CBE, 0x0CBF, 0x0CC1, 0x0CC6], [0x0C82]),  # ಸ್ಸ — 16,527 occ, 4 VS, 1,010 anusv
    (0x0CAD, 0x0CAF, [0x0CBE], []),  # ಭ್ಯ — 15,542 occ, 1 VS
    (0x0CB0, 0x0CAD, [0x0CBF], []),  # ರ್ಭ — 15,358 occ, 1 VS
    (0x0CA4, 0x0CAE, [], []),  # ತ್ಮ — 14,734 occ, 0 VS
    (0x0CB0, 0x0C9A, [0x0CBF, 0x0CC1, 0x0CC6], []),  # ರ್ಚ — 14,626 occ, 3 VS
    (0x0CB0, 0x0CAA, [0x0CBE, 0x0CBF, 0x0CC1], []),  # ರ್ಪ — 14,570 occ, 3 VS
    (0x0CB0, 0x0CA1, [0x0CBF], []),  # ರ್ಡ — 14,383 occ, 1 VS
    (0x0CB7, 0x0CA0, [0x0CBE, 0x0CBF], []),  # ಷ್ಠ — 14,299 occ, 2 VS
    (0x0CA4, 0x0CA8, [0x0CBF], []),  # ತ್ನ — 13,836 occ, 1 VS
    (0x0CAE, 0x0CAF, [0x0CBE, 0x0CC1, 0x0CC2], [0x0C82]),  # ಮ್ಯ — 13,207 occ, 3 VS, 841 anusv
    (0x0CA4, 0x0CAA, [0x0CBE], []),  # ತ್ಪ — 13,081 occ, 1 VS
    (0x0C95, 0x0C9F, [0x0CBF, 0x0CC0, 0x0CC7, 0x0CCB], []),  # ಕ್ಟ — 12,855 occ, 4 VS
    (0x0CB2, 0x0C95, [0x0CC1], []),  # ಲ್ಕ — 12,795 occ, 1 VS
    (0x0CB7, 0x0CAF, [0x0CBE], []),  # ಷ್ಯ — 12,446 occ, 1 VS
    (0x0CB0, 0x0CB8, [0x0CBF], []),  # ರ್ಸ — 12,107 occ, 1 VS
    (0x0CAF, 0x0CAF, [0x0CC1], []),  # ಯ್ಯ — 11,426 occ, 1 VS
    (0x0CB7, 0x0CA3, [0x0CBE, 0x0CC1], []),  # ಷ್ಣ — 10,949 occ, 2 VS
    (0x0CAA, 0x0CA4, [0x0CBF], []),  # ಪ್ತ — 10,462 occ, 1 VS
    (0x0C97, 0x0CB2, [0x0CBE, 0x0CBF, 0x0CC6], [0x0C82]),  # ಗ್ಲ — 10,382 occ, 3 VS, 2,588 anusv
    (0x0CAF, 0x0C95, [0x0CC6], []),  # ಯ್ಕ — 10,239 occ, 1 VS
    (0x0CA6, 0x0CB5, [0x0CBE, 0x0CBF, 0x0CC0, 0x0CC7], [0x0C82]),  # ದ್ವ — 9,732 occ, 4 VS, 1,175 anusv
    (0x0C95, 0x0CB2, [0x0CBE, 0x0CBF], []),  # ಕ್ಲ — 9,197 occ, 2 VS
    (0x0CB8, 0x0CA8, [0x0CBE, 0x0CC7], []),  # ಸ್ನ — 9,122 occ, 2 VS
    (0x0CAB, 0x0CB0, [0x0CBE, 0x0CBF, 0x0CC6], [0x0C82]),  # ಫ್ರ — 9,070 occ, 3 VS, 2,288 anusv
    (0x0CAA, 0x0CB2, [0x0CBE, 0x0CBF, 0x0CC7], []),  # ಪ್ಲ — 9,035 occ, 3 VS
    (0x0CB8, 0x0CAE, [0x0CBE, 0x0CBF], []),  # ಸ್ಮ — 8,718 occ, 2 VS
    (0x0CAA, 0x0CAF, [0x0CBE, 0x0CC2], []),  # ಪ್ಯ — 8,635 occ, 2 VS
    (0x0C9F, 0x0CAF, [0x0CBE, 0x0CC2], [0x0C82]),  # ಟ್ಯ — 8,401 occ, 2 VS, 1,821 anusv
    (0x0CA1, 0x0CB0, [0x0CBE, 0x0CBF, 0x0CC8, 0x0CCB], []),  # ಡ್ರ — 8,308 occ, 4 VS
    (0x0CB6, 0x0CAF, [0x0CBE], []),  # ಶ್ಯ — 7,818 occ, 1 VS
    (0x0CA3, 0x0CAF, [], []),  # ಣ್ಯ — 7,721 occ, 0 VS
    (0x0CB6, 0x0C9A, [0x0CBF], []),  # ಶ್ಚ — 7,418 occ, 1 VS
    (0x0CB6, 0x0CA8, [0x0CBF, 0x0CC6], []),  # ಶ್ನ — 7,355 occ, 2 VS
    (0x0CB0, 0x0CB2, [0x0CBF, 0x0CC6], [0x0C82]),  # ರ್ಲ — 7,157 occ, 2 VS, 1,089 anusv
    (0x0CAC, 0x0CB2, [0x0CBE, 0x0CBF], []),  # ಬ್ಲ — 6,973 occ, 2 VS
    (0x0C9F, 0x0CB8, [], []),  # ಟ್ಸ — 6,924 occ, 0 VS
    (0x0CB2, 0x0CB8, [0x0CBF], []),  # ಲ್ಸ — 6,804 occ, 1 VS
    (0x0CB2, 0x0CB5, [0x0CBE, 0x0CBF, 0x0CC6], []),  # ಲ್ವ — 6,760 occ, 3 VS
    (0x0CB7, 0x0CAE, [0x0CBF, 0x0CC0], []),  # ಷ್ಮ — 6,752 occ, 2 VS
    (0x0C9C, 0x0C9C, [0x0CBE, 0x0CBF, 0x0CC6], []),  # ಜ್ಜ — 6,704 occ, 3 VS
    (0x0CB5, 0x0CB0, [], []),  # ವ್ರ — 6,636 occ, 0 VS
    (0x0CA8, 0x0CAE, [0x0CBE, 0x0CC2], []),  # ನ್ಮ — 6,618 occ, 2 VS
    (0x0CB0, 0x0CAC, [], [0x0C82]),  # ರ್ಬ — 6,605 occ, 0 VS, 1,457 anusv
    (0x0CB2, 0x0CA1, [], []),  # ಲ್ಡ — 6,409 occ, 0 VS
    (0x0CB9, 0x0CAF, [0x0CBE], [0x0C82]),  # ಹ್ಯ — 6,289 occ, 1 VS, 935 anusv
    (0x0CB8, 0x0CB2, [0x0CBE, 0x0CBF], [0x0C82]),  # ಸ್ಲ — 5,921 occ, 2 VS, 1,779 anusv
    (0x0CAC, 0x0CA6, [0x0CBE, 0x0CC1], []),  # ಬ್ದ — 5,857 occ, 2 VS
    (0x0CB2, 0x0CA6, [0x0CBE], []),  # ಲ್ದ — 5,744 occ, 1 VS
    (0x0CA8, 0x0CB5, [], []),  # ನ್ವ — 5,534 occ, 0 VS
    (0x0CAF, 0x0CA6, [0x0CC1, 0x0CC6], []),  # ಯ್ದ — 5,500 occ, 2 VS
    (0x0CB0, 0x0CB9, [], []),  # ರ್ಹ — 5,439 occ, 0 VS
    (0x0CAA, 0x0C9F, [0x0CBF, 0x0CC6], [0x0C82]),  # ಪ್ಟ — 5,321 occ, 2 VS, 2,079 anusv
    (0x0C9A, 0x0C9B, [], []),  # ಚ್ಛ — 5,283 occ, 0 VS
    (0x0CB2, 0x0CAE, [0x0CBE, 0x0CC8], []),  # ಲ್ಮ — 5,147 occ, 2 VS
    (0x0CB2, 0x0C97, [0x0CCA], [0x0C82]),  # ಲ್ಗ — 4,978 occ, 1 VS, 1,946 anusv
    (0x0CA7, 0x0CB5, [], []),  # ಧ್ವ — 4,925 occ, 0 VS
    (0x0C95, 0x0CB5, [0x0CBE, 0x0CBF], []),  # ಕ್ವ — 4,901 occ, 2 VS
    (0x0CA5, 0x0CAF, [], []),  # ಥ್ಯ — 4,766 occ, 0 VS
    (0x0CAD, 0x0CB0, [], []),  # ಭ್ರ — 4,763 occ, 0 VS
    (0x0CB7, 0x0C95, [0x0CBE], []),  # ಷ್ಕ — 4,604 occ, 1 VS
    (0x0C9F, 0x0CB5, [0x0CBF, 0x0CC0], []),  # ಟ್ವ — 4,539 occ, 2 VS
    (0x0CA1, 0x0CAF, [0x0CBE], []),  # ಡ್ಯ — 4,476 occ, 1 VS
    (0x0CB2, 0x0C9F, [0x0CBF], []),  # ಲ್ಟ — 4,266 occ, 1 VS
    (0x0C97, 0x0CA8, [0x0CBF], []),  # ಗ್ನ — 4,225 occ, 1 VS
    (0x0CB9, 0x0CAE, [], []),  # ಹ್ಮ — 4,093 occ, 0 VS
    (0x0CA7, 0x0CB0, [], []),  # ಧ್ರ — 3,711 occ, 0 VS
    (0x0CB2, 0x0CAC, [], []),  # ಲ್ಬ — 3,472 occ, 0 VS
    (0x0CB0, 0x0C98, [], []),  # ರ್ಘ — 3,442 occ, 0 VS
    (0x0CAE, 0x0CB8, [], []),  # ಮ್ಸ — 3,420 occ, 0 VS
    (0x0CAB, 0x0CB2, [], []),  # ಫ್ಲ — 3,186 occ, 0 VS
    (0x0CB6, 0x0CB2, [0x0CC7], []),  # ಶ್ಲ — 3,180 occ, 1 VS
    (0x0CA1, 0x0CB8, [], []),  # ಡ್ಸ — 3,144 occ, 0 VS
    (0x0CA4, 0x0C95, [0x0CBE], []),  # ತ್ಕ — 3,091 occ, 1 VS
    (0x0CAB, 0x0CAF, [0x0CBE], []),  # ಫ್ಯ — 2,980 occ, 1 VS
    (0x0CB9, 0x0CA8, [0x0CC6], []),  # ಹ್ನ — 2,931 occ, 1 VS
    (0x0CAE, 0x0CB0, [0x0CBE], []),  # ಮ್ರ — 2,874 occ, 1 VS
    (0x0CB6, 0x0CAE, [0x0CC0], []),  # ಶ್ಮ — 2,850 occ, 1 VS
    (0x0CA6, 0x0C98, [0x0CBE], []),  # ದ್ಘ — 2,754 occ, 1 VS
    (0x0CB8, 0x0CAB, [0x0CCB], []),  # ಸ್ಫ — 2,708 occ, 1 VS
    (0x0C97, 0x0CB8, [], []),  # ಗ್ಸ — 2,693 occ, 0 VS
    (0x0CAB, 0x0C9F, [], []),  # ಫ್ಟ — 2,625 occ, 0 VS
    (0x0CA6, 0x0CAD, [0x0CC1], []),  # ದ್ಭ — 2,527 occ, 1 VS
    (0x0C9F, 0x0CA8, [], []),  # ಟ್ನ — 2,513 occ, 0 VS
    (0x0CAE, 0x0CB2, [], []),  # ಮ್ಲ — 2,454 occ, 0 VS
    (0x0CB8, 0x0CB0, [], []),  # ಸ್ರ — 2,419 occ, 0 VS
    (0x0C9F, 0x0CB2, [], []),  # ಟ್ಲ — 2,324 occ, 0 VS
    (0x0C98, 0x0CB0, [], []),  # ಘ್ರ — 2,288 occ, 0 VS
    (0x0CAF, 0x0CA4, [0x0CBF, 0x0CC1], []),  # ಯ್ತ — 2,275 occ, 2 VS
    (0x0CA1, 0x0C95, [], []),  # ಡ್ಕ — 2,255 occ, 0 VS
    (0x0CA1, 0x0CA4, [0x0CBF], []),  # ಡ್ತ — 2,196 occ, 1 VS
    (0x0C9C, 0x0CB5, [], []),  # ಜ್ವ — 2,090 occ, 0 VS
    (0x0CB0, 0x0C96, [0x0CBE], []),  # ರ್ಖ — 2,038 occ, 1 VS
    (0x0CB2, 0x0CA4, [], []),  # ಲ್ತ — 1,975 occ, 0 VS
    (0x0C9F, 0x0C97, [], []),  # ಟ್ಗ — 1,966 occ, 0 VS
    (0x0CB2, 0x0CAB, [], []),  # ಲ್ಫ — 1,922 occ, 0 VS
    (0x0CB0, 0x0CB0, [0x0CBF], []),  # ರ್ರ — 1,896 occ, 1 VS
    (0x0CAA, 0x0CB8, [], []),  # ಪ್ಸ — 1,889 occ, 0 VS
    (0x0CAF, 0x0CA1, [], []),  # ಯ್ಡ — 1,873 occ, 0 VS
    (0x0CB9, 0x0CB2, [0x0CBF], []),  # ಹ್ಲ — 1,871 occ, 1 VS
    (0x0CB9, 0x0CB5, [0x0CBE], []),  # ಹ್ವ — 1,796 occ, 1 VS
    (0x0C9A, 0x0CAF, [], []),  # ಚ್ಯ — 1,679 occ, 0 VS
    (0x0CA8, 0x0C97, [], []),  # ನ್ಗ — 1,674 occ, 0 VS
    (0x0CA0, 0x0CAF, [], []),  # ಠ್ಯ — 1,656 occ, 0 VS
    (0x0CB7, 0x0CAA, [], []),  # ಷ್ಪ — 1,647 occ, 0 VS
    (0x0C95, 0x0CA8, [], []),  # ಕ್ನ — 1,616 occ, 0 VS
    (0x0CA6, 0x0CAE, [], []),  # ದ್ಮ — 1,597 occ, 0 VS
    (0x0CA1, 0x0CB2, [], []),  # ಡ್ಲ — 1,521 occ, 0 VS
    (0x0CA1, 0x0CA8, [], []),  # ಡ್ನ — 1,493 occ, 0 VS
    (0x0CB2, 0x0CA8, [], []),  # ಲ್ನ — 1,488 occ, 0 VS
    (0x0CB3, 0x0CB5, [0x0CBF], []),  # ಳ್ವ — 1,475 occ, 1 VS
    (0x0CA1, 0x0CB5, [], []),  # ಡ್ವ — 1,425 occ, 0 VS
    (0x0CA8, 0x0CB0, [], []),  # ನ್ರ — 1,347 occ, 0 VS
    (0x0CB0, 0x0CAB, [], []),  # ರ್ಫ — 1,313 occ, 0 VS
    (0x0C97, 0x0CB5, [], []),  # ಗ್ವ — 1,311 occ, 0 VS
    (0x0CA1, 0x0C97, [], []),  # ಡ್ಗ — 1,213 occ, 0 VS
    (0x0CAC, 0x0CB8, [], []),  # ಬ್ಸ — 1,178 occ, 0 VS
    (0x0CB8, 0x0C97, [], []),  # ಸ್ಗ — 1,166 occ, 0 VS
    (0x0CB5, 0x0CB5, [], []),  # ವ್ವ — 1,155 occ, 0 VS
    (0x0C9C, 0x0CB0, [], []),  # ಜ್ರ — 1,140 occ, 0 VS
    (0x0CA1, 0x0C9C, [], []),  # ಡ್ಜ — 1,121 occ, 0 VS
    (0x0CAE, 0x0CA8, [], []),  # ಮ್ನ — 1,089 occ, 0 VS
    (0x0CAB, 0x0CA4, [], []),  # ಫ್ತ — 1,041 occ, 0 VS
    (0x0CA8, 0x0CB2, [], []),  # ನ್ಲ — 1,026 occ, 0 VS
    (0x0CB3, 0x0CA4, [], []),  # ಳ್ತ — 948 occ, 0 VS
    (0x0CA8, 0x0CAB, [], []),  # ನ್ಫ — 940 occ, 0 VS
    (0x0CA1, 0x0CAE, [], []),  # ಡ್ಮ — 938 occ, 0 VS
    (0x0C97, 0x0CA4, [], []),  # ಗ್ತ — 933 occ, 0 VS
    (0x0CAF, 0x0CB8, [], []),  # ಯ್ಸ — 928 occ, 0 VS
    (0x0CA5, 0x0CB0, [], []),  # ಥ್ರ — 902 occ, 0 VS
    (0x0C97, 0x0CA6, [], []),  # ಗ್ದ — 880 occ, 0 VS
    (0x0CB3, 0x0CAF, [], []),  # ಳ್ಯ — 880 occ, 0 VS
    (0x0CAF, 0x0CB2, [], []),  # ಯ್ಲ — 876 occ, 0 VS
    (0x0CA3, 0x0CAE, [], []),  # ಣ್ಮ — 876 occ, 0 VS
    (0x0CA6, 0x0C97, [], []),  # ದ್ಗ — 856 occ, 0 VS
]

# Script-native digits: U+0CE6 ೦ … U+0CEF ೯ (KANNADA DIGIT ZERO..NINE)
DIGITS: list[int] = list(range(0x0CE6, 0x0CF0))
