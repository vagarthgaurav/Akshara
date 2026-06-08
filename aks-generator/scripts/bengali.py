"""
Bengali script definition for Akshara cluster enumeration.

Codepoint ranges from Unicode Standard, Bengali block (U+0980–U+09FF).
Rule table values match aks_rule_table_t in the .aks format spec.

Primary target: standard Bengali (বাংলা). Includes extended consonants
ড় (U+09DC), ঢ় (U+09DD), and য় (U+09DF), which are precomposed atomic
codepoints outside the main consonant range. At runtime the MCU segmenter
treats them via the 'otherwise' path — they start a new cluster and still
accept vowel signs and modifiers, which is correct since these letters never
form conjuncts. No rule table extension needed.

ৎ (U+09CE, BENGALI LETTER KHANDA TA) is included as a standalone consonant;
it is a word-final form that does not take vowel signs in standard Bengali.

NOTE: CONJUNCT_PAIRS, CONJUNCT_TRIPLES, and MODIFIER_CLUSTERS below are
derived from Bengali linguistic knowledge and common vocabulary. Corpus
validation against the Indic-script-analysis repo is recommended before
generating a production .aks file.

MAX_CONJUNCT_DEPTH is 2: cp[6] keys support depth-2 triples up to 6 codepoints
(c1+v+c2+v+c3+VS). Bengali has a small number of productive depth-2 triples
(রাষ্ট্র, মন্ত্র, চন্দ্র, স্ত্রী) that are covered here.
"""

SCRIPT_ID: int = 0x06

# ── Rule table values (written verbatim to aks_rule_table_t in .aks header) ──

CONSONANT_RANGE: tuple[int, int] = (0x0995, 0x09B9)  # KA..HA
VIRAMA: int = 0x09CD  # BENGALI SIGN VIRAMA (HASANTA)
VOWEL_SIGN_RANGE: tuple[int, int] = (0x09BE, 0x09CC)  # coarse range for segmenter
MODIFIER_RANGE: tuple[int, int] = (0x0981, 0x0983)  # chandrabindu..visarga
MAX_CONJUNCT_DEPTH: int = 2

# ── Enumerable codepoints (explicit lists; unassigned Unicode slots excluded) ─

# Independent vowels: U+0985–U+0994.
# U+098D, U+098E, U+0991, U+0992 are unassigned.
INDEPENDENT_VOWELS: list[int] = [
    0x0985,  # অ A
    0x0986,  # আ AA
    0x0987,  # ই I
    0x0988,  # ঈ II
    0x0989,  # উ U
    0x098A,  # ঊ UU
    0x098B,  # ঋ VOCALIC R (Sanskrit loans: ঋষি, ঋণ)
    0x098C,  # ঌ VOCALIC L (rare, Sanskrit)
    0x098F,  # এ E
    0x0990,  # ঐ AI
    0x0993,  # ও O
    0x0994,  # ঔ AU
]

# Consonants: U+0995–U+09B9. U+09A9 and U+09B1–U+09B5 are unassigned.
# Extended nukta forms ড় (U+09DC), ঢ় (U+09DD), য় (U+09DF) are precomposed
# atomic codepoints used throughout standard Bengali orthography.
# ৎ (U+09CE, KHANDA TA) is a word-final standalone consonant form.
CONSONANTS: list[int] = [
    *range(0x0995, 0x09A9),  # ক(95)..ন(A8) — 20 consonants  (U+09A9 unassigned)
    *range(0x09AA, 0x09B0),  # প(AA)..র(AF) —  6 consonants
    0x09B0,                  # র RA
    # U+09B1 unassigned
    0x09B2,                  # ল LA
    # U+09B3–U+09B5 unassigned
    0x09B6,  # শ SHA
    0x09B7,  # ষ SSA
    0x09B8,  # স SA
    0x09B9,  # হ HA
    # Extended / precomposed forms
    0x09CE,  # ৎ KHANDA TA — word-final 't' sound (বাৎসল্য); rare in modern prose
    0x09DC,  # ড় RRA (ড + NUKTA precomposed) — বড়, পড়া, বাড়ি — very common
    0x09DD,  # ঢ় RHA (ঢ + NUKTA precomposed) — less common
    0x09DF,  # য় YYA (য + NUKTA precomposed) — যায়, হয়, নয় — very common
]

