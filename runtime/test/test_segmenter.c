/*
 * test_segmenter.c — C unit tests for aks_segment_next().
 *
 * Tests mirror the Python TestSegmenter suite in host/test/render_png.py so
 * that the C segmenter and the Python reference produce identical clusters
 * for every covered input.
 *
 * Compile and run via runtime/test/Makefile.
 *
 * Kannada rule table values are hardcoded from host/scripts/kannada.py and
 * match the aks_rule_table_t written into every Kannada .aks file.
 */

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

/* Pull in the segmenter under test directly. */
#include "../aks_internal.h"

/* ── Hardcoded Kannada rule table (matches packer output) ────────────────── */

static const aks_rule_table_t KANNADA = {
    .consonant_start    = 0x0C95,  /* KA */
    .consonant_end      = 0x0CB9,  /* HA */
    .virama             = 0x0CCD,  /* KANNADA SIGN VIRAMA */
    .vowel_sign_start   = 0x0CBE,  /* AA-sign; coarse range includes virama */
    .vowel_sign_end     = 0x0CCD,
    .modifier_start     = 0x0C82,  /* ANUSVARA */
    .modifier_end       = 0x0C83,  /* VISARGA */
    .max_conjunct_depth = 2,
    ._reserved          = {0, 0, 0},
};

/* ── Test harness ─────────────────────────────────────────────────────────── */

static int pass_count = 0;
static int fail_count = 0;

#define CHECK(expr) do { \
    if (!(expr)) { \
        printf("  FAIL  %s:%d  %s\n", __FILE__, __LINE__, #expr); \
        fail_count++; \
    } else { \
        pass_count++; \
    } \
} while (0)

/* Segment the entire string and return all clusters in out[].
 * Returns the number of clusters produced, or -1 on UTF-8 error. */
static int segment_all(const char *utf8, const aks_rule_table_t *rules,
                        uint32_t out[][6], int max_clusters)
{
    int n = 0;
    while (*utf8 && n < max_clusters) {
        int rc = aks_segment_next(&utf8, rules, out[n]);
        if (rc < 0) return -1;
        if (rc == 0) break;
        n++;
    }
    return n;
}

/* Check that a cluster array exactly matches an expected sequence. */
static bool cluster_eq(const uint32_t got[6], const uint32_t *want, int want_len)
{
    for (int i = 0; i < 6; i++) {
        uint32_t expected = (i < want_len) ? want[i] : 0;
        if (got[i] != expected) return false;
    }
    return true;
}

/* ── Individual tests ────────────────────────────────────────────────────── */

static void test_bare_consonant(void)
{
    /* ಕ  → {KA} */
    uint32_t clusters[8][6];
    int n = segment_all("ಕ", &KANNADA, clusters, 8);
    CHECK(n == 1);
    uint32_t want[] = {0x0C95};
    CHECK(cluster_eq(clusters[0], want, 1));
}

static void test_consonant_vowel_sign(void)
{
    /* ಕಾ  → {KA, AA-sign} */
    uint32_t clusters[8][6];
    int n = segment_all("ಕಾ", &KANNADA, clusters, 8);
    CHECK(n == 1);
    uint32_t want[] = {0x0C95, 0x0CBE};
    CHECK(cluster_eq(clusters[0], want, 2));
}

static void test_conjunct(void)
{
    /* ಕ್ತ  → {KA, VIRAMA, TA} */
    uint32_t clusters[8][6];
    int n = segment_all("ಕ್ತ", &KANNADA, clusters, 8);
    CHECK(n == 1);
    uint32_t want[] = {0x0C95, 0x0CCD, 0x0CA4};
    CHECK(cluster_eq(clusters[0], want, 3));
}

static void test_conjunct_with_vowel(void)
{
    /* ಕ್ತಾ  → {KA, VIRAMA, TA, AA-sign} — fills all 4 slots */
    uint32_t clusters[8][6];
    int n = segment_all("ಕ್ತಾ", &KANNADA, clusters, 8);
    CHECK(n == 1);
    uint32_t want[] = {0x0C95, 0x0CCD, 0x0CA4, 0x0CBE};
    CHECK(cluster_eq(clusters[0], want, 4));
}

