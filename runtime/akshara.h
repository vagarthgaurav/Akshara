#ifndef AKSHAR_H
#define AKSHAR_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

/* ── Error codes ─────────────────────────────────────────────────────────── */

#define AKS_OK               0
#define AKS_ERR_BAD_MAGIC   -1   /* file does not start with 0x56414741 */
#define AKS_ERR_BAD_VERSION -2   /* unsupported format version */
#define AKS_ERR_BAD_SCRIPT  -3   /* unknown script_id */
#define AKS_ERR_TRUNCATED   -4   /* file too small for declared structure */
#define AKS_ERR_NULL_ARG    -5   /* required pointer argument is NULL */
#define AKS_ERR_INVALID_UTF8 -6  /* malformed UTF-8 sequence in input */
#define AKS_ERR_IO          -7   /* read callback returned error */

/* ── Script IDs ──────────────────────────────────────────────────────────── */

#define AKS_SCRIPT_KANNADA    0x01
#define AKS_SCRIPT_TAMIL      0x02
#define AKS_SCRIPT_DEVANAGARI 0x03
#define AKS_SCRIPT_TELUGU     0x04
#define AKS_SCRIPT_MALAYALAM  0x05

/* ── .aks file structures (packed; layout must match packer.py byte-for-byte) */

typedef struct __attribute__((packed)) {
    uint32_t magic;          /* 0x56414741 = "VAGA" */
    uint8_t  version;        /* format version, currently 1 */
    uint8_t  script_id;
    uint8_t  weight;         /* 0=Regular, 1=Bold */
    uint8_t  bpp;            /* 1=monochrome, 2=4-grey */
    uint16_t glyph_height;   /* pixel height of tallest glyph */
    uint8_t  baseline;       /* rows from box top to baseline */
    uint8_t  _reserved;
    uint32_t cluster_count;
    uint32_t rule_offset;    /* byte offset to rule table */
    uint32_t lookup_offset;  /* byte offset to cluster key table */
    uint32_t bitmap_offset;  /* byte offset to bitmap store */
} aks_header_t;              /* 28 bytes */

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

typedef struct __attribute__((packed)) {
    uint32_t cp[4];           /* codepoint sequence, zero-padded */
    uint32_t bitmap_off;      /* byte offset into bitmap store */
    uint16_t advance;         /* horizontal advance in pixels */
    uint8_t  width;           /* bitmap width in pixels */
    uint8_t  bearing_x;       /* horizontal bearing (cast to int8_t for use) */
} aks_key_entry_t;            /* 24 bytes */

/* ── Callbacks (app-provided) ────────────────────────────────────────────── */

/* Read bytes from the .aks source. Returns 0 on success, negative on error. */
typedef int (*aks_read_fn)(uint32_t offset, uint8_t *buf,
                           uint32_t size, void *user_data);

/* Blit one rendered cluster to the display. */
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
} akshara_ctx_t;

/* ── Public API ──────────────────────────────────────────────────────────── */

/*
 * Initialise context. Reads and validates header + rule table.
 * The key table is NOT loaded into RAM; lookups binary-search via read.
 * Returns AKS_OK on success, AKS_ERR_* on failure.
 */
int akshara_init(akshara_ctx_t *ctx,
                aks_read_fn   read,    aks_blit_fn  blit,
                void         *read_ud, void         *blit_ud);

/*
 * Render a NUL-terminated UTF-8 string starting at pixel (x, y).
 * Returns x position after the last cluster.
 */
int16_t akshara_render(akshara_ctx_t *ctx, int16_t x, int16_t y,
                      const char *utf8);

/*
 * Measure a UTF-8 string without rendering.
 * Returns total advance width in pixels.
 */
int16_t akshara_measure(akshara_ctx_t *ctx, const char *utf8);

#ifdef __cplusplus
}
#endif

#endif /* AKSHAR_H */
