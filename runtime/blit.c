/*
 * blit.c — layout engine, blit dispatcher, and OOV fallback.
 *
 * Implements akshar_render() and akshar_measure().
 *
 * Per-cluster flow (render):
 *   segment → lookup → read bitmap into stack scratch → blit callback → advance pen
 *
 * OOV fallback: cluster not in key table → try each codepoint individually.
 * If a single codepoint is also missing, skip it silently (never show a
 * missing-glyph box).
 *
 * akshar_measure follows the same segment/lookup path but skips all I/O and
 * blit; it sums advances and returns the final pen x.
 */

#include "aks_internal.h"
#include <string.h>

/*
 * Conservative stack scratch ceiling.  At 24px 2bpp a wide conjunct is
 * ~48px × 28px = 336 bytes.  2048 covers 64px height at 2bpp with room to
 * spare; MCUs with very tight stacks can reduce this constant.
 */
#define BITMAP_SCRATCH_BYTES 2048u

/* Row stride in bytes for a bitmap of width w at bpp (each row byte-aligned). */
static uint32_t row_stride(uint16_t w, uint8_t bpp)
{
    if (bpp == 0) return 0;
    uint32_t ppb = (uint32_t)(8u / bpp);  /* pixels per byte: 8 at 1bpp, 4 at 2bpp */
    return ((uint32_t)w + ppb - 1u) / ppb;
}

static uint32_t bitmap_nbytes(uint16_t w, uint16_t h, uint8_t bpp)
{
    return row_stride(w, bpp) * (uint32_t)h;
}

/*
 * Blit one cluster entry at pen position x, y.
 *
 * Reads the packed bitmap from the .aks file into a stack scratch buffer,
 * then calls ctx->blit.  The glyph is positioned at x + bearing_x so the
 * pen position itself is always the nominal advance origin.
 *
 * Returns new pen x (= x + entry->advance) even on I/O error, so the caller
 * always advances and does not stall rendering.
 */
static int16_t blit_entry(akshar_ctx_t *ctx, int16_t x, int16_t y,
                           const aks_key_entry_t *e)
{
    uint32_t nbytes = bitmap_nbytes(e->width, ctx->_hdr.glyph_height,
                                    ctx->_hdr.bpp);

    if (nbytes == 0 || nbytes > BITMAP_SCRATCH_BYTES)
        goto advance;

    {
        uint8_t scratch[BITMAP_SCRATCH_BYTES];
        uint32_t abs_off = ctx->_hdr.bitmap_offset + e->bitmap_off;

        if (ctx->read(abs_off, scratch, nbytes, ctx->read_ud) != 0)
            goto advance;

        /* bearing_x is stored as uint8_t but interpreted as signed. */
        int16_t blit_x = (int16_t)(x + (int8_t)e->bearing_x);
        ctx->blit(blit_x, y, scratch, e->width, ctx->_hdr.glyph_height,
                  ctx->_hdr.bpp, ctx->blit_ud);
    }

advance:
    return (int16_t)(x + e->advance);
}

/*
 * OOV fallback: try to render each codepoint in the cluster individually.
 * Codepoints whose single-codepoint key is also absent are skipped silently.
 */
static int16_t blit_oov(akshar_ctx_t *ctx, int16_t x, int16_t y,
                         const uint32_t cluster[4])
{
    for (int i = 0; i < 4 && cluster[i] != 0; i++) {
        uint32_t single[4] = {cluster[i], 0u, 0u, 0u};
        aks_key_entry_t e;
        if (aks_lookup(ctx, single, &e) == AKS_OK)
            x = blit_entry(ctx, x, y, &e);
        /* miss or I/O error: skip silently */
    }
    return x;
}

/* OOV measure: sum advances of any individual codepoints that are in-table. */
static int16_t measure_oov(akshar_ctx_t *ctx, int16_t x,
                            const uint32_t cluster[4])
{
    for (int i = 0; i < 4 && cluster[i] != 0; i++) {
        uint32_t single[4] = {cluster[i], 0u, 0u, 0u};
        aks_key_entry_t e;
        if (aks_lookup(ctx, single, &e) == AKS_OK)
            x = (int16_t)(x + e.advance);
    }
    return x;
}

/* ── Public API ──────────────────────────────────────────────────────────── */

int16_t akshar_render(akshar_ctx_t *ctx, int16_t x, int16_t y,
                      const char *utf8)
{
    if (!ctx || !utf8) return x;

    const char *p = utf8;
    uint32_t cluster[4];
    int n;

    while ((n = aks_segment_next(&p, &ctx->_rules, cluster)) > 0) {
        aks_key_entry_t e;
        if (aks_lookup(ctx, cluster, &e) == AKS_OK)
            x = blit_entry(ctx, x, y, &e);
        else
            x = blit_oov(ctx, x, y, cluster);
    }

    return x;
}

int16_t akshar_measure(akshar_ctx_t *ctx, const char *utf8)
{
    if (!ctx || !utf8) return 0;

    const char *p = utf8;
    uint32_t cluster[4];
    int16_t x = 0;
    int n;

    while ((n = aks_segment_next(&p, &ctx->_rules, cluster)) > 0) {
        aks_key_entry_t e;
        if (aks_lookup(ctx, cluster, &e) == AKS_OK)
            x = (int16_t)(x + e.advance);
        else
            x = measure_oov(ctx, x, cluster);
    }

    return x;
}
