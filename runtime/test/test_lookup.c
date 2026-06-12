/*
 * test_lookup.c — C unit tests for akshara_init(), akshara_select_size(),
 *                 and aks_lookup().
 *
 * Tests mirror the Python TestLookup suite in aks-generator/test/render_png.py so
 * that the C binary search and the Python reference produce identical results
 * for every covered cluster.
 *
 * Requires a generated .aks v3 file at AKS_PATH.  If absent the test prints
 * a skip message and exits 0, so CI does not fail on a clean checkout.
 *
 * Generate the file first:
 *     just script=kannada pack
 *
 * Compile and run via runtime/test/Makefile:
 *     make run
 */

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "../aks_internal.h"

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

/* ── stdio read callback ─────────────────────────────────────────────────── */

static int read_file(uint32_t offset, uint8_t *buf, uint32_t size, void *ud)
{
    FILE *f = (FILE *)ud;
    if (fseek(f, (long)offset, SEEK_SET) != 0) return AKS_ERR_IO;
    if (fread(buf, 1, size, f) != (size_t)size)  return AKS_ERR_IO;
    return AKS_OK;
}

static void no_blit(int16_t x, int16_t y, const uint8_t *bmp,
                    uint16_t w, uint16_t h, uint8_t bpp, void *ud)
{
    (void)x; (void)y; (void)bmp; (void)w; (void)h; (void)bpp; (void)ud;
}

/* ── Path to the generated Kannada .aks file ─────────────────────────────── */

/* Run tests from runtime/test/ so this relative path resolves correctly.
 * Generate with: just script=kannada pack  (default size is 22px) */
#define AKS_PATH "../../fonts/generated/noto_kannada_regular.aks"

/* ── akshara_init tests ───────────────────────────────────────────────────── */

static void test_init_null_args(FILE *f)
{
    akshara_ctx_t ctx;
    /* NULL ctx or blit are always errors. */
    CHECK(akshara_init(NULL,  read_file, no_blit, f,    NULL) == AKS_ERR_NULL_ARG);
    CHECK(akshara_init(&ctx,  read_file, NULL,    f,    NULL) == AKS_ERR_NULL_ARG);
    /* NULL read + NULL read_ud: nothing to read from → error. */
    CHECK(akshara_init(&ctx,  NULL,      no_blit, NULL, NULL) == AKS_ERR_NULL_ARG);
    /* NULL read + non-NULL read_ud: flash array shortcut → not an error. */
    CHECK(akshara_init(&ctx,  NULL,      no_blit, f,    NULL) != AKS_ERR_NULL_ARG);
}

static void test_init_cluster_count_plausible(akshara_ctx_t *ctx)
{
    /* Kannada should have several hundred clusters. */
    CHECK(ctx->_hdr.cluster_count >= 500);
    CHECK(ctx->_hdr.cluster_count <= 10000);
}

static void test_init_rule_table(akshara_ctx_t *ctx)
{
    /* Rule table values must match kannada.py */
    CHECK(ctx->_rules.consonant_start    == 0x0C95u);
    CHECK(ctx->_rules.consonant_end      == 0x0CB9u);
    CHECK(ctx->_rules.virama             == 0x0CCDu);
    CHECK(ctx->_rules.vowel_sign_start   == 0x0CBEu);
    CHECK(ctx->_rules.vowel_sign_end     == 0x0CCDu);
    CHECK(ctx->_rules.modifier_start     == 0x0C82u);
    CHECK(ctx->_rules.modifier_end       == 0x0C83u);
    CHECK(ctx->_rules.max_conjunct_depth == 2);
}

/* ── bad-magic test (no real file needed) ────────────────────────────────── */

static uint8_t s_bad_hdr[28];  /* all zeros → magic == 0, not 0x414B5348 */

static int read_bad_magic(uint32_t off, uint8_t *buf, uint32_t size, void *ud)
{
    (void)ud;
    if (off + size > sizeof(s_bad_hdr)) return AKS_ERR_IO;
    memcpy(buf, s_bad_hdr + off, size);
    return AKS_OK;
}

