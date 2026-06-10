/*
 * aks_parser.c — header and rule table parsing; implements akshara_init(),
 *                akshara_set_font(), and akshara_select_size().
 *
 * On init: reads the 28-byte v3 header, validates it, reads the 32-byte rule
 * table, then loads the first size+weight entry as the active size.
 *
 * The cluster key table, composition table, and bitmap stores stay in the
 * .aks file and are accessed on demand via aks_lookup() and blit.c.
 */

#include "aks_internal.h"
#include <string.h>

#define AKS_MAGIC   0x414B5348u  /* "AKSH" */
#define AKS_VERSION 3u

static int aks_read_from_ptr(uint32_t offset, uint8_t *buf,
                             uint32_t size, void *ud)
{
    memcpy(buf, (const uint8_t *)ud + offset, size);
    return AKS_OK;
}

static bool is_known_script(uint8_t id)
{
    return id >= AKS_SCRIPT_KANNADA && id <= AKS_SCRIPT_GUJARATI;
}

int aks_load_size_entry(const akshara_ctx_t *ctx, uint8_t idx,
                        aks_size_entry_t *out)
{
    uint32_t off = ctx->_hdr.sizes_offset +
                   (uint32_t)idx * (uint32_t)sizeof(aks_size_entry_t);
    if (ctx->read(off, (uint8_t *)out, sizeof(aks_size_entry_t),
                  ctx->read_ud) != 0)
        return AKS_ERR_IO;
    return AKS_OK;
}

static int aks_load_font(akshara_ctx_t *ctx)
{
    if (ctx->read(0, (uint8_t *)&ctx->_hdr, sizeof(aks_header_t),
                  ctx->read_ud) != 0)
        return AKS_ERR_IO;

    if (ctx->_hdr.magic != AKS_MAGIC)
        return AKS_ERR_BAD_MAGIC;
    if (ctx->_hdr.version != AKS_VERSION)
        return AKS_ERR_BAD_VERSION;
    if (!is_known_script(ctx->_hdr.script_id))
        return AKS_ERR_BAD_SCRIPT;
    if (ctx->_hdr.size_count == 0)
        return AKS_ERR_TRUNCATED;

    /* Validate that declared section offsets are internally consistent. */
    uint32_t expected_rule   = (uint32_t)sizeof(aks_header_t);
    uint32_t expected_lookup = expected_rule + (uint32_t)sizeof(aks_rule_table_t);
    uint32_t expected_comp   = expected_lookup +
                               ctx->_hdr.cluster_count *
                               (uint32_t)sizeof(aks_key_entry_t);

    if (ctx->_hdr.rule_offset   != expected_rule   ||
        ctx->_hdr.lookup_offset != expected_lookup  ||
        ctx->_hdr.comp_offset   != expected_comp)
        return AKS_ERR_TRUNCATED;

    if (ctx->read(ctx->_hdr.rule_offset, (uint8_t *)&ctx->_rules,
                  sizeof(aks_rule_table_t), ctx->read_ud) != 0)
        return AKS_ERR_IO;

    /* Default to the first size+weight entry. */
    return aks_load_size_entry(ctx, 0, &ctx->_size);
}

int akshara_init(akshara_ctx_t *ctx,
                 aks_read_fn read, aks_blit_fn blit,
                 void *read_ud, void *blit_ud)
{
    if (!ctx || !blit)
        return AKS_ERR_NULL_ARG;
    if (!read && !read_ud)
        return AKS_ERR_NULL_ARG;

    ctx->read    = read ? read : aks_read_from_ptr;
    ctx->read_ud = read_ud;
    ctx->blit    = blit;
    ctx->blit_ud = blit_ud;

    return aks_load_font(ctx);
}

int akshara_set_font(akshara_ctx_t *ctx, aks_read_fn read, void *read_ud)
{
    if (!ctx)
        return AKS_ERR_NULL_ARG;
    if (!read && !read_ud)
        return AKS_ERR_NULL_ARG;

    ctx->read    = read ? read : aks_read_from_ptr;
    ctx->read_ud = read_ud;

    return aks_load_font(ctx);
}

int akshara_get_sizes(akshara_ctx_t *ctx,
                      aks_size_info_t *out_sizes, uint8_t max_count)
{
    if (!ctx || !out_sizes)
        return AKS_ERR_NULL_ARG;

    uint8_t n = ctx->_hdr.size_count < max_count
                    ? ctx->_hdr.size_count : max_count;
    for (uint8_t i = 0; i < n; i++) {
        aks_size_entry_t e;
        if (aks_load_size_entry(ctx, i, &e) != AKS_OK)
            return AKS_ERR_IO;
        out_sizes[i].size_px = e.size_px;
        out_sizes[i].weight  = e.weight;
    }
    return (int)n;
}

int akshara_select_size(akshara_ctx_t *ctx, uint8_t size_px, uint8_t weight)
{
    if (!ctx)
        return AKS_ERR_NULL_ARG;

    for (uint8_t i = 0; i < ctx->_hdr.size_count; i++) {
        aks_size_entry_t e;
        if (aks_load_size_entry(ctx, i, &e) != AKS_OK)
            return AKS_ERR_IO;
        if (e.size_px == size_px && e.weight == weight) {
            ctx->_size = e;
            return AKS_OK;
        }
    }
    return AKS_ERR_NOT_FOUND;
}
