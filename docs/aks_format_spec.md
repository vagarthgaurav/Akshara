# .aks File Format Spec

One `.aks` file per **script + size + weight** combination.
Examples: `noto_kannada_regular_24.aks`, `noto_tamil_bold_16.aks`

The format is script-agnostic. Script-specific rules are embedded as a rule table
inside the file — the MCU has one generic segmenter that reads rules from the file.
Adding a new Indic script requires only a new `.aks` — no firmware change.

---

## File Layout

```text
[ Header         ]  28 bytes, fixed
[ Rule Table     ]  32 bytes, per-script segmentation rules
[ Cluster Keys   ]  cluster_count × 32 bytes, sorted by codepoint sequence
[ Bitmap Store   ]  variable, packed bitmaps
```

Sections are contiguous. Offsets to each section are stored in the header.

---

## Header

```c
typedef struct __attribute__((packed)) {
    uint32_t magic;          // 0x414B5348 = "AKSH"
    uint8_t  version;        // format version, currently 2
    uint8_t  script_id;      // see Script IDs
    uint8_t  weight;         // 0 = Regular, 1 = Bold
    uint8_t  bpp;            // 1 = 1bpp monochrome, 2 = 2bpp 4-grey
    uint16_t glyph_height;   // pixel height of tallest glyph
    uint8_t  baseline;       // pixels from top of glyph box to baseline
    uint8_t  _reserved;
    uint32_t cluster_count;  // number of entries in cluster key table
    uint32_t rule_offset;    // byte offset from file start to rule table
    uint32_t lookup_offset;  // byte offset from file start to cluster key table
    uint32_t bitmap_offset;  // byte offset from file start to bitmap store
} aks_header_t;              // 28 bytes total
```

### Script IDs

```c
#define AKS_SCRIPT_KANNADA    0x01
#define AKS_SCRIPT_TAMIL      0x02
#define AKS_SCRIPT_DEVANAGARI 0x03
#define AKS_SCRIPT_TELUGU     0x04
#define AKS_SCRIPT_MALAYALAM  0x05
```

### Validation

On `akshara_init`, the parser must verify:

- `magic == 0x414B5348` — else `AKS_ERR_BAD_MAGIC`
- `version == 2` — else `AKS_ERR_BAD_VERSION`
- `script_id` is a known value — else `AKS_ERR_BAD_SCRIPT`
- File is large enough for all declared sections — else `AKS_ERR_TRUNCATED`

---

## Rule Table

