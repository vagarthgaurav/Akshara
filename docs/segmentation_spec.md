# Akshara Segmentation Spec

This document defines how codepoint sequences are grouped into clusters (aksharas)
for each supported script. It is the contract between `host/cluster_enum.py` and
`runtime/segmenter.c` — both sides must implement these rules identically.

---

## Cluster Grammar

One akshara = one cluster = one lookup key. The grammar is the same for all scripts;
only the codepoint ranges differ.

```text
cluster = base_consonant
        + (virama + consonant)*    ← 0 to max_conjunct_depth repetitions
        + vowel_sign?              ← 0 or 1 dependent vowel sign
        + modifier?                ← 0 or 1 anusvara / visarga / chandrabindu
```

Additional cluster types:

- **Standalone vowel** — independent vowel form, single codepoint.
- **Digit / ASCII** — single codepoint; included in the .aks for mixed-script text.

Clusters are zero-padded to `uint32_t cp[6]` for storage and binary search.

---

## Segmenter State Machine

The MCU segmenter processes one codepoint at a time, driven by the rule table
embedded in the `.aks` header.

```text
State: IDLE
  consonant            → emit nothing, start new cluster (State: CONSONANT)
  independent vowel    → emit single-codepoint cluster, stay IDLE
  anything else        → emit single-codepoint cluster, stay IDLE

State: CONSONANT
  virama               → if depth < max_conjunct_depth: absorb (State: VIRAMA)
                         else: emit current cluster, start virama as new cluster
  vowel_sign           → absorb into cluster (State: VOWEL)
  modifier             → absorb into cluster, emit cluster, go IDLE
  consonant            → emit current cluster, start new cluster (State: CONSONANT)
  anything else        → emit current cluster, go IDLE, reprocess codepoint

State: VIRAMA
  consonant            → absorb consonant, increment depth (State: CONSONANT)
  anything else        → emit current cluster (including virama), go IDLE, reprocess

State: VOWEL
  modifier             → absorb into cluster, emit cluster, go IDLE
  anything else        → emit current cluster, go IDLE, reprocess codepoint
```

**OOV fallback:** if a cluster key is not found in the lookup table, render each
codepoint individually using single-codepoint keys. If a single codepoint is also
missing, skip silently. Never show a missing-glyph box.

---

## Script Rules

### Kannada

Unicode block: U+0C80–U+0CFF

| Field               | Value                                           |
|---------------------|-------------------------------------------------|
| `consonant_start`   | U+0C95 (ಕ)                                      |
| `consonant_end`     | U+0CB9 (ಹ)                                      |
| `virama`            | U+0CCD (ಿ halant)                                |
| `vowel_sign_start`  | U+0CBE (ಾ)                                       |
| `vowel_sign_end`    | U+0CCD (reuse virama end; see note)             |
| `modifier_start`    | U+0C82 (ಂ anusvara)                              |
| `modifier_end`      | U+0C83 (ಃ visarga)                               |
| `max_conjunct_depth`| 2                                               |

Vowel sign ranges (non-contiguous in Unicode; treat as two sub-ranges):

- U+0CBE–U+0CC4
- U+0CC6–U+0CC8
- U+0CCA–U+0CCD

Cluster count target: **~800–1000**

---

### Tamil

Unicode block: U+0B80–U+0BFF

| Field               | Value                                           |
|---------------------|-------------------------------------------------|
| `consonant_start`   | U+0B95 (க)                                      |
| `consonant_end`     | U+0BB9 (ஹ)                                      |
| `virama`            | U+0BCD (் pulli)                                 |
| `vowel_sign_start`  | U+0BBE (ா)                                       |
| `vowel_sign_end`    | U+0BCC (ௌ)                                       |
| `modifier_start`    | U+0B82 (ஂ anusvara)                              |
| `modifier_end`      | U+0B83 (ஃ visarga)                              |
| `max_conjunct_depth`| 1                                               |

Vowel sign ranges:

- U+0BBE–U+0BC8
- U+0BCA–U+0BCC

Note: Tamil has very few true conjuncts. Most consonant clusters are written with
explicit pulli (virama) rather than a ligature. `max_conjunct_depth=1` reflects this.

Cluster count target: **~800–1000**

---

### Devanagari

Unicode block: U+0900–U+097F