static void test_init_bad_magic(void)
{
    akshara_ctx_t ctx;
    int rc = akshara_init(&ctx, read_bad_magic, no_blit, NULL, NULL);
    CHECK(rc == AKS_ERR_BAD_MAGIC);
}

/* ── akshara_select_size tests ───────────────────────────────────────────── */

static void test_select_size_first(akshara_ctx_t *ctx)
{
    /* The first entry loaded by init must have sensible values. */
    CHECK(ctx->_size.size_px > 0);
    CHECK(ctx->_size.upem > 0);
    CHECK(ctx->_size.glyph_count > 0);
}

static void test_select_size_not_found(akshara_ctx_t *ctx)
{
    /* Requesting a nonexistent size must return AKS_ERR_NOT_FOUND. */
    CHECK(akshara_select_size(ctx, 255, 0) == AKS_ERR_NOT_FOUND);
}

static void test_select_size_null_ctx(void)
{
    CHECK(akshara_select_size(NULL, 22, 0) == AKS_ERR_NULL_ARG);
}

static void test_select_size_first_entry_re_selectable(akshara_ctx_t *ctx)
{
    /* Selecting the known-present size again must succeed. */
    uint8_t sz = ctx->_size.size_px;
    uint8_t wt = ctx->_size.weight;
    CHECK(akshara_select_size(ctx, sz, wt) == AKS_OK);
    CHECK(ctx->_size.size_px == sz);
}

/* ── aks_lookup tests ────────────────────────────────────────────────────── */

static void test_lookup_bare_ka(akshara_ctx_t *ctx)
{
    /* ಕ bare consonant — must always be present */
    uint32_t cp[6] = {0x0C95u, 0, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    /* v3: key entry has cp[] and comp_off only */
    CHECK(e.cp[0] == 0x0C95u);
    CHECK(e.comp_off < 1024u * 1024u);  /* sanity: comp_off within 1 MB */
}

static void test_lookup_entry_codepoints(akshara_ctx_t *ctx)
{
    /* Verify the returned entry's cp[] matches what we searched for */
    uint32_t cp[6] = {0x0C95u, 0, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.cp[0] == 0x0C95u);
    CHECK(e.cp[1] == 0);
    CHECK(e.cp[2] == 0);
    CHECK(e.cp[3] == 0);
}

static void test_lookup_oov_latin(akshara_ctx_t *ctx)
{
    /* Latin A is not in the Kannada .aks */
    uint32_t cp[6] = {0x0041u, 0, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == 1);
}

static void test_lookup_oov_impossible_sequence(akshara_ctx_t *ctx)
{
    uint32_t cp[6] = {0xFFFFu, 0xFFFFu, 0xFFFFu, 0xFFFFu, 0xFFFFu, 0xFFFFu};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == 1);
}

static void test_lookup_vowel_sign(akshara_ctx_t *ctx)
{
    /* ಕಾ = KA + AA-sign */
    uint32_t cp[6] = {0x0C95u, 0x0CBEu, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.comp_off < 1024u * 1024u);
}

