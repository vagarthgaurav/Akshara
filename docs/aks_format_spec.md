# .aks format spec v3

One `.aks` file per script, containing all size+weight variants for that script.
Examples: `noto_kannada_regular.aks`, `noto_tamil_regular.aks`

The format is script-agnostic. Script-specific rules are embedded as a rule table
inside the file; the MCU has one generic segmenter that reads rules from the file.
Adding a new Indic script requires only a new `.aks` file; no firmware change.

---

## File layout

```text
[ Header              ]  28 bytes, fixed
[ Rule Table          ]  32 bytes, per-script segmentation rules  (at rule_offset)
[ Cluster Key Table   ]  cluster_count × 16 bytes, sorted by codepoint sequence  (at lookup_offset)
[ Composition Table   ]  variable, per-cluster glyph composition data  (at comp_offset)
[ Size Directory      ]  size_count × 24 bytes, one entry per size+weight variant  (at sizes_offset)
  Per size+weight:
  [ Glyph Metrics     ]  glyph_count × 4 bytes  (at metrics_offset)
  [ Glyph Offsets     ]  glyph_count × 4 bytes, uint32_t into bitmap store  (at offsets_offset)
  [ Bitmap Store      ]  packed per-glyph bitmaps  (at bitmaps_offset)
```

Cluster key table and composition table are shared across all size+weight variants
(shaping is weight- and size-independent). Only glyph bitmaps differ per size+weight.

---

## Header

```c
typedef struct __attribute__((packed)) {
    uint32_t magic;          // 0x414B5348 = "AKSH"
    uint8_t  version;        // format version = 3
    uint8_t  script_id;      // see Script IDs
    uint8_t  size_count;     // number of size+weight variants in this file
    uint8_t  _reserved;
    uint32_t cluster_count;  // entries in cluster key table (shared across sizes)
    uint32_t rule_offset;    // byte offset to aks_rule_table_t
    uint32_t lookup_offset;  // byte offset to cluster key table
    uint32_t comp_offset;    // byte offset to composition table
    uint32_t sizes_offset;   // byte offset to size directory
} aks_header_t;              // 28 bytes
```

### Script IDs

```c
#define AKS_SCRIPT_KANNADA    0x01
#define AKS_SCRIPT_TAMIL      0x02
#define AKS_SCRIPT_DEVANAGARI 0x03
#define AKS_SCRIPT_TELUGU     0x04
#define AKS_SCRIPT_MALAYALAM  0x05
#define AKS_SCRIPT_BENGALI    0x06
#define AKS_SCRIPT_GUJARATI   0x07
```

### Validation

On `akshara_init`, the parser must verify:

- `magic == 0x414B5348`, else `AKS_ERR_BAD_MAGIC`
- `version == 3`, else `AKS_ERR_BAD_VERSION`
- `script_id` is a known value, else `AKS_ERR_BAD_SCRIPT`
- File is large enough for all declared sections, else `AKS_ERR_TRUNCATED`

---

## Rule table

At `rule_offset`. The generic segmenter reads this at init. Unchanged from v2.

```c
typedef struct __attribute__((packed)) {
    uint32_t consonant_start;     // Unicode range: first consonant codepoint
    uint32_t consonant_end;       // Unicode range: last consonant codepoint
    uint32_t virama;              // virama / halant codepoint for this script
    uint32_t vowel_sign_start;    // dependent vowel sign range start
    uint32_t vowel_sign_end;      // dependent vowel sign range end
    uint32_t modifier_start;      // anusvara, visarga, chandrabindu, nukta range start
    uint32_t modifier_end;        // modifier range end
    uint8_t  max_conjunct_depth;  // max virama+consonant bonds in one cluster
    uint8_t  _reserved[3];
} aks_rule_table_t;               // 32 bytes
```

### Values per script

| Field                | Kannada  | Tamil    | Devanagari | Telugu   | Malayalam | Bengali  | Gujarati |
|----------------------|----------|----------|------------|----------|-----------|----------|----------|
| `consonant_start`    | U+0C95   | U+0B95   | U+0915     | U+0C15   | U+0D15    | U+0995   | U+0A95   |
| `consonant_end`      | U+0CB9   | U+0BB9   | U+0939     | U+0C39   | U+0D39    | U+09B9   | U+0AB9   |
| `virama`             | U+0CCD   | U+0BCD   | U+094D     | U+0C4D   | U+0D4D    | U+09CD   | U+0ACD   |
| `vowel_sign_start`   | U+0CBE   | U+0BBE   | U+093E     | U+0C3E   | U+0D3E    | U+09BE   | U+0ABE   |
| `vowel_sign_end`     | U+0CCD   | U+0BCC   | U+094C     | U+0C4C   | U+0D4C    | U+09CC   | U+0ACC   |
| `modifier_start`     | U+0C82   | U+0B82   | U+0900     | U+0C01   | U+0D02    | U+0981   | U+0A81   |
| `modifier_end`       | U+0C83   | U+0B83   | U+0903     | U+0C03   | U+0D03    | U+0983   | U+0A83   |
| `max_conjunct_depth` | 2        | 1        | 3          | 2        | 2         | 2        | 2        |

Telugu note: `vowel_sign_end` U+0C4C is a coarse range bound; U+0C45 and U+0C49 are
unassigned and skipped by the host enumerator. U+0C4D (virama) is excluded at runtime.
U+0C29 (consonant range gap) is unassigned and excluded at host.

Malayalam note: `vowel_sign_end` U+0D4C is a coarse range bound; virama U+0D4D is
excluded at runtime by the `aks_is_vowel_sign` classifier. Chillu letters
(U+0D7A-U+0D7F) fall outside the consonant range and are treated as single-codepoint
clusters naturally; no rule table extension required.

---

