/*
 * test_blit.c — C unit tests for akshara_render() and akshara_measure().
 *
 * Tests verify:
 *   - pen advance on single and multi-cluster strings
 *   - blit callback receives correct x (with bearing_x), y, w, h, bpp
 *   - akshara_measure agrees with akshara_render's return value
 *   - OOV clusters degrade gracefully (no crash, blit skipped when all OOV)
 *   - NULL argument handling
 *
 * Requires a generated .aks file at AKS_PATH.  If absent the test prints
 * a skip message and exits 0 so CI does not fail on a clean checkout.
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

/* ── Blit logger ─────────────────────────────────────────────────────────── */

typedef struct {
    int      call_count;
    int16_t  last_x;
    int16_t  last_y;
    uint16_t last_w;
    uint16_t last_h;
    uint8_t  last_bpp;
    bool     bmp_nonzero;  /* any non-zero byte in last bitmap */
} blit_log_t;

static void log_blit(int16_t x, int16_t y, const uint8_t *bmp,
                     uint16_t w, uint16_t h, uint8_t bpp, void *ud)
{
    blit_log_t *log = (blit_log_t *)ud;
    log->call_count++;
    log->last_x   = x;
    log->last_y   = y;
    log->last_w   = w;
    log->last_h   = h;
    log->last_bpp = bpp;

    /* Check if the bitmap has any ink; a blank glyph would be suspicious. */
    uint32_t ppb  = (uint32_t)(8u / bpp);
    uint32_t stride = ((uint32_t)w + ppb - 1u) / ppb;
    uint32_t nbytes = stride * (uint32_t)h;
    log->bmp_nonzero = false;
    for (uint32_t i = 0; i < nbytes; i++) {
        if (bmp[i]) { log->bmp_nonzero = true; break; }
    }
}

/* ── Path to the generated Kannada .aks file ─────────────────────────────── */

#define AKS_PATH "../../fonts/noto_kannada_regular_20.aks"

/* ── UTF-8 test strings ──────────────────────────────────────────────────── */

/* ಕ  = U+0C95 */
#define STR_KA     "\xe0\xb2\x95"
/* ಕನ್ನಡ = ka + na + virama + na + da  (3 clusters: ಕ, ನ್ನ, ಡ) */
#define STR_KANNADA "\xe0\xb2\x95\xe0\xb2\xa8\xe0\xb3\x8d\xe0\xb2\xa8\xe0\xb2\xa1"
/* Latin 'A' — not in the Kannada .aks (confirmed by test_lookup) */
#define STR_OOV_LATIN "A"
/*
 * ನಮಸ್ಕಾರ — contains ಸ್ಕಾ (SA+VIRAMA+KA+AA-sign) which is OOV in the 20px .aks
 * because SA was not yet in COMMON_CONSONANTS when that .aks was generated.
 * Used to verify the OOV fallback pairs the AA-sign with KA (ಕಾ) rather than
 * skipping it silently.
 */
#define STR_NAMASKARA \
    "\xe0\xb2\xa8"   /* ನ  U+0CA8 */ \
    "\xe0\xb2\xae"   /* ಮ  U+0CAE */ \
    "\xe0\xb2\xb8"   /* ಸ  U+0CB8 */ \
    "\xe0\xb3\x8d"   /* ್  U+0CCD virama */ \
    "\xe0\xb2\x95"   /* ಕ  U+0C95 */ \
    "\xe0\xb2\xbe"   /* ಾ  U+0CBE AA-sign */ \
    "\xe0\xb2\xb0"   /* ರ  U+0CB0 */

/* ── NULL argument tests (no .aks required) ──────────────────────────────── */

static void test_render_null_ctx(void)
{
    /* NULL ctx — must return the starting x without crashing. */
    blit_log_t log = {0};
    int16_t x = akshara_render(NULL, 5, 10, STR_KA);
    CHECK(x == 5);
    (void)log;
}

static void test_render_null_utf8(akshara_ctx_t *ctx)
{
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t x = akshara_render(ctx, 7, 0, NULL);
    CHECK(x == 7);
    CHECK(log.call_count == 0);
}

static void test_measure_null_ctx(void)
{
    CHECK(akshara_measure(NULL, STR_KA) == 0);
}

static void test_measure_null_utf8(akshara_ctx_t *ctx)
{
    CHECK(akshara_measure(ctx, NULL) == 0);
}

/* ── Empty string ─────────────────────────────────────────────────────────── */

static void test_render_empty(akshara_ctx_t *ctx)
{
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t x = akshara_render(ctx, 20, 10, "");
    CHECK(x == 20);
    CHECK(log.call_count == 0);
}

static void test_measure_empty(akshara_ctx_t *ctx)
{
    CHECK(akshara_measure(ctx, "") == 0);
}

