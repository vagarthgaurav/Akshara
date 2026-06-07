/*
 * aks_parser.c — header and rule table parsing; implements akshara_init().
 *
 * Reads 28-byte header + 32-byte rule table via the read callback.
 * The cluster key table is NOT loaded into RAM; it stays in the .aks file
 * and is accessed on demand by aks_lookup().
 */

#include "aks_internal.h"
#include <string.h>

#define AKS_MAGIC 0x414B5348u /* "AKSH" */
#define AKS_VERSION 2u

static int aks_read_from_ptr(uint32_t offset, uint8_t *buf,
                             uint32_t size, void *ud)
{
    memcpy(buf, (const uint8_t *)ud + offset, size);
    return AKS_OK;
}

static bool is_known_script(uint8_t id)
{
    return id >= AKS_SCRIPT_KANNADA && id <= AKS_SCRIPT_MALAYALAM;
}

/* Shared by akshara_init and akshara_set_font. Caller must have set ctx->read / read_ud. */
static int aks_load_font(akshara_ctx_t *ctx)
{
    if (ctx->read(0, (uint8_t *)&ctx->_hdr, sizeof(aks_header_t), ctx->read_ud) != 0)
        return AKS_ERR_IO;

    if (ctx->_hdr.magic != AKS_MAGIC)
        return AKS_ERR_BAD_MAGIC;

    if (ctx->_hdr.version != AKS_VERSION)
        return AKS_ERR_BAD_VERSION;

    if (!is_known_script(ctx->_hdr.script_id))
        return AKS_ERR_BAD_SCRIPT;

    /*
     * Validate section offsets are internally consistent.
     * The packer always writes: rule immediately after header, lookup
     * immediately after rule, bitmap immediately after the key table.
     * Any deviation means a malformed or truncated file.
     */
    uint32_t expected_rule = (uint32_t)sizeof(aks_header_t);
    uint32_t expected_lookup = expected_rule + (uint32_t)sizeof(aks_rule_table_t);
    uint32_t expected_bitmap = expected_lookup +
                               ctx->_hdr.cluster_count * (uint32_t)sizeof(aks_key_entry_t);

    if (ctx->_hdr.rule_offset != expected_rule ||
        ctx->_hdr.lookup_offset != expected_lookup ||
        ctx->_hdr.bitmap_offset != expected_bitmap)
        return AKS_ERR_TRUNCATED;

    if (ctx->read(ctx->_hdr.rule_offset, (uint8_t *)&ctx->_rules,
                  sizeof(aks_rule_table_t), ctx->read_ud) != 0)
        return AKS_ERR_IO;

    return AKS_OK;
}

int akshara_init(akshara_ctx_t *ctx,
                 aks_read_fn read, aks_blit_fn blit,
                 void *read_ud, void *blit_ud)
{
    if (!ctx || !blit)
        return AKS_ERR_NULL_ARG;
    if (!read && !read_ud)
        return AKS_ERR_NULL_ARG;

    /* NULL read means font_data is a const array in addressable memory (e.g. flash). */
    ctx->read = read ? read : aks_read_from_ptr;
    ctx->read_ud = read_ud;
    ctx->blit = blit;
    ctx->blit_ud = blit_ud;

    return aks_load_font(ctx);
}

int akshara_set_font(akshara_ctx_t *ctx, aks_read_fn read, void *read_ud)
{
    if (!ctx)
        return AKS_ERR_NULL_ARG;
    if (!read && !read_ud)
        return AKS_ERR_NULL_ARG;

    ctx->read = read ? read : aks_read_from_ptr;
    ctx->read_ud = read_ud;

    return aks_load_font(ctx);
}