# Dependent vowel signs.
# U+09C5, U+09C6 are unassigned. U+09C9, U+09CA are unassigned. U+09CD is virama.
VOWEL_SIGNS: list[int] = [
    0x09BE,  # া AA
    0x09BF,  # ি I
    0x09C0,  # ী II
    0x09C1,  # ু U
    0x09C2,  # ূ UU
    0x09C3,  # ৃ VOCALIC R (কৃ, গৃ — Sanskrit loans)
    0x09C4,  # ৄ VOCALIC RR (archaic, near-zero in modern Bengali)
    0x09C7,  # ে E
    0x09C8,  # ৈ AI
    0x09CB,  # ো O  (precomposed; also encoded as U+09C7 U+09BE)
    0x09CC,  # ৌ AU (precomposed; also encoded as U+09C7 U+09D7)
]

MODIFIERS: list[int] = [
    0x0982,  # BENGALI SIGN ANUSVARA (ং) — nasal, ubiquitous: বাংলা, সংখ্যা
    0x0981,  # BENGALI SIGN CHANDRABINDU (ঁ) — nasalised vowel: চাঁদ, বাঁশ
    # 0x0983 VISARGA (ঃ) — Sanskrit loans only; rare in standard Bengali prose
]

# Script-native digits: U+09E6 ০ … U+09EF ৯ (BENGALI DIGIT ZERO..NINE)
DIGITS: list[int] = list(range(0x09E6, 0x09F0))

# High-frequency C + VS + modifier clusters.
# Anusvara = 0x0982, chandrabindu = 0x0981.
# NOTE: frequencies below are estimates pending Bengali corpus validation.
MODIFIER_CLUSTERS: list[tuple[int, list[int], list[int]]] = [
    (0x09AC, [0x09BE, 0x09BF], [0x0982]),  # ব — বাং বিং  (38,725 395)
    (0x09B8, [0x09BE, 0x09BF], [0x0982]),  # স — সাং সিং  (9,586 5,559)
    (0x0995, [0x09BF, 0x09BE], [0x0982]),  # ক — কিং কাং  (6,367 2,047)
    (0x09A4, [0x09BE], [0x0982]),  # ত — তাং  (5,548)
    (0x099F, [0x09BF], [0x0982]),  # ট — টিং  (5,157)
    (0x09AE, [0x09CB, 0x09BE, 0x09BF], [0x0982, 0x0983]),  # ম — মাং মিং মোঃ  (1,521 753 2,848)
    (0x09A8, [0x09BF], [0x0982, 0x0983]),  # ন — নিং নিঃ  (3,724 1,290)
    (0x09B2, [0x09BF], [0x0982]),  # ল — লিং  (3,357)
    (0x09B0, [0x09BF, 0x09BE], [0x0982, 0x0983]),  # র — রিং রাং রাঃ  (1,778 1,149 325)
    (0x09A6, [0x09C1], [0x0983]),  # দ — দুঃ  (2,155)
    (0x09B9, [0x09BF], [0x0982]),  # হ — হিং  (1,418)
    (0x099C, [0x09BF], [0x0982]),  # জ — জিং  (1,332)
    (0x09A1, [0x09BF, 0x09BE], [0x0982, 0x0983]),  # ড — ডিং ডাঃ  (717 392)
    (0x09AA, [0x09BF], [0x0982]),  # প — পিং  (951)
    (0x09B6, [0x09BF], [0x0982]),  # শ — শিং  (831)
    (0x099A, [0x09BF], [0x0982]),  # চ — চিং  (767)
    (0x09AB, [0x09BF], [0x0982]),  # ফ — ফিং  (314)
    (0x09AD, [0x09BE], [0x0982]),  # ভ — ভাং  (311)
    (0x0997, [0x09BF], [0x0982]),  # গ — গিং  (310)
]