/* ── Single-cluster render ────────────────────────────────────────────────── */

static void test_render_single_ka(akshara_ctx_t *ctx)
{
    /* Rendering a single ಕ should call blit exactly once and advance the pen. */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t end_x = akshara_render(ctx, 0, 0, STR_KA);

    CHECK(log.call_count == 1);
    CHECK(end_x > 0);            /* pen must move forward */
    CHECK(end_x < 200);          /* sanity: advance is not absurdly large */
}

static void test_render_blit_dimensions(akshara_ctx_t *ctx)
{
    /* w, h, bpp passed to blit must match what the header declares. */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    akshara_render(ctx, 0, 0, STR_KA);

    CHECK(log.last_h   == ctx->_hdr.glyph_height);
    CHECK(log.last_bpp == ctx->_hdr.bpp);
    CHECK(log.last_w   > 0);
}

static void test_render_blit_y_passthrough(akshara_ctx_t *ctx)
{
    /* The y coordinate passed to render must be forwarded to blit unchanged. */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    akshara_render(ctx, 0, 42, STR_KA);
    CHECK(log.last_y == 42);
}

static void test_render_blit_x_bearing(akshara_ctx_t *ctx)
{
    /*
     * blit x = render start x + bearing_x (signed).
     * Look up ಕ to get its bearing_x, then verify it is applied.
     */
    uint32_t cp[4] = {0x0C95u, 0, 0, 0};
    aks_key_entry_t e;
    if (aks_lookup(ctx, cp, &e) != AKS_OK) return;  /* skip if OOV */

    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t start_x = 10;
    akshara_render(ctx, start_x, 0, STR_KA);

    int16_t expected_blit_x = (int16_t)(start_x + (int8_t)e.bearing_x);
    CHECK(log.last_x == expected_blit_x);
}

static void test_render_pen_matches_advance(akshara_ctx_t *ctx)
{
    /*
     * For a single-cluster string the return value must equal
     * start_x + e.advance regardless of bearing_x.
     */
    uint32_t cp[4] = {0x0C95u, 0, 0, 0};
    aks_key_entry_t e;
    if (aks_lookup(ctx, cp, &e) != AKS_OK) return;

    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t start_x = 5;
    int16_t end_x   = akshara_render(ctx, start_x, 0, STR_KA);

    CHECK(end_x == (int16_t)(start_x + e.advance));
}

static void test_render_bitmap_has_ink(akshara_ctx_t *ctx)
{
    /* A real glyph bitmap must contain at least one set bit. */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    akshara_render(ctx, 0, 0, STR_KA);
    CHECK(log.bmp_nonzero);
}

/* ── Multi-cluster render ─────────────────────────────────────────────────── */

static void test_render_kannada_cluster_count(akshara_ctx_t *ctx)
{
    /*
     * "ಕನ್ನಡ" segments into 3 clusters: ಕ | ನ್ನ | ಡ.
     * Blit must be called exactly 3 times.
     */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    akshara_render(ctx, 0, 0, STR_KANNADA);
    CHECK(log.call_count == 3);
}

static void test_render_starting_offset(akshara_ctx_t *ctx)
{
    /*
     * Render the same string twice: once at x=0 and once at x=100.
     * The second run's final x must equal the first's final x + 100.
     */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t end0 = akshara_render(ctx, 0,   0, STR_KANNADA);
    int16_t end1 = akshara_render(ctx, 100, 0, STR_KANNADA);
    CHECK(end1 == (int16_t)(end0 + 100));
}

/* ── akshara_measure ───────────────────────────────────────────────────────── */

static void test_measure_single_ka(akshara_ctx_t *ctx)
{
    /* measure("ಕ") must equal the advance stored in the key entry for ಕ. */
    uint32_t cp[4] = {0x0C95u, 0, 0, 0};
    aks_key_entry_t e;
    if (aks_lookup(ctx, cp, &e) != AKS_OK) return;

    int16_t measured = akshara_measure(ctx, STR_KA);
    CHECK(measured == (int16_t)e.advance);
}

static void test_measure_equals_render(akshara_ctx_t *ctx)
{
    /*
     * akshara_measure must return the same total advance as akshara_render
     * when render starts at x=0.
     */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t render_end = akshara_render(ctx, 0, 0, STR_KANNADA);
    int16_t measured   = akshara_measure(ctx, STR_KANNADA);
    CHECK(measured == render_end);
}

static void test_measure_no_blit(akshara_ctx_t *ctx)
{
    /*
     * akshara_measure must not call blit.
     * Verify by counting calls after measure.
     */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    akshara_measure(ctx, STR_KANNADA);
    CHECK(log.call_count == 0);
}

