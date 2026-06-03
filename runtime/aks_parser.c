/*
 * aks_parser.c — header and rule table parsing; implements akshar_init().
 *
 * Reads 28-byte header + 32-byte rule table via the read callback.
 * The cluster key table is NOT loaded into RAM; it stays in the .aks file
 * and is accessed on demand by aks_lookup().
 */

#include "aks_internal.h"
#include <string.h>

#define AKS_MAGIC   0x56414741u  /* "VAGA" little-endian */
#define AKS_VERSION 1u

static bool is_known_script(uint8_t id)
{
    return id >= AKS_SCRIPT_KANNADA && id <= AKS_SCRIPT_MALAYALAM;
}

int akshar_init(akshar_ctx_t *ctx,
                aks_read_fn   read,    aks_blit_fn  blit,
                void         *read_ud, void         *blit_ud)
{
    if (!ctx || !read || !blit)
        return AKS_ERR_NULL_ARG;

    ctx->read    = read;
    ctx->read_ud = read_ud;
    ctx->blit    = blit;
    ctx->blit_ud = blit_ud;

    if (read(0, (uint8_t *)&ctx->_hdr, sizeof(aks_header_t), read_ud) != 0)
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
    uint32_t expected_rule   = (uint32_t)sizeof(aks_header_t);
    uint32_t expected_lookup = expected_rule + (uint32_t)sizeof(aks_rule_table_t);
    uint32_t expected_bitmap = expected_lookup +
                               ctx->_hdr.cluster_count * (uint32_t)sizeof(aks_key_entry_t);

    if (ctx->_hdr.rule_offset   != expected_rule   ||
        ctx->_hdr.lookup_offset != expected_lookup ||
        ctx->_hdr.bitmap_offset != expected_bitmap)
        return AKS_ERR_TRUNCATED;

    if (read(ctx->_hdr.rule_offset, (uint8_t *)&ctx->_rules,
             sizeof(aks_rule_table_t), read_ud) != 0)
        return AKS_ERR_IO;

    return AKS_OK;
}
