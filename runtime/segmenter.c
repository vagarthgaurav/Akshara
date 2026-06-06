/*
 * segmenter.c — UTF-8 decoder and akshara cluster segmenter.
 *
 * The segmenter is a greedy left-to-right state machine driven entirely by
 * the rule table loaded from the .aks file.  Adding a new script requires
 * only a new .aks file; no code change here.
 *
 * Grammar (one cluster per call to aks_segment_next):
 *
 *   cluster = consonant (virama consonant)* vowel_sign? modifier?
 *           | any_other_codepoint           (single-codepoint cluster)
 *
 * The cluster array has 6 slots.  The segmenter stops absorbing conjunct
 * pairs once adding another pair would overflow the 6-slot limit, which is
 * equivalent to the key entry format constraint (aks_key_entry_t.cp[6]).
 * Depth-2 conjuncts + vowel sign fit in 6 slots; Devanagari depth-3 will
 * require a format bump to cp[8] (format v3) and a corresponding change here.
 *
 * For Kannada, virama equals vowel_sign_end (U+0CCD), so is_vowel_sign()
 * excludes it explicitly to prevent absorbing a terminal halant as a vowel
 * sign.  Tamil and Devanagari viramas fall outside their vowel_sign ranges,
 * so the exclusion is harmless but not required for those scripts.
 */

#include "aks_internal.h"
#include <string.h>

/* ── UTF-8 decoder ───────────────────────────────────────────────────────── */

/*
 * Decode one codepoint from *p, advancing *p past the consumed bytes.
 * Returns the codepoint (≥ 0), 0 at end of string, AKS_ERR_INVALID_UTF8 on
 * a bad byte sequence.
 */
static int32_t utf8_next(const char **p)
{
    const uint8_t *s = (const uint8_t *)*p;
    uint32_t cp;
    int len;

    if (*s == 0) return 0;

    if      ((*s & 0x80) == 0x00) { cp = *s & 0x7F; len = 1; }
    else if ((*s & 0xE0) == 0xC0) { cp = *s & 0x1F; len = 2; }
    else if ((*s & 0xF0) == 0xE0) { cp = *s & 0x0F; len = 3; }
    else if ((*s & 0xF8) == 0xF0) { cp = *s & 0x07; len = 4; }
    else return AKS_ERR_INVALID_UTF8;

    for (int i = 1; i < len; i++) {
        if ((s[i] & 0xC0) != 0x80) return AKS_ERR_INVALID_UTF8;
        cp = (cp << 6) | (s[i] & 0x3F);
    }

    *p += len;
    return (int32_t)cp;
}

/* Classifiers are defined as static inline in aks_internal.h. */
#define is_consonant  aks_is_consonant
#define is_vowel_sign aks_is_vowel_sign
#define is_modifier   aks_is_modifier

/* ── Public segmenter ────────────────────────────────────────────────────── */

int aks_segment_next(const char **utf8, const aks_rule_table_t *rules,
                     uint32_t cluster[6])
{
    memset(cluster, 0, 6 * sizeof(uint32_t));

    const char *p = *utf8;
    int32_t first = utf8_next(&p);

    if (first == 0)                    return 0;   /* end of string */
    if (first == AKS_ERR_INVALID_UTF8) return AKS_ERR_INVALID_UTF8;

    if (!is_consonant((uint32_t)first, rules)) {
        /* Independent vowel, digit, ASCII, punctuation — single codepoint. */
        cluster[0] = (uint32_t)first;
        *utf8 = p;
        return 1;
    }

    /* ── Consonant-headed cluster ─────────────────────────────────────── */
    int n = 0;
    cluster[n++] = (uint32_t)first;

    /* Greedily absorb (virama + consonant) pairs up to max_conjunct_depth.
     * Stop early if the next pair would fill past the 4-slot key limit. */
    int depth = 0;
    while (depth < (int)rules->max_conjunct_depth) {
        if (n + 2 > 6) break;  /* no room for virama + consonant */

        const char *save = p;

        int32_t v = utf8_next(&p);
        if (v != (int32_t)rules->virama) { p = save; break; }

        int32_t c2 = utf8_next(&p);
        if (c2 <= 0 || !is_consonant((uint32_t)c2, rules)) {
            /* virama not followed by a consonant — not a conjunct bond. */
            p = save;
            break;
        }

        cluster[n++] = (uint32_t)v;
        cluster[n++] = (uint32_t)c2;
        depth++;
    }

    /* Terminal virama (halant / explicit virama form): absorb and emit.
     * Only when depth < max_conjunct_depth; if we have reached the depth
     * limit the spec says to emit the current cluster and leave the virama
     * to become its own single-codepoint cluster on the next call. */
    if (n < 6 && depth < (int)rules->max_conjunct_depth) {
        const char *save = p;
        int32_t v = utf8_next(&p);
        if (v == (int32_t)rules->virama) {
            cluster[n++] = (uint32_t)v;
            *utf8 = p;
            return n;
        }
        p = save;
    }

    /* Optional dependent vowel sign. */
    if (n < 6) {
        const char *save = p;
        int32_t vs = utf8_next(&p);
        if (vs > 0 && is_vowel_sign((uint32_t)vs, rules)) {
            cluster[n++] = (uint32_t)vs;
        } else {
            p = save;
        }
    }

    /* Optional modifier (anusvara, visarga, chandrabindu). */
    if (n < 6) {
        const char *save = p;
        int32_t mod = utf8_next(&p);
        if (mod > 0 && is_modifier((uint32_t)mod, rules)) {
            cluster[n++] = (uint32_t)mod;
        } else {
            p = save;
        }
    }

    *utf8 = p;
    return n;
}
