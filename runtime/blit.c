/*
 * blit.c — layout engine, blit dispatcher, and OOV fallback.
 *
 * Implements akshara_render() and akshara_measure().
 *
 * v3 per-cluster flow (render):
 *   segment → lookup → read comp header → for each glyph:
 *     read comp entry → read glyph metrics → read glyph bitmap
 *     → compute exact screen position → call ctx->blit
 *   → advance pen by sum of HarfBuzz advances
 *
 * The blit callback is called once per glyph (not once per cluster as in v2).
 * (x, y) passed to blit is the exact top-left of the content bitmap.
 *
 * HarfBuzz positions are stored in design units; scaled to pixels at runtime:
 *   pixels = (int16_t)((int32_t)du * size_px / upem)
 *
 * OOV fallback: cluster not in key table → try each codepoint individually,
 * pairing consonant + vowel_sign/modifier where the pair is in the table.
 *
 * akshara_measure follows the same segment/lookup path but skips all I/O
 * and blit; it sums advances and returns the final pen x.
 */

#include "aks_internal.h"
#include <string.h>

/*
 * Per-glyph bitmap scratch.  Max single-glyph bitmap at 24px 2bpp:
 * ~24px × 30px = 180 bytes (4bpp round-up).  512 covers all sizes with room.
 * MCUs with very tight stacks can reduce this if fonts stay small.
 */
#define GLYPH_SCRATCH_BYTES 512u

/* Max glyphs per cluster composition block (depth-2 conjunct + marks). */
#define AKS_MAX_COMP_DEPTH 8

/* Scale design units to pixels: truncate toward zero ((int32_t)du * size_px / upem). */
static int16_t du_to_px(int16_t du, uint16_t size_px, uint16_t upem)
{
    if (upem == 0) return 0;
    return (int16_t)((int32_t)du * (int32_t)size_px / (int32_t)upem);
}

/* Row stride in bytes for a bitmap of width w at bpp. */
static uint32_t row_stride(uint16_t w, uint8_t bpp)
{
    if (bpp == 0 || w == 0) return 0;
    uint32_t ppb = (uint32_t)(8u / bpp);
    return ((uint32_t)w + ppb - 1u) / ppb;
}

/*
 * Blit or measure all glyphs in a cluster composition block.
 *
 * comp_off : byte offset from file's comp_offset to this cluster's block.
 * do_blit  : if false, skip all I/O for bitmaps and skip ctx->blit calls.
 *            Used by akshara_measure().
 *
 * Returns the cluster's total advance in pixels (added to pen x by caller).
 */
static int16_t render_comp(akshara_ctx_t *ctx,
                            int16_t x, int16_t y,
                            uint32_t comp_off,
                            bool do_blit)
{
    const aks_size_entry_t *sz = &ctx->_size;

    /* Read composition block header: glyph_count + pad (2 bytes). */
    uint8_t chdr[2];
    uint32_t abs_comp = ctx->_hdr.comp_offset + comp_off;
    if (ctx->read(abs_comp, chdr, 2u, ctx->read_ud) != 0)
        return (int16_t)0;

    uint8_t glyph_count = chdr[0];
    if (glyph_count > AKS_MAX_COMP_DEPTH)
        glyph_count = AKS_MAX_COMP_DEPTH;  /* safety clamp */

    int32_t pen_x = 0;

    for (uint8_t i = 0; i < glyph_count; i++) {
        /* Read one comp entry (8 bytes). */
        aks_comp_entry_t ce = {0};
        uint32_t ce_off = abs_comp + 2u + (uint32_t)i * (uint32_t)sizeof(aks_comp_entry_t);
        if (ctx->read(ce_off, (uint8_t *)&ce, sizeof(ce), ctx->read_ud) != 0)
            goto advance;

        /* Reject out-of-range glyph index from a corrupt composition table. */
        if (ce.glyph_idx >= sz->glyph_count)
            goto advance;

        if (do_blit) {
            /* Read glyph metrics (4 bytes). */
            aks_glyph_metrics_t gm;
            uint32_t moff = sz->metrics_offset +
                            (uint32_t)ce.glyph_idx * (uint32_t)sizeof(aks_glyph_metrics_t);
            if (ctx->read(moff, (uint8_t *)&gm, sizeof(gm), ctx->read_ud) != 0)
                goto advance;

            /* Skip invisible glyphs (e.g. space). */
            if (gm.width == 0 || gm.height == 0)
                goto advance;

            /* Read glyph bitmap offset from per-size offset table. */
            uint32_t bmap_rel;
            uint32_t ooff = sz->offsets_offset +
                            (uint32_t)ce.glyph_idx * (uint32_t)sizeof(uint32_t);
            if (ctx->read(ooff, (uint8_t *)&bmap_rel, sizeof(bmap_rel),
                          ctx->read_ud) != 0)
                goto advance;

            uint32_t nbytes = row_stride(gm.width, sz->bpp) * (uint32_t)gm.height;
            if (nbytes == 0 || nbytes > GLYPH_SCRATCH_BYTES)
                goto advance;

            uint8_t scratch[GLYPH_SCRATCH_BYTES];
            if (ctx->read(sz->bitmaps_offset + bmap_rel, scratch, nbytes,
                          ctx->read_ud) != 0)
                goto advance;

            /* Compute exact screen position.
             *
             * blit_x = x + pen_x + hb_x_offset_px + bearing_x
             * blit_y = y + baseline - top_from_base - hb_y_offset_px
             *
             * hb offsets are in design units; scale to pixels here.
             * bearing_x is FreeType bitmap_left (pen → left edge of bitmap).
             * top_from_base is FreeType bitmap_top (rows above baseline).
             * hb_y_off is positive = up (HarfBuzz convention); subtract for screen y.
             */
            int16_t hb_x_px = du_to_px(ce.hb_x_off, sz->size_px, sz->upem);
            int16_t hb_y_px = du_to_px(ce.hb_y_off, sz->size_px, sz->upem);
            int32_t blit_x  = (int32_t)x + pen_x + (int32_t)hb_x_px
                              + (int32_t)(int8_t)gm.bearing_x;
            int32_t blit_y  = (int32_t)y + (int32_t)sz->baseline
                              - (int32_t)(int8_t)gm.top_from_base
                              - (int32_t)hb_y_px;

            ctx->blit((int16_t)blit_x, (int16_t)blit_y, scratch,
                      gm.width, gm.height, sz->bpp, ctx->blit_ud);
        }

advance:
        pen_x += (int32_t)((uint32_t)ce.hb_advance * sz->size_px / sz->upem);
    }

    return (int16_t)pen_x;
}

