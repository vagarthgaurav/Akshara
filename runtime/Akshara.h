#ifndef AKSHARA_H
#define AKSHARA_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

/* ── Error codes ─────────────────────────────────────────────────────────── */

#define AKS_OK               0
#define AKS_ERR_BAD_MAGIC   -1   /* file does not start with 0x414B5348 */
#define AKS_ERR_BAD_VERSION -2   /* unsupported format version */
#define AKS_ERR_BAD_SCRIPT  -3   /* unknown script_id */
#define AKS_ERR_TRUNCATED   -4   /* file too small for declared structure */
#define AKS_ERR_NULL_ARG    -5   /* required pointer argument is NULL */
#define AKS_ERR_INVALID_UTF8 -6  /* malformed UTF-8 sequence in input */
#define AKS_ERR_IO          -7   /* read callback returned error */
#define AKS_ERR_NOT_FOUND   -8   /* requested size/weight not in file */

/* ── Script IDs ──────────────────────────────────────────────────────────── */

#define AKS_SCRIPT_KANNADA    0x01
#define AKS_SCRIPT_TAMIL      0x02
#define AKS_SCRIPT_DEVANAGARI 0x03
#define AKS_SCRIPT_TELUGU     0x04
#define AKS_SCRIPT_MALAYALAM  0x05
#define AKS_SCRIPT_BENGALI    0x06
#define AKS_SCRIPT_GUJARATI   0x07

/* ── .aks v3 file structures (packed; layout must match packer.py exactly) ── */

/*
 * Header — 28 bytes.
 *
 * File layout:
 *   [ Header              ]  28 bytes  (this struct)
 *   [ Rule Table          ]  32 bytes  (aks_rule_table_t, at rule_offset)
 *   [ Cluster Key Table   ]  cluster_count × 16 bytes  (at lookup_offset)
 *   [ Composition Table   ]  variable  (at comp_offset)
 *   [ Size Directory      ]  size_count × 24 bytes  (at sizes_offset)
 *   [ Per-size sections   ]  one per entry in size directory
 *       [ Glyph Metrics   ]  glyph_count × 4 bytes
 *       [ Glyph Offsets   ]  glyph_count × 4 bytes (uint32_t into bitmap store)
 *       [ Bitmap Store    ]  packed per-glyph bitmaps (content-only, not padded)
 */
typedef struct __attribute__((packed)) {
    uint32_t magic;          /* 0x414B5348 = "AKSH" */
    uint8_t  version;        /* format version = 3 */
    uint8_t  script_id;
    uint8_t  size_count;     /* number of size+weight variants in this file */
    uint8_t  _reserved;
    uint32_t cluster_count;  /* entries in cluster key table (shared across sizes) */
    uint32_t rule_offset;    /* byte offset to aks_rule_table_t */
    uint32_t lookup_offset;  /* byte offset to cluster key table */
    uint32_t comp_offset;    /* byte offset to composition table */
    uint32_t sizes_offset;   /* byte offset to size directory */
} aks_header_t;              /* 28 bytes */

/*
 * Rule table — 32 bytes.  Unchanged from v2.
 * Script-specific segmentation parameters.  The generic segmenter reads these
 * at init so no firmware change is needed when adding a new script.
 */
typedef struct __attribute__((packed)) {
    uint32_t consonant_start;
    uint32_t consonant_end;
    uint32_t virama;
    uint32_t vowel_sign_start;
    uint32_t vowel_sign_end;  /* coarse range; virama excluded at runtime */
    uint32_t modifier_start;
    uint32_t modifier_end;
    uint8_t  max_conjunct_depth;
    uint8_t  _reserved[3];
} aks_rule_table_t;           /* 32 bytes */

/*
 * Cluster key entry — 16 bytes (was 32 in v2).
 *
 * Sorted lexicographically by cp[6] for binary search.
 * All Indic codepoints are in the BMP (U+0000–U+FFFF), so uint16_t suffices.
 * comp_off is a byte offset from the file's comp_offset into the composition table.
 */