Immediately follows the header (at `rule_offset`). The generic segmenter reads this
at init time. All Indic scripts share the same structure; only values differ.

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
} aks_rule_table_t;               // 32 bytes total
```

### Values per Script

| Field                | Kannada       | Tamil         | Devanagari              | Telugu        | Malayalam     |
|----------------------|---------------|---------------|-------------------------|---------------|---------------|
| `consonant_start`    | U+0C95        | U+0B95        | U+0915                  | U+0C15        | U+0D15        |
| `consonant_end`      | U+0CB9        | U+0BB9        | U+0939                  | U+0C39        | U+0D39        |
| `virama`             | U+0CCD        | U+0BCD        | U+094D                  | U+0C4D        | U+0D4D        |
| `vowel_sign_start`   | U+0CBE        | U+0BBE        | U+093E                  | U+0C3E        | U+0D3E        |
| `vowel_sign_end`     | U+0CCD        | U+0BCC        | U+094C                  | U+0C4C        | U+0D4C        |
| `modifier_start`     | U+0C82        | U+0B82        | U+0900                  | U+0C01        | U+0D02        |
| `modifier_end`       | U+0C83        | U+0B83        | U+0903                  | U+0C03        | U+0D03        |
| `max_conjunct_depth` | 2             | 1             | 3                       | 2             | 2             |

Telugu note: `vowel_sign_end` U+0C4C is a coarse range bound; U+0C45 and U+0C49 are
unassigned and skipped by the host enumerator. U+0C4D (virama) is excluded at runtime.
U+0C29 (consonant range gap) is unassigned and excluded at host.

Malayalam note: `vowel_sign_end` U+0D4C is a coarse range bound; virama U+0D4D is
excluded at runtime by the `aks_is_vowel_sign` classifier. Chillu letters
(U+0D7A–U+0D7F) fall outside the consonant range and are treated as single-codepoint
clusters naturally — no rule table extension required.

---

## Cluster Key Table

Sorted array of fixed-size entries starting at `lookup_offset`. Sorted
lexicographically by the `cp[6]` codepoint sequence to enable binary search on MCU.

```c
typedef struct __attribute__((packed)) {
    uint32_t cp[6];      // codepoint sequence; unused slots = 0x00000000
    uint32_t bitmap_off; // byte offset into bitmap store (from bitmap_offset)
    uint16_t advance;    // horizontal advance in pixels
    uint8_t  width;      // bitmap width in pixels
    uint8_t  bearing_x;  // horizontal bearing (cast to int8_t for signed use)
} aks_key_entry_t;       // 32 bytes per entry
```

Maximum cluster depth: 6 codepoints. Covers depth-2 conjuncts
(C + virama + C + virama + C = 5 slots) plus one vowel sign or modifier (6 slots).
Depth-2 conjunct + VS + modifier = 7 codepoints and falls through to OOV.
Devanagari depth-3 will require cp[8] (format v3).
Shorter clusters zero-pad from the right.

### Sort Order

Entries are sorted by lexicographic comparison of the six `uint32_t` values in
`cp[0..5]`. `cp[0]` is the most significant key. Zero slots sort before any
codepoint value (0x00000000 < any valid Unicode codepoint).

### Binary Search

The MCU performs standard binary search comparing `uint32_t cp[6]` arrays.
A match requires all six values to be equal.

---

## Bitmap Store

Packed bitmaps stored contiguously starting at `bitmap_offset`. Each bitmap is
referenced by `bitmap_off` in its key table entry (offset relative to `bitmap_offset`).

### Encoding

| `bpp` | Format          | Bits per pixel | Grey levels |
|-------|-----------------|----------------|-------------|
| 1     | 1bpp monochrome | 1              | 2 (on/off)  |
| 2     | 2bpp grey       | 2              | 4           |

Row stride (bytes) = `ceil(width × bpp / 8)`

Rows are stored top-to-bottom. Within each row, bits are packed MSB-first.
No padding between bitmaps. No padding between rows within a bitmap.

### Scratch Buffer Sizing

Bitmaps are not loaded into RAM at init. During render, one bitmap at a time is
read into a stack-allocated scratch buffer:

```text
scratch_size = ceil(max_width / (8 / bpp)) × glyph_height
```

At 24px with 1bpp this is approximately 1536 bytes.

---

## Error Codes

```c
#define AKS_OK                  0
#define AKS_ERR_BAD_MAGIC      -1   // file does not start with 0x414B5348
#define AKS_ERR_BAD_VERSION    -2   // unsupported format version
#define AKS_ERR_BAD_SCRIPT     -3   // unknown script_id
#define AKS_ERR_TRUNCATED      -4   // file too small for declared structure
#define AKS_ERR_NULL_ARG       -5   // required pointer argument is NULL
#define AKS_ERR_INVALID_UTF8   -6   // malformed UTF-8 sequence in input
#define AKS_ERR_IO             -7   // read callback returned error
```

---

## File Generation

`.aks` files are produced by `aks-generator/akshara_gen.py`. The packer (`aks-generator/packer.py`)
validates the output by re-parsing it and comparing `cluster_count` and a sample
of bitmap offsets before writing is considered complete.

Naming convention: `{font}_{script}_{weight}_{size}.aks`
Example: `noto_kannada_regular_22.aks`

Use `aks-generator/aks2h.py` to convert a `.aks` binary into a `const uint8_t[]` C header
for baking directly into firmware flash (no SD card or filesystem required).
