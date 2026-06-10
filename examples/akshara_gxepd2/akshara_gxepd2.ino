/*
 * akshara_gxepd2.ino — render an Indic script at every size embedded in one .aks file.
 *
 * akshara_get_sizes() discovers all size+weight variants packed into the file;
 * the same sample text is rendered once per size, stacked top-to-bottom.
 *
 * ── Generate the font file ────────────────────────────────────────────────────
 *
 * Single size (default 22px):
 *   just script=kannada pack
 *
 * Multiple sizes in one file:
 *   just script=kannada sizes=16,20,22 pack
 *
 * The output is written to fonts/generated/noto_kannada_regular.aks.
 * Copy the .aks file to the root of a FAT-formatted SD card.
 *
 * ── Required libraries ────────────────────────────────────────────────────────
 *   Akshara  (this library)
 *   GxEPD2   (ZinggJM)
 *   SD       (built-in)
 */

#include <GxEPD2_BW.h>
#include <SD.h>
#include <Akshara.h>

static const int  SD_CS     = 10;

// ── Language selection ────────────────────────────────────────────────────────
// Change LANGUAGE to switch scripts. Generate the font with:
//   just script=<name> sizes=16,20,22 pack
#define LANG_KANNADA    0
#define LANG_DEVANAGARI 1
#define LANG_TAMIL      2
#define LANG_TELUGU     3
#define LANG_MALAYALAM  4
#define LANG_BENGALI    5
#define LANG_GUJARATI   6

#define LANGUAGE LANG_KANNADA

#if   LANGUAGE == LANG_KANNADA
  static const char FONT_FILE[]   = "/noto_kannada_regular.aks";
  static const char SAMPLE_TEXT[] = "ಕನ್ನಡ ಭಾಷೆ";
#elif LANGUAGE == LANG_DEVANAGARI
  static const char FONT_FILE[]   = "/noto_devanagari_regular.aks";
  static const char SAMPLE_TEXT[] = "हिन्दी भाषा";
#elif LANGUAGE == LANG_TAMIL
  static const char FONT_FILE[]   = "/noto_tamil_regular.aks";
  static const char SAMPLE_TEXT[] = "தமிழ் மொழி";
#elif LANGUAGE == LANG_TELUGU
  static const char FONT_FILE[]   = "/noto_telugu_regular.aks";
  static const char SAMPLE_TEXT[] = "తెలుగు భాష";
#elif LANGUAGE == LANG_MALAYALAM
  static const char FONT_FILE[]   = "/noto_malayalam_regular.aks";
  static const char SAMPLE_TEXT[] = "മലയാളം ഭാഷ";
#elif LANGUAGE == LANG_BENGALI
  static const char FONT_FILE[]   = "/noto_bengali_regular.aks";
  static const char SAMPLE_TEXT[] = "বাংলা ভাষা";
#elif LANGUAGE == LANG_GUJARATI
  static const char FONT_FILE[]   = "/noto_gujarati_regular.aks";
  static const char SAMPLE_TEXT[] = "ગુજરાતી ભાષા";
#endif

// ── Pin definitions ───────────────────────────────────────────────────────────
// NRF52840
// static const int EPD_CS   = 16;
// static const int EPD_DC   = 15;
// static const int EPD_RST  = 14;
// static const int EPD_BUSY = 13;
// static const int EPD_SCK  = 2;
// static const int EPD_MOSI = 4;
// static const int EPD_MISO = -1;

// ESP32-C3
static const int EPD_CS   = 3;
static const int EPD_DC   = 2;
static const int EPD_RST  = 1;
static const int EPD_BUSY = 0;
static const int EPD_SCK  = 4;
static const int EPD_MOSI = 6;
static const int EPD_MISO = -1;

// ── Display instance ──────────────────────────────────────────────────────────
GxEPD2_BW<GxEPD2_290_BS, GxEPD2_290_BS::HEIGHT>
    display(GxEPD2_290_BS(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

// ── Callbacks ─────────────────────────────────────────────────────────────────

static int read_sd(uint32_t offset, uint8_t *buf, uint32_t size, void *ud) {
    File *f = (File *)ud;
    if (!f->seek(offset)) return AKS_ERR_IO;
    return (f->read(buf, size) == size) ? AKS_OK : AKS_ERR_IO;
}

// bitmap is 1bpp, MSB-first, stride = ceil(w/8) — matches Adafruit_GFX::drawBitmap.
static void blit_gxepd2(int16_t x, int16_t y, const uint8_t *bitmap,
                         uint16_t w, uint16_t h, uint8_t bpp, void *ud) {
    Adafruit_GFX *gfx = (Adafruit_GFX *)ud;
    if (bpp == 1)
        gfx->drawBitmap(x, y, bitmap, (int16_t)w, (int16_t)h, GxEPD_BLACK);
}

// ── Setup ─────────────────────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    display.init(115200);
    display.setRotation(1);  // landscape: 296 × 128

    if (!SD.begin(SD_CS)) { Serial.println("SD init failed"); return; }

    File font_file = SD.open(FONT_FILE, FILE_READ);
    if (!font_file) { Serial.print("Cannot open "); Serial.println(FONT_FILE); return; }

    akshara_ctx_t ctx;
    int err = akshara_init(&ctx, read_sd, blit_gxepd2, &font_file, &display);
    if (err != AKS_OK) { Serial.print("akshara_init: "); Serial.println(err); return; }

    // Discover all size+weight variants packed into this .aks file.
    aks_size_info_t sizes[8];
    int n = akshara_get_sizes(&ctx, sizes, 8);
    if (n < 0) { Serial.print("akshara_get_sizes: "); Serial.println(n); return; }

    display.setFullWindow();
    display.firstPage();
    do {
        display.fillScreen(GxEPD_WHITE);

        int16_t y = 4;
        for (int i = 0; i < n; i++) {
            if (akshara_select_size(&ctx, sizes[i].size_px, sizes[i].weight) != AKS_OK)
                continue;
            akshara_render(&ctx, 10, y, SAMPLE_TEXT);
            y += sizes[i].size_px + 4;  // advance by nominal size + 4px gap
        }
    } while (display.nextPage());

    font_file.close();
    Serial.println("Done.");
}

void loop() {}