/* ── OOV fallback ─────────────────────────────────────────────────────────── */

static void test_render_oov_no_crash(akshara_ctx_t *ctx)
{
    /*
     * Latin 'A' is not in the Kannada .aks (confirmed by test_lookup).
     * Rendering it must not crash and must not call blit (since the
     * per-codepoint fallback also misses).
     */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t start_x = 20;
    int16_t end_x   = akshara_render(ctx, start_x, 0, STR_OOV_LATIN);
    CHECK(log.call_count == 0);
    CHECK(end_x == start_x);     /* no advance when all codepoints are OOV */
}

static void test_measure_oov_zero(akshara_ctx_t *ctx)
{
    /* measure of a fully-OOV string must be 0. */
    CHECK(akshara_measure(ctx, STR_OOV_LATIN) == 0);
}

/*
 * ಸ್ಕಾ is OOV in the 20px .aks (SA not in COMMON_CONSONANTS at gen time).
 * The OOV fallback must pair KA+AA-sign as a [ಕ, ಾ] lookup instead of
 * trying the AA-sign as a standalone codepoint (which has no entry).
 *
 * Evidence: ಕಾ advance (20px) > ಕ advance (11px).  If the fallback drops
 * the vowel sign, ನಮಸ್ಕಾರ measures shorter than if the sign is included.
 */
static void test_oov_conjunct_vowel_sign_paired(akshara_ctx_t *ctx)
{
    /* Measure ನಮಸ್ಕಾರ — the ಕಾ pair advance must exceed bare ಕ advance. */
    int16_t w_namaskara = akshara_measure(ctx, STR_NAMASKARA);

    /* ನಮಸ್ಕರ (same word but without the AA-sign on ಕ) for comparison.
     * ಸ್ಕ is still OOV; only the trailing vowel sign differs. */
    int16_t w_no_sign = akshara_measure(ctx,
        "\xe0\xb2\xa8"   /* ನ */
        "\xe0\xb2\xae"   /* ಮ */
        "\xe0\xb2\xb8"   /* ಸ */
        "\xe0\xb3\x8d"   /* ್ */
        "\xe0\xb2\x95"   /* ಕ  (no AA-sign) */
        "\xe0\xb2\xb0"   /* ರ */
    );

    /* With the fix, ಕಾ (advance 20) > ಕ (advance 11): namaskara is wider. */
    CHECK(w_namaskara > w_no_sign);

    /* Also ensure we got some blit calls — rendering must not be silent. */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    akshara_render(ctx, 0, 0, STR_NAMASKARA);
    CHECK(log.call_count >= 4);  /* at minimum: ನ, ಮ, ಕಾ (or ಕ+ಾ), ರ */
}

/* ── Main ────────────────────────────────────────────────────────────────── */

int main(void)
{
    printf("test_blit\n");

    /* Tests that require no .aks file */
    test_render_null_ctx();
    test_measure_null_ctx();

    FILE *f = fopen(AKS_PATH, "rb");
    if (!f) {
        printf("SKIP: cannot open %s\n", AKS_PATH);
        printf("      Generate it first:\n");
        printf("        cd host && uv run python akshara_gen.py"
               " --font <font.ttf> --script kannada --size 24 --bpp 1"
               " --output ../fonts/noto_kannada_regular_24.aks\n");
        printf("\n%d passed, %d failed  (file-dependent tests skipped)\n",
               pass_count, fail_count);
        return fail_count ? 1 : 0;
    }

    blit_log_t log = {0};
    akshara_ctx_t ctx;
    int rc = akshara_init(&ctx, read_file, log_blit, f, &log);
    if (rc != AKS_OK) {
        printf("FAIL: akshara_init returned %d\n", rc);
        fclose(f);
        return 1;
    }

    test_render_null_utf8(&ctx);
    test_measure_null_utf8(&ctx);

    test_render_empty(&ctx);
    test_measure_empty(&ctx);

    test_render_single_ka(&ctx);
    test_render_blit_dimensions(&ctx);
    test_render_blit_y_passthrough(&ctx);
    test_render_blit_x_bearing(&ctx);
    test_render_pen_matches_advance(&ctx);
    test_render_bitmap_has_ink(&ctx);

    test_render_kannada_cluster_count(&ctx);
    test_render_starting_offset(&ctx);

    test_measure_single_ka(&ctx);
    test_measure_equals_render(&ctx);
    test_measure_no_blit(&ctx);

    test_render_oov_no_crash(&ctx);
    test_measure_oov_zero(&ctx);
    test_oov_conjunct_vowel_sign_paired(&ctx);

    fclose(f);

    printf("\n%d passed, %d failed\n", pass_count, fail_count);
    return fail_count ? 1 : 0;
}
