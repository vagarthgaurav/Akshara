"""
Tamil script definition for Akshara cluster enumeration.

Codepoint ranges from Unicode Standard, Tamil block (U+0B80–U+0BFF).
Rule table values match aks_rule_table_t in the .aks format spec.
"""

SCRIPT_ID: int = 0x02

# ── Rule table values (written verbatim to aks_rule_table_t in .aks header) ──

CONSONANT_RANGE: tuple[int, int] = (0x0B95, 0x0BB9)  # KA..HA
VIRAMA: int = 0x0BCD  # TAMIL SIGN VIRAMA (PULLI)
VOWEL_SIGN_RANGE: tuple[int, int] = (0x0BBE, 0x0BCC)  # coarse range for segmenter
MODIFIER_RANGE: tuple[int, int] = (0x0B82, 0x0B83)  # anusvara..aytham
MAX_CONJUNCT_DEPTH: int = 1

# ── Enumerable codepoints (explicit lists; unassigned Unicode slots excluded) ─

# Independent vowels: U+0B85–U+0B94 (several slots unassigned)
INDEPENDENT_VOWELS: list[int] = [
    0x0B85,  # அ A
    0x0B86,  # ஆ AA
    0x0B87,  # இ I
    0x0B88,  # ஈ II
    0x0B89,  # உ U
    0x0B8A,  # ஊ UU
    # 0x0B8B–0x0B8D unassigned
    0x0B8E,  # எ E
    0x0B8F,  # ஏ EE
    0x0B90,  # ஐ AI
    # 0x0B91 unassigned
    0x0B92,  # ஒ O
    0x0B93,  # ஓ OO
    0x0B94,  # ஔ AU
]

# Consonants: U+0B95–U+0BB9 — Tamil block has many unassigned slots in this range.
# Native Tamil consonants: 18 (KA group of 3 + 3 more groups) + SHA, SSA, SA, HA grantha.
CONSONANTS: list[int] = [
    0x0B95,  # க KA
    # 0x0B96–0x0B98 unassigned
    0x0B99,  # ங NGA
    0x0B9A,  # ச CA
    # 0x0B9B unassigned
    0x0B9C,  # ஜ JA (grantha, loanwords)
    # 0x0B9D unassigned
    0x0B9E,  # ஞ NYA
    0x0B9F,  # ட TTA
    # 0x0BA0–0x0BA2 unassigned
    0x0BA3,  # ண NNA
    0x0BA4,  # த TA
    # 0x0BA5–0x0BA7 unassigned
    0x0BA8,  # ந NA
    0x0BA9,  # ன NA (final/uyirmei variant)
    0x0BAA,  # ப PA
    # 0x0BAB–0x0BAD unassigned
    0x0BAE,  # ம MA
    0x0BAF,  # ய YA
    0x0BB0,  # ர RA
    0x0BB1,  # ற RRA
    0x0BB2,  # ல LA
    0x0BB3,  # ள LLA
    0x0BB4,  # ழ LLLA
    0x0BB5,  # வ VA
    0x0BB6,  # ஶ SHA (grantha, rare)
    0x0BB7,  # ஷ SSA (grantha)
    0x0BB8,  # ஸ SA (grantha)
    0x0BB9,  # ஹ HA (grantha)
]

# Dependent vowel signs — two non-contiguous sub-ranges; virama U+0BCD excluded.
VOWEL_SIGNS: list[int] = [
    *range(0x0BBE, 0x0BC3),  # ா ி ீ ு ூ   (AA..UU; 0x0BC3–0x0BC5 unassigned)
    *range(0x0BC6, 0x0BC9),  # ெ ே ை        (E..AI; 0x0BC9 unassigned)
    *range(0x0BCA, 0x0BCD),  # ொ ோ ௌ        (O..AU; 0x0BCD is virama, excluded)
]

MODIFIERS: list[int] = [
    0x0B82,  # TAMIL SIGN ANUSVARA (ஂ) — appears in Sanskrit loanwords
    # 0x0B83 AYTHAM (ஃ) omitted — standalone character, not an akshara modifier
]

MODIFIER_CLUSTERS: list[tuple[int, list[int], list[int]]] = []

# All VS forms precomputed for every conjunct — Tamil cluster space is small enough
# (~50 pairs × 11 VS = ~550 entries) that exhaustive VS coverage is practical.
_VS = [0x0BBE, 0x0BBF, 0x0BC0, 0x0BC1, 0x0BC2, 0x0BC6, 0x0BC7, 0x0BC8, 0x0BCA, 0x0BCB]