typedef struct __attribute__((packed)) {
    uint16_t cp[6];          /* codepoint sequence, zero-padded; BMP only */
    uint32_t comp_off;       /* byte offset into composition table */
} aks_key_entry_t;            /* 16 bytes */

/*
 * Composition entry — 8 bytes.
 * Stored per-glyph within a cluster's composition block.
 * Positions are in font design units (size-independent); the MCU scales them
 * to pixels at render time via: pixels = round(du * size_px / upem).
 */
typedef struct __attribute__((packed)) {
    uint16_t glyph_idx;      /* index into per-size glyph store */
    int16_t  hb_x_off;       /* HarfBuzz x_offset in design units (usually 0) */
    int16_t  hb_y_off;       /* HarfBuzz y_offset in design units (positive = up) */
    uint16_t hb_advance;     /* HarfBuzz x_advance in design units */
} aks_comp_entry_t;           /* 8 bytes */

/*
 * Composition block header — 2 bytes, immediately followed by glyph_count ×
 * aks_comp_entry_t.  Accessed via: comp_offset + aks_key_entry_t.comp_off.
 */
typedef struct __attribute__((packed)) {
    uint8_t  glyph_count;    /* number of glyphs in this cluster */
    uint8_t  _pad;
} aks_comp_hdr_t;             /* 2 bytes */

/*
 * Size+weight directory entry — 24 bytes.
 *
 * Points to per-size glyph metrics, bitmap offsets, and the bitmap store.
 * Regular and Bold at the same pixel size have separate entries but share
 * the cluster key table and composition table (shaping is weight-independent).
 */
typedef struct __attribute__((packed)) {
    uint8_t  size_px;        /* pixel size (e.g. 16, 22, 24) */
    uint8_t  weight;         /* 0 = Regular, 1 = Bold */
    uint8_t  bpp;            /* 1 = monochrome, 2 = 4-grey */
    uint8_t  glyph_height;   /* full box height in pixels (ascender + |descender|) */
    uint8_t  baseline;       /* rows from box top to baseline */
    uint8_t  _reserved;
    uint16_t upem;           /* font units per em (typically 2048) */
    uint16_t glyph_count;    /* unique glyphs in this size+weight variant */
    uint16_t _reserved2;
    uint32_t metrics_offset; /* byte offset to aks_glyph_metrics_t[glyph_count] */
    uint32_t offsets_offset; /* byte offset to uint32_t[glyph_count] (into bitmap store) */
    uint32_t bitmaps_offset; /* byte offset to packed glyph bitmaps */
} aks_size_entry_t;           /* 24 bytes */

/*
 * Per-glyph metrics — 4 bytes.
 * FreeType metrics for one glyph at a specific pixel size.
 * bearing_x = ft.bitmap_left  (signed: pen-to-bitmap-left, can be negative)
 * top_from_base = ft.bitmap_top  (signed: rows above baseline; negative = below)
 */
typedef struct __attribute__((packed)) {
    uint8_t  width;          /* bitmap width in pixels (0 for non-printing glyphs) */
    uint8_t  height;         /* bitmap height in pixels (content rows only) */
    int8_t   bearing_x;      /* ft.bitmap_left */
    int8_t   top_from_base;  /* ft.bitmap_top (positive = above baseline) */
} aks_glyph_metrics_t;        /* 4 bytes */

/* ── Callbacks (app-provided) ────────────────────────────────────────────── */

/*
 * Read bytes from the .aks source.
 * Returns 0 on success, negative on error.
 */
typedef int (*aks_read_fn)(uint32_t offset, uint8_t *buf,
                           uint32_t size, void *user_data);

/*
 * Blit one glyph bitmap to the display.
 *
 * Called once per glyph (not once per cluster as in v2).
 * (x, y) is the exact screen position of the bitmap's top-left corner.
 * (w, h) is the content bitmap size (not the full glyph box).
 * The bitmap may be 1bpp (packed, MSB first) or 2bpp (4-grey, MSB first).
 */
typedef void (*aks_blit_fn)(int16_t x, int16_t y,
                             const uint8_t *bitmap,
                             uint16_t w, uint16_t h,
                             uint8_t bpp, void *user_data);