# Attested conjunct pairs to precompute.
# Format: (c1, c2, vowel_signs, modifiers). Cluster = c1 + virama + c2.
# Bare conjunct (no VS, no modifier) always included.
# NOTE: frequencies are estimates pending Bengali corpus validation.
CONJUNCT_PAIRS: list[tuple[int, int, list[int], list[int]]] = [
    (0x09AA, 0x09B0, [0x09BE, 0x09BF, 0x09C0, 0x09C7, 0x09CB], []),  # প্র — 317,010 occ, 5 VS
    (0x09A8, 0x09A4, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7, 0x09CB], [0x0983]),  # ন্ত — 157,554 occ, 6 VS, 668 visarg
    (0x0995, 0x09B7, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7, 0x09CB], []),  # ক্ষ — 154,025 occ, 6 VS
    (0x09A4, 0x09B0, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7, 0x09CB], []),  # ত্র — 135,450 occ, 6 VS
    (0x09AC, 0x09AF, [0x09BE, 0x09C1, 0x09C7], [0x0982]),  # ব্য — 98,005 occ, 3 VS, 5,815 anusv
    (0x09A8, 0x09AF, [0x09BE, 0x09C1, 0x09C2, 0x09C7], []),  # ন্য — 96,421 occ, 4 VS
    (0x09B8, 0x09A5, [0x09BE, 0x09BF], []),  # স্থ — 90,893 occ, 2 VS
    (0x0995, 0x09A4, [0x09BE, 0x09BF, 0x09C3, 0x09C7], []),  # ক্ত — 82,427 occ, 4 VS
    (0x0999, 0x0997, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7, 0x09CB], []),  # ঙ্গ — 73,843 occ, 6 VS
    (0x09A7, 0x09AF, [0x09BE, 0x09C7], []),  # ধ্য — 72,860 occ, 2 VS
    (0x0997, 0x09B0, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7], []),  # গ্র — 71,066 occ, 5 VS
    (0x09A8, 0x09A6, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7, 0x09CB], []),  # ন্দ — 70,629 occ, 6 VS
    (0x09B8, 0x09A4, [0x09BE, 0x09BF, 0x09C1, 0x09C3, 0x09C7, 0x09CB], []),  # স্ত — 68,535 occ, 6 VS
    (0x0995, 0x09B0, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7, 0x09CB], []),  # ক্র — 62,505 occ, 6 VS
    (0x09B7, 0x099F, [0x09BE, 0x09BF, 0x09C7], []),  # ষ্ট — 58,541 occ, 3 VS
    (0x09B8, 0x099F, [0x09BE, 0x09BF, 0x09C1, 0x09C7, 0x09CB], [0x0982]),  # স্ট — 56,965 occ, 5 VS, 507 anusv
    (0x09B0, 0x09AE, [0x09BE, 0x09BF, 0x09C0, 0x09C2, 0x09C7], []),  # র্ম — 53,893 occ, 5 VS
    (0x09B0, 0x09A4, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C3, 0x09C7], []),  # র্ত — 53,799 occ, 6 VS
    (0x09A6, 0x09A7, [0x09BE, 0x09BF, 0x09C3, 0x09C7], []),  # দ্ধ — 53,444 occ, 4 VS
    (0x099A, 0x099B, [0x09BE, 0x09BF, 0x09C1, 0x09C7], []),  # চ্ছ — 52,967 occ, 4 VS
    (0x09AE, 0x09AA, [0x09BE, 0x09BF, 0x09C2, 0x09C3, 0x09C7], []),  # ম্প — 52,647 occ, 5 VS
    (0x09B0, 0x09AF, [0x09BE, 0x09C7, 0x09CB], []),  # র্য — 51,044 occ, 3 VS
    (0x09B8, 0x09AC, [0x09BE, 0x09C0, 0x09C7], []),  # স্ব — 50,918 occ, 3 VS
    (0x09B0, 0x09AC, [0x09BE, 0x09BF, 0x09C3, 0x09C7, 0x09CB], []),  # র্ব — 50,551 occ, 5 VS
    (0x09A4, 0x09AF, [0x09BE, 0x09BF, 0x09C1, 0x09C7], []),  # ত্য — 46,889 occ, 4 VS
    (0x09B0, 0x09A5, [0x09BE, 0x09BF, 0x09C0, 0x09C7], []),  # র্থ — 45,939 occ, 4 VS
    (0x099F, 0x09B0, [0x09BE, 0x09BF, 0x09C0, 0x09C7, 0x09CB], []),  # ট্র — 43,381 occ, 5 VS
    (0x09A8, 0x099F, [0x09BE, 0x09BF, 0x09C1, 0x09C7], []),  # ন্ট — 42,103 occ, 4 VS
    (0x09A8, 0x09A8, [0x09BE, 0x09BF, 0x09C0, 0x09C7], []),  # ন্ন — 41,250 occ, 4 VS
    (0x09A4, 0x09A4, [0x09BE, 0x09BF, 0x09C0, 0x09C7, 0x09CB], []),  # ত্ত — 39,126 occ, 5 VS
    (0x09A8, 0x09A1, [0x09BE, 0x09BF, 0x09C1, 0x09C7, 0x09CB], [0x0982]),  # ন্ড — 37,564 occ, 5 VS, 379 anusv
    (0x09B6, 0x09AC, [0x09BE, 0x09BF, 0x09C7], []),  # শ্ব — 37,243 occ, 3 VS
    (0x09A6, 0x09B0, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7, 0x09CB], []),  # দ্র — 36,171 occ, 6 VS
    (0x09B7, 0x09A0, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7], []),  # ষ্ঠ — 35,126 occ, 5 VS
    (0x09A8, 0x09A7, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7], []),  # ন্ধ — 34,252 occ, 5 VS
    (0x09A6, 0x09AF, [0x09BE, 0x09C1, 0x09C7, 0x09CB], []),  # দ্য — 34,046 occ, 4 VS
    (0x09A4, 0x09AC, [0x09BE, 0x09BF, 0x09C7], []),  # ত্ব — 32,613 occ, 3 VS
    (0x09AE, 0x09AC, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7, 0x09CB], []),  # ম্ব — 31,061 occ, 6 VS
    (0x09AE, 0x09AF, [0x09BE], []),  # ম্য — 30,914 occ, 1 VS
    (0x09B2, 0x09B2, [0x09BE, 0x09BF, 0x09C0, 0x09C7], []),  # ল্ল — 30,721 occ, 4 VS
    (0x09B8, 0x0995, [0x09BE, 0x09BF, 0x09C1, 0x09C3, 0x09C7, 0x09CB], []),  # স্ক — 30,364 occ, 6 VS
    (0x09B8, 0x09AF, [0x09BE, 0x09C1, 0x09C7], []),  # স্য — 27,994 occ, 3 VS
    (0x09B0, 0x0995, [0x09BE, 0x09BF, 0x09C7], [0x0982]),  # র্ক — 27,422 occ, 3 VS, 309 anusv
    (0x09AA, 0x09A4, [0x09BE, 0x09BF], []),  # প্ত — 26,404 occ, 2 VS
    (0x09B2, 0x09AA, [0x09BF, 0x09C0, 0x09C7], []),  # ল্প — 23,859 occ, 3 VS
    (0x09B6, 0x09B0, [0x09BE, 0x09C0, 0x09C1, 0x09C7], []),  # শ্র — 23,224 occ, 4 VS
    (0x09A6, 0x09AC, [0x09BE, 0x09BF, 0x09C0, 0x09C7, 0x09CB], []),  # দ্ব — 23,132 occ, 5 VS
    (0x099E, 0x099C, [0x09BE, 0x09BF, 0x09C1, 0x09C7], []),  # ঞ্জ — 22,984 occ, 4 VS
    (0x09B2, 0x09AF, [0x09BE, 0x09C7], []),  # ল্য — 22,256 occ, 2 VS
    (0x09AC, 0x09B0, [0x09BE, 0x09BF, 0x09C1, 0x09C7, 0x09CB], []),  # ব্র — 21,939 occ, 5 VS
    (0x099C, 0x099E, [0x09BE, 0x09C7], []),  # জ্ঞ — 21,392 occ, 2 VS
    (0x09A5, 0x09AF, [0x09BE, 0x09C7], []),  # থ্য — 21,169 occ, 2 VS
    (0x09B0, 0x099F, [0x09BE, 0x09BF, 0x09C7], []),  # র্ট — 20,994 occ, 3 VS
    (0x0995, 0x09AF, [0x09BE, 0x09C7], []),  # ক্য — 20,410 occ, 2 VS
    (0x0996, 0x09AF, [0x09BE], []),  # খ্য — 20,312 occ, 1 VS
    (0x09B0, 0x09A3, [0x09BE, 0x09BF, 0x09C7], []),  # র্ণ — 19,507 occ, 3 VS
    (0x09B0, 0x099C, [0x09BE, 0x09BF, 0x09C1, 0x09C7], []),  # র্জ — 19,141 occ, 4 VS
    (0x09A8, 0x09B8, [0x09BE, 0x09BF, 0x09C0, 0x09C7], []),  # ন্স — 18,971 occ, 4 VS
    (0x09AE, 0x09AE, [0x09BE, 0x09BF, 0x09C1, 0x09C7], []),  # ম্ম — 18,533 occ, 4 VS
    (0x09B0, 0x09A1, [0x09BE, 0x09BF, 0x09C7], []),  # র্ড — 18,501 occ, 3 VS
    (0x099E, 0x099A, [0x09BE, 0x09BF, 0x09C1, 0x09C7], []),  # ঞ্চ — 18,148 occ, 4 VS
    (0x09B0, 0x09B7, [0x09BE, 0x09BF, 0x09C7], []),  # র্ষ — 16,895 occ, 3 VS
    (0x0995, 0x09B8, [0x09BE, 0x09BF, 0x09C7], []),  # ক্স — 16,735 occ, 3 VS
    (0x099A, 0x099A, [0x09BE, 0x09BF, 0x09C1], []),  # চ্চ — 16,080 occ, 3 VS
    (0x09A6, 0x09A6, [0x09BE, 0x09BF, 0x09C0, 0x09C1, 0x09C7], []),  # দ্দ — 16,069 occ, 5 VS
    (0x09B0, 0x09B6, [0x09BE, 0x09BF, 0x09C0, 0x09C7], []),  # র্শ — 15,952 occ, 4 VS
    (0x09B8, 0x09AA, [0x09BE, 0x09BF, 0x09C7, 0x09CB], []),  # স্প — 15,542 occ, 4 VS
    (0x099C, 0x09AF, [0x09BE, 0x09BF, 0x09C7, 0x09CB], []),  # জ্য — 15,527 occ, 4 VS
    (0x09B0, 0x09A6, [0x09BE, 0x09BF, 0x09C0, 0x09C7], []),  # র্দ — 14,156 occ, 4 VS
    (0x09B6, 0x09AF, [0x09BE, 0x09C1, 0x09C7], []),  # শ্য — 14,026 occ, 3 VS
    (0x09B6, 0x099A, [0x09BE, 0x09BF], []),  # শ্চ — 13,478 occ, 2 VS
    (0x09B0, 0x09B8, [0x09BE, 0x09BF, 0x09C7], [0x0982]),  # র্স — 12,830 occ, 3 VS, 364 anusv
    (0x0999, 0x0995, [0x09BE, 0x09BF, 0x09C1, 0x09C7], []),  # ঙ্ক — 12,574 occ, 4 VS
    (0x09AC, 0x09A6, [0x09C0, 0x09C1, 0x09C7], []),  # ব্দ — 11,822 occ, 3 VS
    (0x0995, 0x099F, [0x09BF, 0x09C7, 0x09CB], []),  # ক্ট — 11,223 occ, 3 VS
    (0x09B0, 0x09A8, [0x09BE, 0x09BF, 0x09C0, 0x09C7], [0x0982]),  # র্ন — 11,127 occ, 4 VS, 588 anusv
    (0x0995, 0x09B2, [0x09BE, 0x09BF, 0x09CB], []),  # ক্ল — 11,019 occ, 3 VS
    (0x09A3, 0x09A1, [0x09BE, 0x09BF, 0x09C7], []),  # ণ্ড — 10,990 occ, 3 VS
    (0x0997, 0x09AF, [0x09BE, 0x09C7], []),  # গ্য — 10,222 occ, 2 VS
    (0x09AE, 0x09AD, [0x09BE, 0x09BF], []),  # ম্ভ — 10,194 occ, 2 VS
    (0x09AA, 0x09B2, [0x09BE, 0x09BF, 0x09C7, 0x09CB], []),  # প্ল — 10,135 occ, 4 VS
    (0x09B0, 0x09AD, [0x09BE, 0x09BF, 0x09C1, 0x09C2, 0x09C7, 0x09CB], []),  # র্ভ — 9,860 occ, 6 VS
    (0x09A8, 0x09AE, [0x09BE, 0x09C1, 0x09C7, 0x09CB], []),  # ন্ম — 9,723 occ, 4 VS
    (0x09B0, 0x099A, [0x09BE, 0x09C1, 0x09C7], []),  # র্চ — 9,599 occ, 3 VS
    (0x09B7, 0x09AF, [0x09C7], []),  # ষ্য — 8,972 occ, 1 VS
    (0x09B0, 0x09A7, [0x09BE, 0x09BF, 0x09C7], []),  # র্ধ — 8,778 occ, 3 VS
    (0x09B0, 0x0998, [], []),  # র্ঘ — 8,528 occ, 0 VS
    (0x09AB, 0x09B0, [0x09BE, 0x09BF, 0x09C7], []),  # ফ্র — 8,455 occ, 3 VS
    (0x099F, 0x099F, [0x09BE, 0x09BF, 0x09CB], []),  # ট্ট — 8,314 occ, 3 VS
    (0x099C, 0x099C, [0x09BE, 0x09BF, 0x09C0], []),  # জ্জ — 8,229 occ, 3 VS
    (0x09AD, 0x09AF, [0x09BE, 0x09C1], []),  # ভ্য — 8,185 occ, 2 VS
    (0x09B0, 0x0997, [0x09BE, 0x09C7], []),  # র্গ — 7,958 occ, 2 VS
    (0x09A4, 0x09AE, [0x09BE, 0x09C0], []),  # ত্ম — 7,805 occ, 2 VS
    (0x099A, 0x09AF, [0x09BE, 0x09C1, 0x09C7], []),  # চ্য — 7,556 occ, 3 VS
    (0x09B6, 0x09A8, [0x09C7], []),  # শ্ন — 7,265 occ, 1 VS
    (0x09B8, 0x09AE, [0x09BE, 0x09BF, 0x09C3], []),  # স্ম — 7,229 occ, 3 VS
    (0x099F, 0x09AF, [0x09BE, 0x09C1], []),  # ট্য — 7,226 occ, 2 VS
    (0x09AC, 0x09B2, [0x09BE, 0x09BF, 0x09C1], []),  # ব্ল — 7,117 occ, 3 VS
    (0x09AA, 0x09AF, [0x09BE], []),  # প্য — 6,950 occ, 1 VS
    (0x09B9, 0x09AF, [0x09BE], []),  # হ্য — 6,752 occ, 1 VS
    (0x09AA, 0x099F, [0x09BE, 0x09C7], []),  # প্ট — 6,186 occ, 2 VS
    (0x09B2, 0x099F, [0x09BE, 0x09BF, 0x09C7, 0x09CB], []),  # ল্ট — 5,578 occ, 4 VS
    (0x09A1, 0x09B0, [0x09BE, 0x09BF, 0x09C7, 0x09CB], []),  # ড্র — 5,215 occ, 4 VS
    (0x09A3, 0x09AF, [0x09C7], []),  # ণ্য — 5,185 occ, 1 VS
    (0x09B7, 0x0995, [0x09BE, 0x09C3, 0x09C7], []),  # ষ্ক — 5,048 occ, 3 VS
    (0x09B2, 0x09A1, [0x09BE, 0x09BF, 0x09C7], [0x0982]),  # ল্ড — 5,034 occ, 3 VS, 626 anusv
    (0x09B6, 0x09B2, [0x09BF, 0x09C0, 0x09C7], []),  # শ্ল — 4,733 occ, 3 VS
    (0x09AF, 0x09AF, [0x09BE, 0x09C7], []),  # য্য — 4,677 occ, 2 VS
    (0x099C, 0x09AC, [0x09BE], []),  # জ্ব — 4,619 occ, 1 VS
    (0x09A3, 0x099F, [0x09BE], []),  # ণ্ট — 4,519 occ, 1 VS
    (0x0995, 0x0995, [0x09BE], []),  # ক্ক — 4,243 occ, 1 VS
    (0x09A7, 0x09AC, [], [0x0982]),  # ধ্ব — 4,107 occ, 0 VS, 1,637 anusv
    (0x09AD, 0x09B0, [0x09BE], []),  # ভ্র — 3,947 occ, 1 VS
    (0x0997, 0x09A8, [0x09BF, 0x09C7], []),  # গ্ন — 3,929 occ, 2 VS
    (0x09A8, 0x09A5, [0x09BE, 0x09C0, 0x09C7], []),  # ন্থ — 3,590 occ, 3 VS
    (0x09AC, 0x09AC, [0x09BE, 0x09BF, 0x09C1], []),  # ব্ব — 3,588 occ, 3 VS
    (0x09AB, 0x09B2, [0x09BE, 0x09CB], []),  # ফ্ল — 3,251 occ, 2 VS
    (0x09B9, 0x09AC, [0x09BE], []),  # হ্ব — 3,074 occ, 1 VS
    (0x09AA, 0x09A8, [0x09C7], []),  # প্ন — 2,962 occ, 1 VS
    (0x09B0, 0x09AA, [0x09CB], []),  # র্প — 2,874 occ, 1 VS
    (0x0996, 0x09B0, [0x09BF], []),  # খ্র — 2,861 occ, 1 VS
    (0x09B0, 0x09B2, [0x09BE, 0x09BF], []),  # র্ল — 2,803 occ, 2 VS
    (0x09B9, 0x09A8, [0x09BF], []),  # হ্ন — 2,680 occ, 1 VS
    (0x09B7, 0x09A3, [0x09BE, 0x09C1], []),  # ষ্ণ — 2,512 occ, 2 VS
    (0x09A6, 0x09AD, [0x09BE, 0x09BF, 0x09C1, 0x09C2], []),  # দ্ভ — 2,491 occ, 4 VS
    (0x09AB, 0x09AF, [0x09BE], []),  # ফ্য — 2,478 occ, 1 VS
    (0x09A8, 0x09AC, [0x09BF], []),  # ন্ব — 2,414 occ, 1 VS
    (0x09AE, 0x09A8, [], []),  # ম্ন — 2,325 occ, 0 VS
    (0x09B8, 0x09A8, [0x09BE], []),  # স্ন — 2,280 occ, 1 VS
    (0x0999, 0x0996, [], []),  # ঙ্খ — 2,259 occ, 0 VS
    (0x09B8, 0x09AB, [0x09CB], []),  # স্ফ — 1,900 occ, 1 VS
    (0x09B7, 0x09AE, [0x09C0], []),  # ষ্ম — 1,866 occ, 1 VS
    (0x09B6, 0x09AE, [0x09C0], []),  # শ্ম — 1,821 occ, 1 VS
    (0x0997, 0x09B2, [0x09BE, 0x09CB], []),  # গ্ল — 1,756 occ, 2 VS
    (0x09A3, 0x09A0, [0x09C7], []),  # ণ্ঠ — 1,746 occ, 1 VS
    (0x09A4, 0x09A8, [], []),  # ত্ন — 1,723 occ, 0 VS
    (0x09B8, 0x09B0, [0x09BE, 0x09CB], []),  # স্র — 1,721 occ, 2 VS
    (0x09B8, 0x09B2, [0x09CB], []),  # স্ল — 1,636 occ, 1 VS
    (0x09A6, 0x09AE, [0x09BE], []),  # দ্ম — 1,607 occ, 1 VS
    (0x0997, 0x09AE, [], []),  # গ্ম — 1,532 occ, 0 VS
    (0x09B9, 0x09AE, [], []),  # হ্ম — 1,514 occ, 0 VS
    (0x09AE, 0x09B0, [0x09BE], []),  # ম্র — 1,503 occ, 1 VS
    (0x09AC, 0x09A7, [0x09BF], []),  # ব্ধ — 1,403 occ, 1 VS
    (0x09A1, 0x09A1, [0x09BE], []),  # ড্ড — 1,338 occ, 1 VS
    (0x09A4, 0x09A5, [0x09BE], []),  # ত্থ — 1,207 occ, 1 VS
    (0x0997, 0x09A7, [], []),  # গ্ধ — 1,143 occ, 0 VS
    (0x09B7, 0x09AA, [], []),  # ষ্প — 1,122 occ, 0 VS
    (0x09AA, 0x09AA, [], []),  # প্প — 1,030 occ, 0 VS
    (0x09B9, 0x09B0, [0x09BE], []),  # হ্র — 985 occ, 1 VS
    (0x09B2, 0x09AE, [], []),  # ল্ম — 960 occ, 0 VS
    (0x09B2, 0x0995, [], []),  # ল্ক — 930 occ, 0 VS
    (0x09A5, 0x09B0, [0x09BF], []),  # থ্র — 878 occ, 1 VS
    (0x09A1, 0x09AF, [0x09BE], []),  # ড্য — 846 occ, 1 VS
    (0x0999, 0x0998, [], []),  # ঙ্ঘ — 813 occ, 0 VS
    (0x0998, 0x09AF, [], []),  # ঘ্য — 756 occ, 0 VS
    (0x09A4, 0x09B8, [0x09BE], []),  # ত্স — 756 occ, 1 VS
    (0x09A0, 0x09AF, [], []),  # ঠ্য — 604 occ, 0 VS
    (0x0998, 0x09B0, [], []),  # ঘ্র — 566 occ, 0 VS
    (0x09B9, 0x09A3, [], []),  # হ্ণ — 553 occ, 0 VS
    (0x09A7, 0x09B0, [], []),  # ধ্র — 509 occ, 0 VS
    (0x09A8, 0x09A0, [], []),  # ন্ঠ — 457 occ, 0 VS
    (0x099B, 0x09AC, [], []),  # ছ্ব — 440 occ, 0 VS
    (0x0998, 0x09A8, [], []),  # ঘ্ন — 401 occ, 0 VS
    (0x09A4, 0x09AA, [], []),  # ত্প — 372 occ, 0 VS
    (0x099C, 0x09B0, [], []),  # জ্র — 367 occ, 0 VS
    (0x0995, 0x09AC, [], []),  # ক্ব — 365 occ, 0 VS
    (0x09B8, 0x09B9, [], []),  # স্হ — 351 occ, 0 VS
    (0x099E, 0x099B, [], []),  # ঞ্ছ — 342 occ, 0 VS
]