# Valid Tamil consonant clusters from Tamil phonology (Wikipedia / Tolkāppiyam):
#   C:  — geminates (any consonant doubled)
#   NP  — nasal + homorganic plosive
#   ṭP  — retroflex stop (ட்) + plosive
#   RP  — liquid/approximant (ர்,ல்,ள்,ற்,ன்) + plosive or consonant
#   grantha — loanword clusters involving SSA, SA, SHA
CONJUNCT_PAIRS: list[tuple[int, int, list[int], list[int]]] = [

    # ── Geminates (C:) ────────────────────────────────────────────────────────
    (0x0B95, 0x0B95, _VS, []),  # க்க  KA+KA    — வணக்கம், தக்கது
    (0x0B9A, 0x0B9A, _VS, []),  # ச்ச  CA+CA    — அச்சம், எச்சம்
    (0x0B9F, 0x0B9F, _VS, []),  # ட்ட  TTA+TTA  — நாட்டு, கேட்டு
    (0x0BA4, 0x0BA4, _VS, []),  # த்த  TA+TA    — எழுத்து, புத்தகம்
    (0x0BAA, 0x0BAA, _VS, []),  # ப்ப  PA+PA    — அப்பா, இப்போது
    (0x0BA3, 0x0BA3, _VS, []),  # ண்ண  NNA+NNA  — கண்ணன், திண்ணை
    (0x0BA9, 0x0BA9, _VS, []),  # ன்ன  ṉ+ṉ     — சென்னை, மன்னன்
    (0x0BB2, 0x0BB2, _VS, []),  # ல்ல  LA+LA    — எல்லாம், பல்லு
    (0x0BB3, 0x0BB3, _VS, []),  # ள்ள  LLA+LLA  — வெள்ளி, பள்ளி
    (0x0BB1, 0x0BB1, _VS, []),  # ற்ற  RRA+RRA  — யாவற்றும், பெற்று

    # ── NP: nasal + homorganic plosive ────────────────────────────────────────
    (0x0B99, 0x0B95, _VS, []),  # ங்க  NGA+KA   — தங்கம், சங்கம்
    (0x0B9E, 0x0B9A, _VS, []),  # ஞ்ச  NYA+CA   — அஞ்சு, நஞ்சு
    (0x0BA3, 0x0B9F, _VS, []),  # ண்ட  NNA+TTA  — கண்டம், தண்டு
    (0x0BA8, 0x0BA4, _VS, []),  # ந்த  NA+TA    — இந்தியா, அந்த
    (0x0BAE, 0x0BAA, _VS, []),  # ம்ப  MA+PA    — கம்பம், வம்பு

    # ── ṭP: retroflex stop + plosive ──────────────────────────────────────────
    (0x0B9F, 0x0B95, _VS, []),  # ட்க  TTA+KA   — நாட்கள்
    (0x0B9F, 0x0BAA, _VS, []),  # ட்ப  TTA+PA   — நுட்பம்

    # ── RP: ர் (RA) + consonant ───────────────────────────────────────────────
    (0x0BB0, 0x0B95, _VS, []),  # ர்க  RA+KA    — அர்க்கம்
    (0x0BB0, 0x0B9A, _VS, []),  # ர்ச  RA+CA
    (0x0BB0, 0x0B9F, _VS, []),  # ர்ட  RA+TTA
    (0x0BB0, 0x0BA4, _VS, []),  # ர்த  RA+TA    — அர்த்தம்
    (0x0BB0, 0x0BAA, _VS, []),  # ர்ப  RA+PA
    (0x0BB0, 0x0BAE, _VS, []),  # ர்ம  RA+MA    — தர்மம்
    (0x0BB0, 0x0BB5, _VS, []),  # ர்வ  RA+VA    — கர்வம்

    # ── RP: ல் (LA) + consonant ───────────────────────────────────────────────
    (0x0BB2, 0x0B95, _VS, []),  # ல்க  LA+KA    — செயல்கள்
    (0x0BB2, 0x0B9F, _VS, []),  # ல்ட  LA+TTA
    (0x0BB2, 0x0BA4, _VS, []),  # ல்த  LA+TA
    (0x0BB2, 0x0BAA, _VS, []),  # ல்ப  LA+PA
    (0x0BB2, 0x0BB5, _VS, []),  # ல்வ  LA+VA

    # ── RP: ள் (LLA) + consonant ──────────────────────────────────────────────
    (0x0BB3, 0x0B95, _VS, []),  # ள்க  LLA+KA   — களுக்கு
    (0x0BB3, 0x0B9F, _VS, []),  # ள்ட  LLA+TTA

    # ── RP: ற் (RRA) + consonant ──────────────────────────────────────────────
    (0x0BB1, 0x0B95, _VS, []),  # ற்க  RRA+KA   — ஏற்கப்
    (0x0BB1, 0x0B9A, _VS, []),  # ற்ச  RRA+CA
    (0x0BB1, 0x0B9F, _VS, []),  # ற்ட  RRA+TTA
    (0x0BB1, 0x0BA4, _VS, []),  # ற்த  RRA+TA
    (0x0BB1, 0x0BAA, _VS, []),  # ற்ப  RRA+PA   — பெற்று

    # ── RP: ன் (final-NA) + consonant ────────────────────────────────────────
    (0x0BA9, 0x0B95, _VS, []),  # ன்க  ṉ+KA
    (0x0BA9, 0x0B9A, _VS, []),  # ன்ச  ṉ+CA
    (0x0BA9, 0x0B9F, _VS, []),  # ன்ட  ṉ+TTA
    (0x0BA9, 0x0BA4, _VS, []),  # ன்த  ṉ+TA
    (0x0BA9, 0x0BAA, _VS, []),  # ன்ப  ṉ+PA     — அன்பு
    (0x0BA9, 0x0BAE, _VS, []),  # ன்ம  ṉ+MA
    (0x0BA9, 0x0BB0, _VS, []),  # ன்ர  ṉ+RA
    (0x0BA9, 0x0BB2, _VS, []),  # ன்ல  ṉ+LA
    (0x0BA9, 0x0BB5, _VS, []),  # ன்வ  ṉ+VA
    (0x0BA9, 0x0BB1, _VS, []),  # ன்ற  ṉ+RRA    — நன்றி, என்ற

    # ── Grantha ───────────────────────────────────────────────────────────────
    (0x0B95, 0x0BB7, _VS, []),  # க்ஷ  KA+SSA   — க்ஷமிக்கவும்
    (0x0BB8, 0x0BB0, _VS, []),  # ஸ்ர  SA+RA    — ஸ்ரீ
    (0x0BB6, 0x0BB0, _VS, []),  # ஶ்ர  SHA+RA   — ஶ்ரீ
]

# Script-native digits: U+0BE6 ௦ … U+0BEF ௯ (TAMIL DIGIT ZERO..NINE)
DIGITS: list[int] = list(range(0x0BE6, 0x0BF0))
