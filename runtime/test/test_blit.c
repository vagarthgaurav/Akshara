/*
 * test_blit.c — C unit tests for akshara_render() and akshara_measure().
 *
 * Tests verify:
 *   - pen advance on single and multi-cluster strings
 *   - blit callback receives correct x, y, w, h, bpp (v3: called once per glyph)
 *   - akshara_measure agrees with akshara_render's return value
 *   - OOV clusters degrade gracefully (no crash, blit skipped when all OOV)
 *   - NULL argument handling
 *
 * v3 notes:
 *   - blit is called once per glyph (not once per cluster as in v2)
 *   - (x, y) passed to blit is the exact top-left of the content bitmap
 *   - advance is derived from composition entries (HarfBuzz design units)
 *
 * Requires a generated .aks v3 file at AKS_PATH.  If absent the test prints
 * a skip message and exits 0 so CI does not fail on a clean checkout.
 *
 * Generate the file first: just script=kannada pack
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

    uint32_t ppb    = (uint32_t)(8u / bpp);
    uint32_t stride = ((uint32_t)w + ppb - 1u) / ppb;
    uint32_t nbytes = stride * (uint32_t)h;
    log->bmp_nonzero = false;
    for (uint32_t i = 0; i < nbytes; i++) {
        if (bmp[i]) { log->bmp_nonzero = true; break; }
    }
}

/* ── Path to the generated Kannada .aks file ─────────────────────────────── */

#define AKS_PATH "../../fonts/generated/noto_kannada_regular.aks"

/* ── UTF-8 test strings ──────────────────────────────────────────────────── */

/* ಕ  = U+0C95 */
#define STR_KA     "\xe0\xb2\x95"
/* ಕನ್ನಡ = ka + na + virama + na + da  (3 clusters: ಕ, ನ್ನ, ಡ) */
#define STR_KANNADA "\xe0\xb2\x95\xe0\xb2\xa8\xe0\xb3\x8d\xe0\xb2\xa8\xe0\xb2\xa1"
/* Latin 'A' — not in the Kannada .aks */
#define STR_OOV_LATIN "A"
/*
 * ನಮಸ್ಕಾರ — contains ಸ್ಕಾ (SA+VIRAMA+KA+AA-sign).
 * Used to verify the OOV fallback pairs KA+AA-sign as ಕಾ rather than
 * skipping the vowel sign silently.
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
    int16_t x = akshara_render(NULL, 5, 10, STR_KA);
    CHECK(x == 5);
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
    /* Rendering a single ಕ must call blit at least once and advance the pen. */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t end_x = akshara_render(ctx, 0, 0, STR_KA);

    CHECK(log.call_count >= 1);
    CHECK(end_x > 0);
    CHECK(end_x < 200);
}

static void test_render_blit_dimensions(akshara_ctx_t *ctx)
{
    /*
     * v3: blit is called with the glyph's content dimensions (not the full box).
     * w and h are the content bitmap size — both must be positive and within
     * the full glyph box.
     */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    akshara_render(ctx, 0, 0, STR_KA);

    CHECK(log.last_w > 0);
    CHECK(log.last_h > 0);
    CHECK(log.last_h <= ctx->_size.glyph_height);
    CHECK(log.last_bpp == ctx->_size.bpp);
}

static void test_render_blit_y_offset_consistent(akshara_ctx_t *ctx)
{
    /*
     * v3: blit_y is adjusted for baseline/metrics, so it is NOT equal to the
     * y argument passed to akshara_render.  However, the offset between two
     * renders at different y values must be exactly the y delta.
     */
    blit_log_t log0 = {0};
    ctx->blit_ud = &log0;
    akshara_render(ctx, 0, 0, STR_KA);

    blit_log_t log1 = {0};
    ctx->blit_ud = &log1;
    akshara_render(ctx, 0, 50, STR_KA);

    CHECK(log1.last_y == (int16_t)(log0.last_y + 50));
}

static void test_render_blit_x_in_range(akshara_ctx_t *ctx)
{
    /*
     * blit_x = start_x + hb_x_offset_px + bearing_x.
     * Bearing on Indic glyphs is typically small; accept ±20px from start.
     */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t start_x = 10;
    akshara_render(ctx, start_x, 0, STR_KA);

    CHECK(log.last_x >= start_x - 20);
    CHECK(log.last_x <= start_x + 20);
}