static void test_modifier(void)
{
    /* ಕಂ  → {KA, ANUSVARA} */
    uint32_t clusters[8][6];
    int n = segment_all("ಕಂ", &KANNADA, clusters, 8);
    CHECK(n == 1);
    uint32_t want[] = {0x0C95, 0x0C82};
    CHECK(cluster_eq(clusters[0], want, 2));
}

static void test_visarga(void)
{
    /* ಕಃ  → {KA, VISARGA} */
    uint32_t clusters[8][6];
    int n = segment_all("ಕಃ", &KANNADA, clusters, 8);
    CHECK(n == 1);
    uint32_t want[] = {0x0C95, 0x0C83};
    CHECK(cluster_eq(clusters[0], want, 2));
}

static void test_halant_form(void)
{
    /* ಕ್  → {KA, VIRAMA}  (halant / explicit virama) */
    uint32_t clusters[8][6];
    int n = segment_all("ಕ್", &KANNADA, clusters, 8);
    CHECK(n == 1);
    uint32_t want[] = {0x0C95, 0x0CCD};
    CHECK(cluster_eq(clusters[0], want, 2));
}

static void test_independent_vowel(void)
{
    /* ಅ  → {0x0C85}  (independent vowel, not in consonant range) */
    uint32_t clusters[8][6];
    int n = segment_all("ಅ", &KANNADA, clusters, 8);
    CHECK(n == 1);
    uint32_t want[] = {0x0C85};
    CHECK(cluster_eq(clusters[0], want, 1));
}

static void test_multi_cluster_word(void)
{
    /* ಕನ್ನಡ  → {KA} {NA,VIR,NA} {DA}  (the word "Kannada") */
    uint32_t clusters[8][6];
    int n = segment_all("ಕನ್ನಡ", &KANNADA, clusters, 8);
    CHECK(n == 3);

    uint32_t w0[] = {0x0C95};
    uint32_t w1[] = {0x0CA8, 0x0CCD, 0x0CA8};
    uint32_t w2[] = {0x0CA1};
    CHECK(cluster_eq(clusters[0], w0, 1));
    CHECK(cluster_eq(clusters[1], w1, 3));
    CHECK(cluster_eq(clusters[2], w2, 1));
}

static void test_ascii_passthrough(void)
{
    /* ASCII bytes are single-codepoint clusters (0x61, 0x62, 0x63). */
    uint32_t clusters[8][6];
    int n = segment_all("abc", &KANNADA, clusters, 8);
    CHECK(n == 3);
    uint32_t w0[] = {0x61};
    uint32_t w1[] = {0x62};
    uint32_t w2[] = {0x63};
    CHECK(cluster_eq(clusters[0], w0, 1));
    CHECK(cluster_eq(clusters[1], w1, 1));
    CHECK(cluster_eq(clusters[2], w2, 1));
}

static void test_empty_string(void)
{
    uint32_t cluster[6];
    const char *p = "";
    int rc = aks_segment_next(&p, &KANNADA, cluster);
    CHECK(rc == 0);
}

static void test_invalid_utf8(void)
{
    /* 0xFF is not a valid UTF-8 start byte. */
    uint32_t cluster[6];
    const char *p = "\xFF";
    int rc = aks_segment_next(&p, &KANNADA, cluster);
    CHECK(rc == AKS_ERR_INVALID_UTF8);
}

