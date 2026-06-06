/*
 * lookup.c — binary search over the sorted cluster key table.
 *
 * The key table is never loaded into RAM.  Each binary search step reads
 * one 32-byte aks_key_entry_t from the .aks file via ctx->read.
 * For 1317 clusters this is at most ceil(log2(1317)) = 11 reads per lookup.
 * For flash-backed fonts (read_flash = memcpy) each read is essentially free.
 */

#include "aks_internal.h"
#include <string.h>

/* Lexicographic comparison of two uint32_t[6] codepoint arrays. */
static int cp6_cmp(const uint32_t a[6], const uint32_t b[6])
{
    for (int i = 0; i < 6; i++) {
        if (a[i] < b[i]) return -1;
        if (a[i] > b[i]) return  1;
    }
    return 0;
}

int aks_lookup(const akshara_ctx_t *ctx, const uint32_t cp[6],
               aks_key_entry_t *out)
{
    if (ctx->_hdr.cluster_count == 0)
        return 1;  /* empty table — miss */

    uint32_t lo = 0;
    uint32_t hi = ctx->_hdr.cluster_count - 1;

    while (lo <= hi) {
        uint32_t mid = lo + (hi - lo) / 2;
        uint32_t off = ctx->_hdr.lookup_offset +
                       mid * (uint32_t)sizeof(aks_key_entry_t);

        if (ctx->read(off, (uint8_t *)out, sizeof(aks_key_entry_t),
                      ctx->read_ud) != 0)
            return AKS_ERR_IO;

        uint32_t entry_cp[6];
        memcpy(entry_cp, out->cp, sizeof(entry_cp));
        int cmp = cp6_cmp(entry_cp, cp);
        if (cmp == 0) return AKS_OK;
        if (cmp < 0) {
            lo = mid + 1;
        } else {
            if (mid == 0) break;  /* guard against uint32_t underflow */
            hi = mid - 1;
        }
    }

    return 1;  /* miss */
}