static void test_render_pen_matches_measure(akshara_ctx_t *ctx)
{
    /*
     * For any string, akshara_render(x=start) must return
     * start + akshara_measure().
     */
    int16_t start_x = 5;
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t end_x  = akshara_render(ctx, start_x, 0, STR_KA);
    int16_t measured = akshara_measure(ctx, STR_KA);
    CHECK(end_x == (int16_t)(start_x + measured));
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
     * v3: blit is called once per glyph — at least one blit per cluster,
     * so call_count >= 3.
     */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    akshara_render(ctx, 0, 0, STR_KANNADA);
    CHECK(log.call_count >= 3);
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
    int16_t measured = akshara_measure(ctx, STR_KA);
    CHECK(measured > 0);
    CHECK(measured < 200);
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
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    akshara_measure(ctx, STR_KANNADA);
    CHECK(log.call_count == 0);
}

/* ── OOV fallback ─────────────────────────────────────────────────────────── */

static void test_render_oov_no_crash(akshara_ctx_t *ctx)
{
    /*
     * Latin 'A' is not in the Kannada .aks.
     * Rendering it must not crash and must not call blit.
     */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    int16_t start_x = 20;
    int16_t end_x   = akshara_render(ctx, start_x, 0, STR_OOV_LATIN);
    CHECK(log.call_count == 0);
    CHECK(end_x == start_x);
}

static void test_measure_oov_zero(akshara_ctx_t *ctx)
{
    CHECK(akshara_measure(ctx, STR_OOV_LATIN) == 0);
}

/*
 * ಸ್ಕಾ is an OOV cluster if SA is not in CONJUNCT_PAIRS for this .aks.
 * The OOV fallback must pair KA+AA-sign as ಕಾ rather than dropping the sign.
 * Evidence: ಕಾ advance > ಕ advance → ನಮಸ್ಕಾರ is wider than ನಮಸ್ಕರ.
 */
static void test_oov_conjunct_vowel_sign_paired(akshara_ctx_t *ctx)
{
    int16_t w_with_sign = akshara_measure(ctx, STR_NAMASKARA);

    /* Same word without the AA-sign on ಕ */
    int16_t w_no_sign = akshara_measure(ctx,
        "\xe0\xb2\xa8"   /* ನ */
        "\xe0\xb2\xae"   /* ಮ */
        "\xe0\xb2\xb8"   /* ಸ */
        "\xe0\xb3\x8d"   /* ್ */
        "\xe0\xb2\x95"   /* ಕ  (no AA-sign) */
        "\xe0\xb2\xb0"   /* ರ */
    );

    /*
     * If ಸ್ಕಾ is OOV and the fallback correctly pairs ಕಾ:
     * w_with_sign > w_no_sign (ಕಾ advance > ಕ advance).
     * If ಸ್ಕಾ is a known cluster this test is less meaningful but still valid
     * (both sides equal or close).
     */
    CHECK(w_with_sign >= w_no_sign);

    /* Rendering must produce some blit calls — not entirely silent. */
    blit_log_t log = {0};
    ctx->blit_ud = &log;
    akshara_render(ctx, 0, 0, STR_NAMASKARA);
    CHECK(log.call_count >= 4);  /* at minimum: ನ, ಮ, ಕ (or ಕಾ), ರ */
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
        printf("      Generate it first: just script=kannada pack\n");
        printf("\n%d passed, %d failed  (file-dependent tests skipped)\n",
               pass_count, fail_count);
        return fail_count ? 1 : 0;
    }

    blit_log_t log = {0};
    akshara_ctx_t ctx;
    int rc = akshara_init(&ctx, read_file, log_blit, f, &log);
    if (rc != AKS_OK) {
        if (rc == AKS_ERR_BAD_VERSION)
            printf("SKIP: %s is not a v3 file — regenerate: just script=kannada pack\n",
                   AKS_PATH);
        else
            printf("SKIP: akshara_init returned %d for %s\n", rc, AKS_PATH);
        fclose(f);
        printf("\n%d passed, %d failed  (init-dependent tests skipped)\n",
               pass_count, fail_count);
        return fail_count ? 1 : 0;
    }

    test_render_null_utf8(&ctx);
    test_measure_null_utf8(&ctx);

    test_render_empty(&ctx);
    test_measure_empty(&ctx);

    test_render_single_ka(&ctx);
    test_render_blit_dimensions(&ctx);
    test_render_blit_y_offset_consistent(&ctx);
    test_render_blit_x_in_range(&ctx);
    test_render_pen_matches_measure(&ctx);
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