/*
 * OOV fallback: try to render each codepoint in the cluster individually.
 *
 * A consonant immediately followed by a vowel sign or modifier is tried as a
 * two-codepoint pair first — standalone vowel signs have no .aks entry, only
 * consonant+sign pairs do.  This preserves the vowel sign on the second
 * consonant of an OOV conjunct (e.g. ಸ್ಕಾ falls back to ಸ + ್ + ಕಾ).
 * If the pair is also absent, both codepoints fall through to single lookups.
 */
static int32_t oov_fallback(akshara_ctx_t *ctx, int32_t x, int16_t y,
                             const uint32_t cluster[6], bool do_blit)
{
    const aks_rule_table_t *r = &ctx->_rules;

    for (int i = 0; i < 6 && cluster[i] != 0; i++) {
        uint32_t cp = cluster[i];
        aks_key_entry_t e;

        if (aks_is_consonant(cp, r) && i + 1 < 6 && cluster[i + 1] != 0 &&
            (aks_is_vowel_sign(cluster[i + 1], r) ||
             aks_is_modifier(cluster[i + 1], r))) {
            uint32_t pair[6] = {cp, cluster[i + 1], 0u, 0u, 0u, 0u};
            if (aks_lookup(ctx, pair, &e) == AKS_OK) {
                x += render_comp(ctx, (int16_t)x, y, e.comp_off, do_blit);
                i++;  /* sign was consumed by the pair */
                continue;
            }
        }

        uint32_t single[6] = {cp, 0u, 0u, 0u, 0u, 0u};
        if (aks_lookup(ctx, single, &e) == AKS_OK)
            x += render_comp(ctx, (int16_t)x, y, e.comp_off, do_blit);
        /* miss: skip silently — never show a missing-glyph box */
    }
    return x;
}

/* ── Public API ──────────────────────────────────────────────────────────── */

int16_t akshara_render(akshara_ctx_t *ctx, int16_t x, int16_t y,
                      const char *utf8)
{
    if (!ctx || !utf8) return x;

    int32_t x_acc = (int32_t)x;
    const char *p = utf8;
    uint32_t cluster[6];
    int n;

    while ((n = aks_segment_next(&p, &ctx->_rules, cluster)) != 0) {
        if (n < 0) break;  /* malformed UTF-8 — stop silently */
        aks_key_entry_t e;
        if (aks_lookup(ctx, cluster, &e) == AKS_OK)
            x_acc += render_comp(ctx, (int16_t)x_acc, y, e.comp_off, true);
        else
            x_acc = oov_fallback(ctx, x_acc, y, cluster, true);
    }

    return (int16_t)x_acc;
}

int16_t akshara_measure(akshara_ctx_t *ctx, const char *utf8)
{
    if (!ctx || !utf8) return 0;

    const char *p = utf8;
    uint32_t cluster[6];
    int32_t x_acc = 0;
    int n;

    while ((n = aks_segment_next(&p, &ctx->_rules, cluster)) != 0) {
        if (n < 0) break;  /* malformed UTF-8 */
        aks_key_entry_t e;
        if (aks_lookup(ctx, cluster, &e) == AKS_OK)
            x_acc += render_comp(ctx, (int16_t)x_acc, 0, e.comp_off, false);
        else
            x_acc = oov_fallback(ctx, x_acc, 0, cluster, false);
    }

    return (int16_t)x_acc;
}