static void test_namaskara(void)
{
    /* ನಮಸ್ಕಾರ  → {NA} {MA} {SA,VIR,KA,AA-sign} {RA} */
    uint32_t clusters[8][6];
    int n = segment_all("ನಮಸ್ಕಾರ", &KANNADA, clusters, 8);
    CHECK(n == 4);

    uint32_t w0[] = {0x0CA8};                              /* ನ  NA */
    uint32_t w1[] = {0x0CAE};                              /* ಮ  MA */
    uint32_t w2[] = {0x0CB8, 0x0CCD, 0x0C95, 0x0CBE};    /* ಸ್ಕಾ */
    uint32_t w3[] = {0x0CB0};                              /* ರ  RA */
    CHECK(cluster_eq(clusters[0], w0, 1));
    CHECK(cluster_eq(clusters[1], w1, 1));
    CHECK(cluster_eq(clusters[2], w2, 4));
    CHECK(cluster_eq(clusters[3], w3, 1));
}

static void test_bengaluru(void)
{
    /* ಬೆಂಗಳೂರು  → {BA,E-sign,ANUSV} {GA} {LLA,UU-sign} {RA,U-sign} */
    uint32_t clusters[8][6];
    int n = segment_all("ಬೆಂಗಳೂರು", &KANNADA, clusters, 8);
    CHECK(n == 4);

    /* ಬೆಂ: BA + E-sign(0x0CC6) + ANUSVARA(0x0C82) */
    uint32_t w0[] = {0x0CAC, 0x0CC6, 0x0C82};
    /* ಗ: GA */
    uint32_t w1[] = {0x0C97};
    /* ಳೂ: LLA(0x0CB3) + UU-sign(0x0CC2) */
    uint32_t w2[] = {0x0CB3, 0x0CC2};
    /* ರು: RA + U-sign(0x0CC1) */
    uint32_t w3[] = {0x0CB0, 0x0CC1};
    CHECK(cluster_eq(clusters[0], w0, 3));
    CHECK(cluster_eq(clusters[1], w1, 1));
    CHECK(cluster_eq(clusters[2], w2, 2));
    CHECK(cluster_eq(clusters[3], w3, 2));
}

static void test_akshara_word(void)
{
    /* ಅಕ್ಷರ  → {A} {KA,VIR,SSA} {RA} */
    uint32_t clusters[8][6];
    int n = segment_all("ಅಕ್ಷರ", &KANNADA, clusters, 8);
    CHECK(n == 3);

    uint32_t w0[] = {0x0C85};                   /* ಅ  A (independent vowel) */
    uint32_t w1[] = {0x0C95, 0x0CCD, 0x0CB7};  /* ಕ್ಷ */
    uint32_t w2[] = {0x0CB0};                   /* ರ  RA */
    CHECK(cluster_eq(clusters[0], w0, 1));
    CHECK(cluster_eq(clusters[1], w1, 3));
    CHECK(cluster_eq(clusters[2], w2, 1));
}

static void test_priti(void)
{
    /* ಪ್ರೀತಿ  → {PA,VIR,RA,II-sign} {TA,I-sign} */
    uint32_t clusters[8][6];
    int n = segment_all("ಪ್ರೀತಿ", &KANNADA, clusters, 8);
    CHECK(n == 2);

    /* ಪ್ರೀ: PA(0x0CAA) + VIR + RA(0x0CB0) + II-sign(0x0CC0) */
    uint32_t w0[] = {0x0CAA, 0x0CCD, 0x0CB0, 0x0CC0};
    /* ತಿ: TA(0x0CA4) + I-sign(0x0CBF) */
    uint32_t w1[] = {0x0CA4, 0x0CBF};
    CHECK(cluster_eq(clusters[0], w0, 4));
    CHECK(cluster_eq(clusters[1], w1, 2));
}

static void test_kannada_digits(void)
{
    /* ೧೨೩ — Kannada digits are single-codepoint clusters */
    uint32_t clusters[8][6];
    int n = segment_all("೧೨೩", &KANNADA, clusters, 8);
    CHECK(n == 3);
    uint32_t w0[] = {0x0CE7};
    uint32_t w1[] = {0x0CE8};
    uint32_t w2[] = {0x0CE9};
    CHECK(cluster_eq(clusters[0], w0, 1));
    CHECK(cluster_eq(clusters[1], w1, 1));
    CHECK(cluster_eq(clusters[2], w2, 1));
}

