#ifndef AKS_INTERNAL_H
#define AKS_INTERNAL_H

#include "Akshara.h"
#include <stdbool.h>

/* ── Codepoint classifiers (shared by segmenter.c and blit.c) ────────────── */

static inline bool aks_is_consonant(uint32_t cp, const aks_rule_table_t *r)
{
    return cp >= r->consonant_start && cp <= r->consonant_end;
}

/*
 * Excludes virama explicitly: for Kannada, virama == vowel_sign_end, so the
 * coarse range would otherwise match it.
 */
static inline bool aks_is_vowel_sign(uint32_t cp, const aks_rule_table_t *r)
{
    return cp >= r->vowel_sign_start
        && cp <= r->vowel_sign_end
        && cp != r->virama;
}

static inline bool aks_is_modifier(uint32_t cp, const aks_rule_table_t *r)
{
    return cp >= r->modifier_start && cp <= r->modifier_end;
}

/*
 * Decode the next akshara cluster from *utf8.
 *
 * Advances *utf8 past the consumed bytes.
 * cluster[6] is filled with codepoints (zero-padded to 6 slots).
 *
 * Returns:
 *   1–6  : number of codepoints in the cluster
 *   0    : end of string
 *   AKS_ERR_INVALID_UTF8 : malformed UTF-8
 */
int aks_segment_next(const char **utf8, const aks_rule_table_t *rules,
                     uint32_t cluster[6]);

/*
 * Binary-search the cluster key table for the uint32_t cp[6] via ctx->read.
 * The on-disk key table stores uint16_t cp[6]; codepoints are BMP-only.
 *
 * Returns:
 *   AKS_OK            : hit; *out is filled with the matching aks_key_entry_t
 *   AKS_ERR_NOT_FOUND : miss (cluster not in table — OOV)
 *   AKS_ERR_IO        : read callback failed
 */
int aks_lookup(const akshara_ctx_t *ctx, const uint32_t cp[6],
               aks_key_entry_t *out);

/*
 * Load the size directory entry at index idx into *out.
 */
int aks_load_size_entry(const akshara_ctx_t *ctx, uint8_t idx,
                        aks_size_entry_t *out);

#endif /* AKS_INTERNAL_H */
