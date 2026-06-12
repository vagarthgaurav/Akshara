/*
 * kannada_paragraph.ino — render a paragraph of Kannada text with word wrap at 22px.
 *
 * ── Generate the font file ────────────────────────────────────────────────────
 *   just script=kannada sizes=22 pack
 *
 * Copy noto_kannada_regular.aks to the root of a FAT-formatted SD card.
 *
 * ── Required libraries ────────────────────────────────────────────────────────
 *   Akshara  (this library)
 *   GxEPD2   (ZinggJM)
 *   SD       (built-in)
 */

#include <GxEPD2_BW.h>
#include <SD.h>
#include <Akshara.h>

static const int SD_CS    = 10;
static const int EPD_CS   = 3;
static const int EPD_DC   = 2;
static const int EPD_RST  = 1;
static const int EPD_BUSY = 0;
static const int EPD_SCK  = 4;
static const int EPD_MOSI = 6;
static const int EPD_MISO = -1;

GxEPD2_BW<GxEPD2_290_BS, GxEPD2_290_BS::HEIGHT>
    display(GxEPD2_290_BS(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

static const char FONT_FILE[] = "/noto_kannada_regular.aks";
static const char TEXT[] =
    "ವಾಸ್ತವವಾಗಿ, ಪೋಲಂಡ್ ಮತ್ತು ಜರ್ಮನಿಗಳು ತಮ್ಮನ್ನು ತಾವು ಕಷ್ಟಕರ "
    "ಪರಿಸ್ಥಿತಿಯಲ್ಲಿ ಕಂಡುಕೊಂಡರು: ಮೊದಲನೆಯದಾಗಿ ಅವರು ತಮ್ಮ";

static const int16_t MARGIN    = 4;
static const int16_t LINE_SIZE = 22;
static const int16_t LINE_GAP  = 5;
static const int16_t LINE_H    = LINE_SIZE + LINE_GAP;

// ── Callbacks ─────────────────────────────────────────────────────────────────

static int read_sd(uint32_t offset, uint8_t *buf, uint32_t size, void *ud) {
    File *f = (File *)ud;
    if (!f->seek(offset)) return AKS_ERR_IO;
    return (f->read(buf, size) == size) ? AKS_OK : AKS_ERR_IO;
}

static void blit_gxepd2(int16_t x, int16_t y, const uint8_t *bitmap,
                         uint16_t w, uint16_t h, uint8_t bpp, void *ud) {
    Adafruit_GFX *gfx = (Adafruit_GFX *)ud;
    if (bpp == 1)
        gfx->drawBitmap(x, y, bitmap, (int16_t)w, (int16_t)h, GxEPD_BLACK);
}

// ── Word-wrap renderer ────────────────────────────────────────────────────────

// Renders UTF-8 text with word wrap. Words must be separated by ASCII space (0x20).
static void render_paragraph(akshara_ctx_t *ctx,
                              int16_t x0, int16_t y0,
                              const char *text,
                              int16_t max_w, int16_t line_h) {
    static char word_buf[96];
    static char line_buf[288];

    const char *p          = text;
    const char *line_start = text;
    int16_t     line_w     = 0;
    int16_t     y          = y0;
    bool        line_empty = true;

    int16_t space_w = akshara_measure(ctx, " ");

    while (true) {
        const char *word_start = p;
        while (*p && (uint8_t)*p != ' ') p++;
        const char *word_end = p;
        bool        at_end   = (*p == '\0');

        size_t wlen = (size_t)(word_end - word_start);
        if (wlen > 0 && wlen < sizeof(word_buf)) {
            memcpy(word_buf, word_start, wlen);
            word_buf[wlen] = '\0';

            int16_t word_w = akshara_measure(ctx, word_buf);
            int16_t need_w = line_empty ? word_w : (line_w + space_w + word_w);

            if (!line_empty && need_w > max_w) {
                // Flush the current line up to (but not including) this word.
                size_t llen = (size_t)(word_start - line_start);
                while (llen > 0 && line_start[llen - 1] == ' ') llen--;
                if (llen > 0 && llen < sizeof(line_buf)) {
                    memcpy(line_buf, line_start, llen);
                    line_buf[llen] = '\0';
                    akshara_render(ctx, x0, y, line_buf);
                }
                y          += line_h;
                line_start  = word_start;
                line_w      = word_w;
                line_empty  = false;
            } else {
                line_w     = need_w;
                line_empty = false;
            }
        }

        if (at_end) break;
        p++;  // skip the space
    }

    // Render the last (or only) line.
    if (*line_start)
        akshara_render(ctx, x0, y, line_start);
}

// ── Setup ─────────────────────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    display.init(115200);
    display.setRotation(1);  // landscape: 296 × 128 px

    if (!SD.begin(SD_CS)) { Serial.println("SD init failed"); return; }

    File font_file = SD.open(FONT_FILE, FILE_READ);
    if (!font_file) { Serial.print("Cannot open "); Serial.println(FONT_FILE); return; }

    akshara_ctx_t ctx;
    int err = akshara_init(&ctx, read_sd, blit_gxepd2, &font_file, &display);
    if (err != AKS_OK) { Serial.print("akshara_init: "); Serial.println(err); return; }

    if (akshara_select_size(&ctx, LINE_SIZE, 0) != AKS_OK) {
        Serial.println("22px not found in font file");
        return;
    }

    int16_t max_w = display.width() - 2 * MARGIN;

    display.setFullWindow();
    display.firstPage();
    do {
        display.fillScreen(GxEPD_WHITE);
        render_paragraph(&ctx, MARGIN, MARGIN, TEXT, max_w, LINE_H);
    } while (display.nextPage());

    font_file.close();
    Serial.println("Done.");
}

void loop() {}
