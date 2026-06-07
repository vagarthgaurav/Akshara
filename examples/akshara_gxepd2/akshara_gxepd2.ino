/*
 * akshara_gxepd2.ino — render all five Indic scripts on a GxEPD2 e-paper display,
 * demonstrating runtime font switching with setFont().
 *
 * ── Setup ─────────────────────────────────────────────────────────────────────
 *
 * 1. Generate the .aks font files (from the host/ directory):
 *
 *   python akshara_gen.py --font NotoSansKannada-Regular.ttf \
 *                         --script kannada --size 24 --bpp 1 \
 *                         --output noto_kannada_regular_24.aks
 *   python akshara_gen.py --font NotoSansTamil-Regular.ttf \
 *                         --script tamil --size 24 --bpp 1 \
 *                         --output noto_tamil_regular_24.aks
 *   python akshara_gen.py --font NotoSansDevanagari-Regular.ttf \
 *                         --script devanagari --size 24 --bpp 1 \
 *                         --output noto_devanagari_regular_24.aks
 *   python akshara_gen.py --font NotoSansTelugu-Regular.ttf \
 *                         --script telugu --size 24 --bpp 1 \
 *                         --output noto_telugu_regular_24.aks
 *   python akshara_gen.py --font NotoSansMalayalam-Regular.ttf \
 *                         --script malayalam --size 24 --bpp 1 \
 *                         --output noto_malayalam_regular_24.aks
 *
 * 2. Copy all five .aks files to the root of a FAT-formatted SD card.
 *
 * 3. Connect the SD card via SPI and set SD_CS below.
 *
 * Required libraries (Arduino Library Manager):
 *   - Akshara   (this library)
 *   - GxEPD2   (by ZinggJM)
 *   - SD       (built-in)
 */

#include <GxEPD2_BW.h>
#include <SD.h>
#include <Akshara.h>

static const int SD_CS = 10;

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

// ud must point to an open SD File object.
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
    gfx->drawBitmap(x, y, (const uint8_t *)bitmap,
                   (int16_t)w, (int16_t)h, GxEPD_BLACK);
}

// ── Akshara instance ──────────────────────────────────────────────────────────
Akshara akshara(blit_gxepd2, &display);

// ── Font + sample text table ──────────────────────────────────────────────────

struct ScriptEntry {
  const char *label;     // script name in its own script
  const char *filename;  // .aks file on SD card
};

static const ScriptEntry scripts[] = {
  { "ಕನ್ನಡ",   "/noto_kannada_regular_24.aks"    },
  { "தமிழ்",   "/noto_tamil_regular_24.aks"      },
  { "हिन्दी",  "/noto_devanagari_regular_24.aks" },
  { "తెలుగు",  "/noto_telugu_regular_24.aks"     },
  { "മലയാളം", "/noto_malayalam_regular_24.aks"  },
};

static const int NUM_SCRIPTS = sizeof(scripts) / sizeof(scripts[0]);
static const int LINE_HEIGHT = 24;  // matches --size 24 passed to akshara_gen.py
static const int MARGIN_X    = 10;
static const int MARGIN_Y    = 4;

void setup() {
  Serial.begin(115200);
  display.init(115200);
  display.setRotation(1);  // landscape: 296 × 128

  if (!SD.begin(SD_CS)) {
    Serial.println("SD init failed");
    return;
  }

  File font_files[NUM_SCRIPTS];

  display.setFullWindow();
  display.firstPage();
  do {
    display.fillScreen(GxEPD_WHITE);

    for (int i = 0; i < NUM_SCRIPTS; i++) {
      font_files[i] = SD.open(scripts[i].filename, FILE_READ);
      if (!font_files[i]) {
        Serial.print("Cannot open "); Serial.println(scripts[i].filename);
        continue;
      }
      int err = akshara.setFont(read_sd, &font_files[i]);
      if (err != AKS_OK) {
        Serial.print("akshara.setFont error: "); Serial.println(err);
        continue;
      }
      akshara.render(MARGIN_X, MARGIN_Y + i * LINE_HEIGHT, scripts[i].label);
    }
  } while (display.nextPage());

  for (int i = 0; i < NUM_SCRIPTS; i++)
    font_files[i].close();

  Serial.println("Done.");
}

void loop() {}