| Field               | Value                                           |
|---------------------|-------------------------------------------------|
| `consonant_start`   | U+0915 (क)                                      |
| `consonant_end`     | U+0939 (ह)                                      |
| `virama`            | U+094D (् halant)                                |
| `vowel_sign_start`  | U+093E (ा)                                       |
| `vowel_sign_end`    | U+094C (ौ)                                       |
| `modifier_start`    | U+0900 (chandrabindu range start)               |
| `modifier_end`      | U+0903 (ः visarga)                               |
| `max_conjunct_depth`| 3                                               |

Extended consonant range (nukta forms): U+0958–U+095F

Modifier codepoints:

- U+0900 chandrabindu (ऀ)
- U+0901 anusvara (ँ)
- U+0902 anusvara (ं)
- U+0903 visarga (ः)

Note: Devanagari has rich conjunct formation. `max_conjunct_depth=3` covers
three-consonant clusters (e.g. क्ष्ण). Only corpus-attested conjuncts are
enumerated — combinations with near-zero real-world occurrence are excluded.

Cluster count target: **~800–1000**

---

### Malayalam

Unicode block: U+0D00–U+0D7F

| Field               | Value                                           |
|---------------------|-------------------------------------------------|
| `consonant_start`   | U+0D15 (KA)                                     |
| `consonant_end`     | U+0D39 (HA; U+0D29 unassigned, skipped by host) |
| `virama`            | U+0D4D (virama)                                 |
| `vowel_sign_start`  | U+0D3E (AA matra)                               |
| `vowel_sign_end`    | U+0D4C (AU matra; virama U+0D4D excl. runtime)  |
| `modifier_start`    | U+0D02 (anusvara)                               |
| `modifier_end`      | U+0D03 (visarga)                                |
| `max_conjunct_depth`| 2                                               |

Vowel sign ranges (non-contiguous; virama excluded):

- U+0D3E–U+0D44
- U+0D46–U+0D48
- U+0D4A–U+0D4C

Chillu letters (U+0D7A–U+0D7F): atomic Unicode codepoints representing final
consonant forms (e.g. ൺ ൻ ർ ൽ ൾ ൿ). They fall outside the consonant range, so
the segmenter emits them as single-codepoint clusters without any special case.
They are precomputed in the .aks key table via `ScriptConfig.chillus`.

Cluster count target: **~800–1000**

---

## Key Table Entry

Clusters are stored as sorted `uint32_t cp[6]` arrays (zero-padded). Sorting is
lexicographic on the six uint32_t values. This enables binary search on the MCU.

```c
typedef struct __attribute__((packed)) {
    uint32_t cp[6];      // codepoint sequence; unused slots = 0x00000000
    uint32_t bitmap_off; // byte offset into bitmap store
    uint16_t advance;    // horizontal advance in pixels
    uint8_t  width;      // bitmap width in pixels
    uint8_t  bearing_x;  // horizontal bearing (cast to int8_t for signed use)
} aks_key_entry_t;       // 32 bytes per entry
```

---

## Host Cluster Enumeration (`cluster_enum.py`)

For each script, enumerate:

1. All standalone independent vowels — single-codepoint clusters.
2. All `consonant` forms — single-codepoint clusters.
3. All `consonant + vowel_sign` combinations.
4. All `consonant + virama` (explicit half-form).
5. All `consonant + virama + consonant` conjuncts (depth 1), optionally with vowel sign.
6. For scripts with `max_conjunct_depth >= 2`: depth-2 conjuncts
   (`C + V + C + V + C [+ vowel_sign]`), frequency-filtered.
7. For Devanagari with `max_conjunct_depth == 3`: depth-3 conjuncts, frequency-filtered.
8. All above forms with an optional trailing modifier.
9. Digits (U+0030–U+0039) and common ASCII punctuation as single-codepoint clusters.

Apply corpus frequency cutoff for depth ≥ 2 conjuncts to stay within the cluster
count target. Skip combinations with near-zero real-world occurrence.

---

## Unit Test Contract (`host/test/test_clusters.py`)

Every segmenter rule must have a corresponding test. Minimum test cases:

| Input string | Expected clusters |
| --- | --- |
| Simple consonant | 1 cluster |
| Consonant + vowel sign | 1 cluster |
| Consonant + virama + consonant | 1 cluster (conjunct) |
| Conjunct at max depth | 1 cluster |
| Conjunct exceeding max depth | 2 clusters (split at depth limit) |
| Consonant + modifier | 1 cluster |
| Mixed Indic + ASCII | Indic clusters + ASCII single-codepoint clusters |
| Unknown codepoint mid-string | OOV cluster emitted, segmentation continues |
| Empty string | 0 clusters |
| Standalone vowel | 1 cluster |