static void test_vowel_sign_not_absorbed_as_modifier(void)
{
    /* Vowel signs must not be absorbed by the modifier branch.
     * ಕಾ: only vowel sign absorption; modifier slot stays empty. */
    uint32_t clusters[8][6];
    int n = segment_all("ಕಾ", &KANNADA, clusters, 8);
    CHECK(n == 1);
    /* slot 2 must be 0 (no modifier consumed) */
    CHECK(clusters[0][2] == 0);
}

static void test_virama_not_absorbed_as_vowel_sign(void)
{
    /* Halant ಕ್ must produce {KA, VIRAMA}, not {KA} with virama eaten as
     * a vowel sign.  Verified by test_halant_form; this checks the slot. */
    uint32_t clusters[8][6];
    int n = segment_all("ಕ್", &KANNADA, clusters, 8);
    CHECK(n == 1);
    CHECK(clusters[0][0] == 0x0C95);
    CHECK(clusters[0][1] == 0x0CCD);
    CHECK(clusters[0][2] == 0);
}

static void test_conjunct_exceeds_max_depth(void)
{
    /* When a conjunct bond would exceed max_conjunct_depth the spec says:
     * emit the current cluster, start the virama as a new single-codepoint
     * cluster (not absorb it as a terminal halant).
     *
     * Use a depth-1 variant of the rule table so the limit fires cleanly
     * without the 4-slot constraint obscuring the result.
     * Input: ಕ್ನ್ (KA VIR NA VIR) — KA+VIR+NA is depth-1 = max,
     * so the trailing VIR should become its own cluster. */
    aks_rule_table_t depth1 = KANNADA;
    depth1.max_conjunct_depth = 1;

    uint32_t clusters[8][6];
    int n = segment_all("ಕ್ನ್", &depth1, clusters, 8);
    CHECK(n == 2);

    /* First cluster: conjunct KA+VIR+NA */
    uint32_t w0[] = {0x0C95, 0x0CCD, 0x0CA8};
    CHECK(cluster_eq(clusters[0], w0, 3));

    /* Second cluster: virama as its own single-codepoint cluster */
    uint32_t w1[] = {0x0CCD};
    CHECK(cluster_eq(clusters[1], w1, 1));
}

static void test_pointer_advances_correctly(void)
{
    /* After segmenting two clusters the pointer must sit exactly at the
     * third character, not before or after. */
    const char *text = "ಕನ";   /* KA, NA — two bare consonants */
    const char *p    = text;
    uint32_t cluster[6];

    int r1 = aks_segment_next(&p, &KANNADA, cluster);
    CHECK(r1 == 1);
    CHECK(cluster[0] == 0x0C95);  /* KA */

    int r2 = aks_segment_next(&p, &KANNADA, cluster);
    CHECK(r2 == 1);
    CHECK(cluster[0] == 0x0CA8);  /* NA */

    int r3 = aks_segment_next(&p, &KANNADA, cluster);
    CHECK(r3 == 0);               /* end of string */
}

/* ── Main ────────────────────────────────────────────────────────────────── */

int main(void)
{
    printf("test_segmenter\n");

    test_empty_string();
    test_invalid_utf8();
    test_bare_consonant();
    test_consonant_vowel_sign();
    test_conjunct();
    test_conjunct_with_vowel();
    test_modifier();
    test_visarga();
    test_halant_form();
    test_independent_vowel();
    test_multi_cluster_word();
    test_ascii_passthrough();
    test_namaskara();
    test_bengaluru();
    test_akshara_word();
    test_priti();
    test_kannada_digits();
    test_vowel_sign_not_absorbed_as_modifier();
    test_virama_not_absorbed_as_vowel_sign();
    test_conjunct_exceeds_max_depth();
    test_pointer_advances_correctly();

    printf("\n%d passed, %d failed\n", pass_count, fail_count);
    return fail_count ? 1 : 0;
}
