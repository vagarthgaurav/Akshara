/*
 * lookup.c — binary search over the sorted cluster key table.
 *
 * The key table is never loaded into RAM.  Each step reads one 16-byte
 * aks_key_entry_t via ctx->read.  For 1424 clusters: ceil(log2(1424)) = 11
 * reads per lookup.  For flash-baked fonts (read = memcpy) each read is free.
 *
 * Key table format (v3): sorted uint16_t cp[6] + uint32_t comp_off.
 * All Indic codepoints are BMP (≤ U+FFFF), so uint16_t is sufficient.
 * The segmenter produces uint32_t cp[6]; we compare against uint16_t on-disk.
 */

#include "aks_internal.h"
#include <string.h>

/*
 * Compare a uint32_t[6] key (from segmenter) against a uint16_t[6] entry
 * (from the file).  Lexicographic comparison.
 */
static int cp6_cmp(const uint32_t key[6], const uint16_t entry[6])
{
    for (int i = 0; i < 6; i++) {
        uint32_t a = key[i];
        uint32_t b = (uint32_t)entry[i];
        if (a < b) return -1;
        if (a > b) return  1;
    }
    return 0;
}

int aks_lookup(const akshara_ctx_t *ctx, const uint32_t cp[6],
               aks_key_entry_t *out)
{
    if (ctx->_hdr.cluster_count == 0)
        return AKS_ERR_NOT_FOUND;  /* empty table — miss */

    uint32_t lo = 0;
    uint32_t hi = ctx->_hdr.cluster_count - 1;

    while (lo <= hi) {
        uint32_t mid = lo + (hi - lo) / 2;
        uint32_t off = ctx->_hdr.lookup_offset +
                       mid * (uint32_t)sizeof(aks_key_entry_t);

        if (ctx->read(off, (uint8_t *)out, sizeof(aks_key_entry_t),
                      ctx->read_ud) != 0)
            return AKS_ERR_IO;

        /* Copy cp[] out of the packed struct before passing by pointer so that
         * the comparison is safe on architectures that forbid unaligned reads. */
        uint16_t disk_cp[6];
        memcpy(disk_cp, out->cp, sizeof(disk_cp));
        int cmp = cp6_cmp(cp, disk_cp);
        if (cmp == 0) return AKS_OK;
        if (cmp > 0) {
            lo = mid + 1;
        } else {
            if (mid == 0) break;  /* guard against uint32_t underflow */
            hi = mid - 1;
        }
    }

    return AKS_ERR_NOT_FOUND;  /* miss */
}