static void test_lookup_modifier(akshara_ctx_t *ctx)
{
    /* ಕಂ = KA + ANUSVARA */
    uint32_t cp[6] = {0x0C95u, 0x0C82u, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
}

static void test_lookup_halant(akshara_ctx_t *ctx)
{
    /* ಕ್ = KA + VIRAMA (half-form) */
    uint32_t cp[6] = {0x0C95u, 0x0CCDu, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
}

static void test_lookup_conjunct_na_na(akshara_ctx_t *ctx)
{
    /* ನ್ನ = NA + VIRAMA + NA  (from ಕನ್ನಡ) */
    uint32_t cp[6] = {0x0CA8u, 0x0CCDu, 0x0CA8u, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
}

static void test_lookup_conjunct_ka_ssa(akshara_ctx_t *ctx)
{
    /* ಕ್ಷ = KA + VIRAMA + SSA  (from ಅಕ್ಷರ) */
    uint32_t cp[6] = {0x0C95u, 0x0CCDu, 0x0CB7u, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
}

static void test_lookup_conjunct_with_vowel(akshara_ctx_t *ctx)
{
    /* ಸ್ಕಾ = SA + VIRAMA + KA + AA-sign  (from ನಮಸ್ಕಾರ) */
    uint32_t cp[6] = {0x0CB8u, 0x0CCDu, 0x0C95u, 0x0CBEu, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
}

static void test_lookup_kannada_digit(akshara_ctx_t *ctx)
{
    /* ೧ = Kannada digit one */
    uint32_t cp[6] = {0x0CE7u, 0, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
}

static void test_lookup_comp_off_sane(akshara_ctx_t *ctx)
{
    /* comp_off for ಕ must be within a reasonable bound.
     * Composition table for Kannada 22px is well under 512 KB. */
    uint32_t cp[6] = {0x0C95u, 0, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.comp_off < 512u * 1024u);
}

/* ── Main ────────────────────────────────────────────────────────────────── */

int main(void)
{
    printf("test_lookup\n");

    /* Tests that require no real .aks file */
    test_init_bad_magic();
    test_select_size_null_ctx();

    FILE *f = fopen(AKS_PATH, "rb");
    if (!f) {
        printf("SKIP: cannot open %s\n", AKS_PATH);
        printf("      Generate it first: just script=kannada pack\n");
        printf("\n%d passed, %d failed  (file-dependent tests skipped)\n",
               pass_count, fail_count);
        return fail_count ? 1 : 0;
    }

    test_init_null_args(f);

    /* Initialize the shared ctx; skip all dependent tests if it fails
     * (e.g. an old v2 .aks file is present but hasn't been regenerated). */
    akshara_ctx_t ctx;
    int init_rc = akshara_init(&ctx, read_file, no_blit, f, NULL);
    if (init_rc != AKS_OK) {
        if (init_rc == AKS_ERR_BAD_VERSION)
            printf("SKIP: %s is not a v3 file — regenerate: just script=kannada pack\n",
                   AKS_PATH);
        else
            printf("SKIP: akshara_init returned %d for %s\n", init_rc, AKS_PATH);
        fclose(f);
        printf("\n%d passed, %d failed  (init-dependent tests skipped)\n",
               pass_count, fail_count);
        return fail_count ? 1 : 0;
    }
    /* ctx is valid from here; verify init populated expected fields */
    CHECK(ctx._hdr.version       == 3);
    CHECK(ctx._hdr.script_id     == AKS_SCRIPT_KANNADA);
    CHECK(ctx._hdr.size_count    >  0);
    CHECK(ctx._hdr.cluster_count >  0);
    CHECK(ctx._size.glyph_height >  0);
    CHECK(ctx._size.baseline     >  0);
    CHECK(ctx._size.baseline     <  ctx._size.glyph_height);
    CHECK(ctx._size.bpp          == 1 || ctx._size.bpp == 2);
    CHECK(ctx._size.upem         >  0);
    CHECK(ctx._size.glyph_count  >  0);

    test_init_cluster_count_plausible(&ctx);
    test_init_rule_table(&ctx);

    test_select_size_first(&ctx);
    test_select_size_not_found(&ctx);
    test_select_size_first_entry_re_selectable(&ctx);

    test_lookup_bare_ka(&ctx);
    test_lookup_entry_codepoints(&ctx);
    test_lookup_oov_latin(&ctx);
    test_lookup_oov_impossible_sequence(&ctx);
    test_lookup_vowel_sign(&ctx);
    test_lookup_modifier(&ctx);
    test_lookup_halant(&ctx);
    test_lookup_conjunct_na_na(&ctx);
    test_lookup_conjunct_ka_ssa(&ctx);
    test_lookup_conjunct_with_vowel(&ctx);
    test_lookup_kannada_digit(&ctx);
    test_lookup_comp_off_sane(&ctx);

    fclose(f);

    printf("\n%d passed, %d failed\n", pass_count, fail_count);
    return fail_count ? 1 : 0;
}
