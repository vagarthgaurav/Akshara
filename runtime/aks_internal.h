#ifndef AKS_INTERNAL_H
#define AKS_INTERNAL_H

#include "akshar.h"

/*
 * Decode the next akshara cluster from *utf8.
 *
 * Advances *utf8 past the consumed bytes.
 * cluster[4] is filled with codepoints (zero-padded to 4 slots).
 *
 * Returns:
 *   1–4  : number of codepoints in the cluster
 *   0    : end of string
 *   AKS_ERR_INVALID_UTF8 : malformed UTF-8
 */
int aks_segment_next(const char **utf8, const aks_rule_table_t *rules,
                     uint32_t cluster[4]);

/*
 * Binary-search the cluster key table for cp[4] via ctx->read.
 *
 * Returns:
 *   AKS_OK  : hit; *out is filled with the matching entry
 *   1       : miss (cluster not in table — OOV)
 *   AKS_ERR_IO : read callback failed
 */
int aks_lookup(const akshar_ctx_t *ctx, const uint32_t cp[4],
               aks_key_entry_t *out);

#endif /* AKS_INTERNAL_H */
