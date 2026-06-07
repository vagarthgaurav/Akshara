/*
 * test_lookup.c — C unit tests for akshara_init() and aks_lookup().
 *
 * Tests mirror the Python TestLookup suite in host/test/render_png.py so
 * that the C binary search and the Python reference produce identical results
 * for every covered cluster.
 *
 * Requires a generated .aks file at AKS_PATH.  If absent the test prints
 * a skip message and exits 0, so CI does not fail on a clean checkout.
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

/* Run tests from runtime/test/ so this relative path resolves correctly. */
#define AKS_PATH "../../fonts/noto_kannada_regular_24.aks"

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

static void test_init_succeeds(akshara_ctx_t *ctx, FILE *f)
{
    int rc = akshara_init(ctx, read_file, no_blit, f, NULL);
    CHECK(rc == AKS_OK);
    CHECK(ctx->_hdr.script_id    == AKS_SCRIPT_KANNADA);
    CHECK(ctx->_hdr.cluster_count > 0);
    CHECK(ctx->_hdr.glyph_height > 0);
    CHECK(ctx->_hdr.baseline     > 0);
    CHECK(ctx->_hdr.baseline     < ctx->_hdr.glyph_height);
    CHECK(ctx->_hdr.bpp          == 1 || ctx->_hdr.bpp == 2);
}

static void test_init_cluster_count_plausible(akshara_ctx_t *ctx)
{
    /* Kannada at 24px should have several hundred clusters. */
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

/* ── aks_lookup tests ────────────────────────────────────────────────────── */

static void test_lookup_bare_ka(akshara_ctx_t *ctx)
{
    /* ಕ bare consonant — must always be present */
    uint32_t cp[6] = {0x0C95u, 0, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.advance > 0);
    CHECK(e.width   > 0);
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
    /* Latin A is not in the Kannada .aks — mirrors Python test_oov_returns_none */
    uint32_t cp[6] = {0x0041u, 0, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == 1);
}

static void test_lookup_oov_impossible_sequence(akshara_ctx_t *ctx)
{
    /* A codepoint sequence that can never appear as a valid cluster */
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
    CHECK(e.advance > 0);
}

static void test_lookup_modifier(akshara_ctx_t *ctx)
{
    /* ಕಂ = KA + ANUSVARA */
    uint32_t cp[6] = {0x0C95u, 0x0C82u, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.advance > 0);
}

static void test_lookup_halant(akshara_ctx_t *ctx)
{
    /* ಕ್ = KA + VIRAMA (half-form / halant) */
    uint32_t cp[6] = {0x0C95u, 0x0CCDu, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.advance > 0);
}

static void test_lookup_conjunct_na_na(akshara_ctx_t *ctx)
{
    /* ನ್ನ = NA + VIRAMA + NA  (from ಕನ್ನಡ; NA is in COMMON_CONSONANTS Tier 1) */
    uint32_t cp[6] = {0x0CA8u, 0x0CCDu, 0x0CA8u, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.advance > 0);
}

static void test_lookup_conjunct_ka_ssa(akshara_ctx_t *ctx)
{
    /* ಕ್ಷ = KA + VIRAMA + SSA  (from ಅಕ್ಷರ; both in COMMON_CONSONANTS) */
    uint32_t cp[6] = {0x0C95u, 0x0CCDu, 0x0CB7u, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.advance > 0);
}

static void test_lookup_conjunct_with_vowel(akshara_ctx_t *ctx)
{
    /* ಸ್ಕಾ = SA + VIRAMA + KA + AA-sign  (from ನಮಸ್ಕಾರ; SA and KA both in COMMON_CONSONANTS) */
    uint32_t cp[6] = {0x0CB8u, 0x0CCDu, 0x0C95u, 0x0CBEu, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.advance > 0);
}

static void test_lookup_kannada_digit(akshara_ctx_t *ctx)
{
    /* ೧ = Kannada digit one */
    uint32_t cp[6] = {0x0CE7u, 0, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.advance > 0);
}

static void test_lookup_advance_sane(akshara_ctx_t *ctx)
{
    /* advance should be <= 4× glyph_height (very wide glyph would be unusual) */
    uint32_t cp[6] = {0x0C95u, 0, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    CHECK(e.advance <= (uint16_t)(ctx->_hdr.glyph_height * 4));
    CHECK(e.width   <= (uint8_t)(ctx->_hdr.glyph_height * 4));
}

static void test_lookup_bitmap_offset_in_range(akshara_ctx_t *ctx)
{
    /* bitmap_off must not point past a reasonable upper bound */
    uint32_t cp[6] = {0x0C95u, 0, 0, 0, 0, 0};
    aks_key_entry_t e;
    CHECK(aks_lookup(ctx, cp, &e) == AKS_OK);
    /* 300 KB is a very conservative upper bound for the Kannada bitmap store */
    CHECK(e.bitmap_off < 300u * 1024u);
}

/* ── Main ────────────────────────────────────────────────────────────────── */

int main(void)
{
    printf("test_lookup\n");

    /* Bad-magic test requires no real .aks file */
    test_init_bad_magic();

    FILE *f = fopen(AKS_PATH, "rb");
    if (!f) {
        printf("SKIP: cannot open %s\n", AKS_PATH);
        printf("      Generate it first:\n");
        printf("        cd host && uv run python akshara_gen.py"
               " --font <font.ttf> --script kannada --size 24 --bpp 1"
               " --output ../fonts/noto_kannada_regular_24.aks\n");
        /* Not a test failure — clean checkout has no .aks file */
        printf("\n%d passed, %d failed  (file-dependent tests skipped)\n",
               pass_count, fail_count);
        return fail_count ? 1 : 0;
    }

    akshara_ctx_t ctx;

    test_init_null_args(f);
    test_init_succeeds(&ctx, f);
    test_init_cluster_count_plausible(&ctx);
    test_init_rule_table(&ctx);

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
    test_lookup_advance_sane(&ctx);
    test_lookup_bitmap_offset_in_range(&ctx);

    fclose(f);

    printf("\n%d passed, %d failed\n", pass_count, fail_count);
    return fail_count ? 1 : 0;
}