/* ── Context ─────────────────────────────────────────────────────────────── */

typedef struct {
    aks_read_fn       read;
    void             *read_ud;
    aks_blit_fn       blit;
    void             *blit_ud;
    /* internal — do not access directly */
    aks_header_t      _hdr;
    aks_rule_table_t  _rules;
    aks_size_entry_t  _size;   /* active size+weight entry */
} akshara_ctx_t;

/* ── C API ───────────────────────────────────────────────────────────────── */

/*
 * Initialise context. Reads and validates header + rule table.
 * Selects the first size+weight entry in the file as the active size.
 *
 * read     — I/O callback for SD, LittleFS, FatFs, etc.
 *            Pass NULL when read_ud is a pointer to a const byte array in
 *            addressable memory (e.g. a .h file baked into flash via aks2h.py).
 * read_ud  — passed to read on every call; for the NULL-read case, pass
 *            the font array pointer directly.
 *
 * Returns AKS_OK on success, AKS_ERR_* on failure.
 */
int akshara_init(akshara_ctx_t *ctx,
                aks_read_fn   read,    aks_blit_fn  blit,
                void         *read_ud, void         *blit_ud);

/*
 * Switch to a different .aks font without changing the display callbacks.
 * Selects the first size+weight entry in the new file.
 * Pass NULL read with a const array pointer in read_ud for flash-baked fonts.
 */
int akshara_set_font(akshara_ctx_t *ctx, aks_read_fn read, void *read_ud);

/*
 * Select a specific size+weight from a multi-size .aks file.
 * Must be called after akshara_init() if you want a size other than the first.
 * Returns AKS_OK if found, AKS_ERR_NOT_FOUND if no matching entry.
 */
int akshara_select_size(akshara_ctx_t *ctx, uint8_t size_px, uint8_t weight);

/* Render a NUL-terminated UTF-8 string at (x, y).
 * Calls ctx->blit once per glyph with exact screen coordinates.
 * Returns x position after the last cluster. */
int16_t akshara_render(akshara_ctx_t *ctx, int16_t x, int16_t y,
                      const char *utf8);

/* Measure a UTF-8 string without rendering. Returns total advance width. */
int16_t akshara_measure(akshara_ctx_t *ctx, const char *utf8);

#ifdef __cplusplus
} /* extern "C" */

/* ── C++ API ─────────────────────────────────────────────────────────────── */

/*
 *   Akshara akshara(blit_gxepd2, &display);
 *
 *   void setup() {
 *     akshara.setFont(read_sd, &font_file);
 *     akshara.render(0, 0, "ಕನ್ನಡ");
 *     akshara.selectSize(22, 0);   // switch to 22px Regular in a multi-size file
 *   }
 */
class Akshara {
public:
    Akshara(aks_blit_fn blit, void *blit_ud)
        : _blit(blit), _blit_ud(blit_ud) {}

    /* Load or switch font. Selects first size+weight by default.
     * Pass NULL read with a const array pointer in read_ud for flash fonts. */
    int setFont(aks_read_fn read, void *read_ud) {
        return akshara_init(&_ctx, read, _blit, read_ud, _blit_ud);
    }

    /* Select a specific size+weight from a multi-size file. */
    int selectSize(uint8_t size_px, uint8_t weight = 0) {
        return akshara_select_size(&_ctx, size_px, weight);
    }

    /* Render a NUL-terminated UTF-8 string at (x, y).
     * Returns the x position after the last cluster. */
    int16_t render(int16_t x, int16_t y, const char *utf8) {
        return akshara_render(&_ctx, x, y, utf8);
    }

    /* Measure a UTF-8 string without rendering. Returns total advance width. */
    int16_t measure(const char *utf8) {
        return akshara_measure(&_ctx, utf8);
    }

private:
    akshara_ctx_t _ctx;
    aks_blit_fn   _blit;
    void         *_blit_ud;
};

#endif /* __cplusplus */
#endif /* AKSHARA_H */