# Depth-2 conjunct triples (three consonants, two hasantas).
# Format: (c1, c2, c3, vowel_signs, modifiers).
# Cluster = c1 + virama + c2 + virama + c3 [+ vs] — 5 or 6 codepoints.
# NOTE: frequencies are estimates pending Bengali corpus validation.
CONJUNCT_TRIPLES: list[tuple[int, int, int, list[int], list[int]]] = [
    (0x09A8, 0x09A4, 0x09B0, [0x09C0, 0x09BF, 0x09BE, 0x09C7], []),  # ন্ত্র — 43263 occ
    (0x09A8, 0x09A6, 0x09B0, [0x09C0, 0x09C7, 0x09BF, 0x09BE], []),  # ন্দ্র — 19440 occ
    (0x09B7, 0x099F, 0x09B0, [0x09C7, 0x09C0], []),  # ষ্ট্র — 14375 occ
    (0x09B8, 0x09A4, 0x09B0, [0x09C0, 0x09C7, 0x09CB], []),  # স্ত্র — 10082 occ
    (0x09B8, 0x09A5, 0x09AF, [0x09C7], []),  # স্থ্য — 9062 occ
    (0x09B8, 0x099F, 0x09B0, [0x09C7, 0x09BF, 0x09BE, 0x09CB], []),  # স্ট্র — 8198 occ
    (0x09AE, 0x09AA, 0x09B0, [], []),  # ম্প্র — 7225 occ
    (0x0995, 0x09B7, 0x09AF, [0x09C7], []),  # ক্ষ্য — 5951 occ
    (0x09A4, 0x09A4, 0x09AC, [0x09C7, 0x09BE, 0x09BF], []),  # ত্ত্ব — 3622 occ
    (0x09A8, 0x09A7, 0x09AF, [0x09BE], []),  # ন্ধ্য — 3367 occ
    (0x09A8, 0x09A6, 0x09AF, [0x09CB], []),  # ন্দ্য — 1838 occ
    (0x09B8, 0x099F, 0x09AF, [0x09BE], []),  # স্ট্য — 1782 occ
    (0x09B0, 0x09A7, 0x09AC, [], []),  # র্ধ্ব — 1560 occ
    (0x09A8, 0x09A6, 0x09AC, [0x09C0, 0x09BF], []),  # ন্দ্ব — 1556 occ
    (0x09A8, 0x099F, 0x09B0, [0x09CB, 0x09BE, 0x09BF], []),  # ন্ট্র — 1412 occ
    (0x09B8, 0x0995, 0x09B0, [0x09BF], []),  # স্ক্র — 1333 occ
    (0x09AA, 0x09B2, 0x09AF, [0x09BE], []),  # প্ল্য — 1320 occ
    (0x0995, 0x09B7, 0x09AE, [0x09C0], []),  # ক্ষ্ম — 1214 occ
    (0x09AC, 0x09B0, 0x09AF, [0x09BE], []),  # ব্র্য — 1124 occ
    (0x099C, 0x099C, 0x09AC, [], []),  # জ্জ্ব — 1004 occ
    (0x09B7, 0x099F, 0x09AF, [], []),  # ষ্ট্য — 955 occ
    (0x09B0, 0x09B6, 0x09AC, [], []),  # র্শ্ব — 881 occ
    (0x09A8, 0x09A1, 0x09B0, [], []),  # ন্ড্র — 746 occ
    (0x09B0, 0x09B2, 0x09A1, [], []),  # র্ল্ড — 718 occ
    (0x099F, 0x09B0, 0x09AF, [0x09BE], []),  # ট্র্য — 714 occ
    (0x09B0, 0x0998, 0x09AF, [], []),  # র্ঘ্য — 705 occ
    (0x09AB, 0x09B2, 0x09AF, [0x09BE], []),  # ফ্ল্য — 690 occ
    (0x09B8, 0x09AA, 0x09AF, [0x09BE], []),  # স্প্য — 666 occ
    (0x09AC, 0x09B2, 0x09AF, [0x09BE], []),  # ব্ল্য — 547 occ
    (0x0999, 0x0995, 0x09B7, [], []),  # ঙ্ক্ষ — 540 occ
    (0x0997, 0x09B0, 0x09AF, [0x09BE], []),  # গ্র্য — 527 occ
    (0x09B0, 0x09AF, 0x09AF, [], []),  # র্য্য — 515 occ
    (0x099A, 0x099B, 0x09AC, [], []),  # চ্ছ্ব — 440 occ
    (0x0995, 0x09B0, 0x09AF, [0x09BE], []),  # ক্র্য — 431 occ
    (0x09A4, 0x09B0, 0x09AF, [], []),  # ত্র্য — 408 occ
    (0x09A6, 0x09B0, 0x09AF, [], []),  # দ্র্য — 358 occ
    (0x09B0, 0x09B8, 0x099F, [], []),  # র্স্ট — 358 occ
    (0x09B8, 0x09AA, 0x09B0, [], []),  # স্প্র — 350 occ
    (0x09B0, 0x09A5, 0x09AF, [], []),  # র্থ্য — 347 occ
    (0x09B8, 0x0995, 0x09AF, [0x09BE], []),  # স্ক্য — 344 occ
    (0x09B0, 0x099C, 0x09AF, [], []),  # র্জ্য — 340 occ
    (0x0995, 0x099F, 0x09B0, [], []),  # ক্ট্র — 316 occ
]