## Cluster key table

At `lookup_offset`. Sorted lexicographically by `cp[6]` for binary search, 16 bytes
per entry (was 32 in v2). All Indic codepoints are in the BMP (U+0000-U+FFFF),
so `uint16_t` suffices.

```c
typedef struct __attribute__((packed)) {
    uint16_t cp[6];      // codepoint sequence, zero-padded; BMP only
    uint32_t comp_off;   // byte offset into composition table (from comp_offset)
} aks_key_entry_t;       // 16 bytes
```

Maximum cluster depth: 6 codepoints. Covers depth-2 conjuncts
(C + virama + C + virama + C = 5 slots) plus one vowel sign or modifier (6 slots).
Shorter clusters zero-pad from the right.

### Sort order

Entries are sorted by lexicographic comparison of the six `uint16_t` values in
`cp[0..5]`. `cp[0]` is the most significant key. Zero slots sort before any
codepoint value.

### Binary search

The MCU compares `uint32_t` segmenter keys against `uint16_t` file entries per slot.
A match requires all six slots to be equal. ~13 read steps for 7000 clusters.

---

## Composition table

At `comp_offset`. Each cluster points into this table via `aks_key_entry_t.comp_off`.

### Composition block

```c
typedef struct __attribute__((packed)) {
    uint8_t  glyph_count;    // number of glyphs in this cluster
    uint8_t  _pad;
} aks_comp_hdr_t;             // 2 bytes, followed by glyph_count × aks_comp_entry_t
```

### Composition entry

```c
typedef struct __attribute__((packed)) {
    uint16_t glyph_idx;      // index into per-size glyph store
    int16_t  hb_x_off;       // HarfBuzz x_offset in design units (usually 0)
    int16_t  hb_y_off;       // HarfBuzz y_offset in design units (positive = up)
    uint16_t hb_advance;     // HarfBuzz x_advance in design units
} aks_comp_entry_t;           // 8 bytes
```

Positions are in font design units. The MCU scales to pixels at render time:
`pixels = round(du × size_px / upem)`

---

## Size directory

At `sizes_offset`. Array of `size_count` entries, one per size+weight variant.
Regular and Bold at the same pixel size are separate entries but share the cluster
key table and composition table.

```c
typedef struct __attribute__((packed)) {
    uint8_t  size_px;        // pixel size (e.g. 16, 22, 24)
    uint8_t  weight;         // 0 = Regular, 1 = Bold
    uint8_t  bpp;            // 1 = monochrome, 2 = 4-grey
    uint8_t  glyph_height;   // full box height in pixels (ascender + |descender|)
    uint8_t  baseline;       // rows from box top to baseline
    uint8_t  _reserved;
    uint16_t upem;           // font units per em (typically 2048)
    uint16_t glyph_count;    // unique glyphs in this size+weight variant
    uint16_t _reserved2;
    uint32_t metrics_offset; // byte offset to aks_glyph_metrics_t[glyph_count]
    uint32_t offsets_offset; // byte offset to uint32_t[glyph_count] into bitmap store
    uint32_t bitmaps_offset; // byte offset to packed glyph bitmaps
} aks_size_entry_t;           // 24 bytes
```

---

## Glyph metrics

At `metrics_offset` within each size entry. Array of `glyph_count` entries.

```c
typedef struct __attribute__((packed)) {
    uint8_t  width;          // bitmap width in pixels (0 for non-printing glyphs)
    uint8_t  height;         // bitmap height in pixels (content rows only)
    int8_t   bearing_x;      // ft.bitmap_left (signed: pen-to-bitmap-left)
    int8_t   top_from_base;  // ft.bitmap_top (positive = above baseline)
} aks_glyph_metrics_t;        // 4 bytes
```

---

## Bitmap store

At `bitmaps_offset` within each size entry. Glyph offsets in the store are at
`offsets_offset` (array of `uint32_t[glyph_count]`).

| `bpp` | Format          | Bits per pixel | Grey levels |
|-------|-----------------|----------------|-------------|
| 1     | 1bpp monochrome | 1              | 2 (on/off)  |
| 2     | 2bpp grey       | 2              | 4           |

Row stride (bytes) = `ceil(width × bpp / 8)`

Rows are stored top-to-bottom. Within each row, bits are packed MSB-first.
No padding between bitmaps.

---

## Error codes

```c
#define AKS_OK                  0
#define AKS_ERR_BAD_MAGIC      -1   // file does not start with 0x414B5348
#define AKS_ERR_BAD_VERSION    -2   // unsupported format version
#define AKS_ERR_BAD_SCRIPT     -3   // unknown script_id
#define AKS_ERR_TRUNCATED      -4   // file too small for declared structure
#define AKS_ERR_NULL_ARG       -5   // required pointer argument is NULL
#define AKS_ERR_INVALID_UTF8   -6   // malformed UTF-8 sequence in input
#define AKS_ERR_IO             -7   // read callback returned error
#define AKS_ERR_NOT_FOUND      -8   // requested size/weight not in file
```

---

## File generation

`.aks` files are produced by `akshara-generator/packer.py`. Pass `--sizes` for
multi-size output and `--font-bold` to embed a Bold variant.

```bash
# Single size (default)
just script=kannada pack

# Multiple sizes in one file
just script=kannada sizes=16,20,22,24 pack

# Include Bold variant
just script=kannada font_bold=fonts/original/NotoSansKannada-Bold.ttf sizes=16,22 pack
```

Output is written to `fonts/generated/noto_{script}_regular.aks`.

Naming convention: `noto_{script}_regular.aks` (size and weight embedded in file).

Use `akshara-generator/aks2h.py` to convert a `.aks` binary into a `const uint8_t[]`
C header for baking directly into firmware flash (no SD card or filesystem required).
