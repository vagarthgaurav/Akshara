/*
 * akshara_st7789.ino — render Indic scripts on a 1.47" 172×320 ST7789 color TFT
 *
 * Uses 2bpp anti-aliased .aks fonts for smooth rendering on a color display.
 *
 * ── Hardware ──────────────────────────────────────────────────────────────────
 *
 * Tested on ESP32. Default SPI pin mapping (change in User_Setup.h if needed):
 *
 *   ST7789   →   ESP32
 *   VCC           3.3V
 *   GND           GND
 *   SCL           GPIO 18  (SCLK)
 *   SDA           GPIO 23  (MOSI)
 *   RES           GPIO 4   (RST)
 *   DC            GPIO 2
 *   CS            GPIO 5
 *   BLK           GPIO 32  (backlight, PWM or 3.3V)
 *
 * ── TFT_eSPI setup ────────────────────────────────────────────────────────────
 *
 * TFT_eSPI is configured via User_Setup.h in the library folder, NOT in sketch.
 * Edit <Arduino>/libraries/TFT_eSPI/User_Setup.h and set:
 *
 *   #define ST7789_DRIVER
 *   #define TFT_WIDTH  172
 *   #define TFT_HEIGHT 320
 *   #define TFT_MOSI   23
 *   #define TFT_SCLK   18
 *   #define TFT_CS      5
 *   #define TFT_DC      2
 *   #define TFT_RST     4
 *   #define SPI_FREQUENCY  40000000
 *
 * Comment out any other driver that was previously defined.
 *
 * ── Font generation ───────────────────────────────────────────────────────────
 *
 * Generate 2bpp .aks files for smooth anti-aliased rendering:
 *
 *   python akshara_gen.py --font NotoSansKannada-Regular.ttf \
 *                         --script kannada --size 20 --bpp 2 \
 *                         --output noto_kannada_regular_20.aks
 *   python akshara_gen.py --font NotoSansTamil-Regular.ttf \
 *                         --script tamil --size 20 --bpp 2 \
 *                         --output noto_tamil_regular_20.aks
 *   python akshara_gen.py --font NotoSansDevanagari-Regular.ttf \
 *                         --script devanagari --size 20 --bpp 2 \
 *                         --output noto_devanagari_regular_20.aks
 *   python akshara_gen.py --font NotoSansTelugu-Regular.ttf \
 *                         --script telugu --size 20 --bpp 2 \
 *                         --output noto_telugu_regular_20.aks
 *   python akshara_gen.py --font NotoSansMalayalam-Regular.ttf \
 *                         --script malayalam --size 20 --bpp 2 \
 *                         --output noto_malayalam_regular_20.aks
 *
 *   Size 20 fits ~14 lines on the 320px axis. Use 24 if you prefer larger text.
 *
 * Copy all .aks files to the root of a FAT-formatted SD card.
 *
 * Required libraries (Arduino Library Manager):
 *   - Akshara   (this library)
 *   - TFT_eSPI  (by Bodmer)
 *   - SD        (built-in)
 */

#include <TFT_eSPI.h>
#include <SD.h>
#include <Akshara.h>

static const int SD_CS = 10;

// ── Display ───────────────────────────────────────────────────────────────────

TFT_eSPI tft;

// ── Colour scheme ─────────────────────────────────────────────────────────────

static const uint16_t COLOR_BG   = TFT_BLACK;
static const uint16_t COLOR_TEXT = TFT_WHITE;

// Precomputed RGB565 grey ramp blended from COLOR_BG to COLOR_TEXT.
// Index = 2-bit grey level (0 = transparent, 3 = solid text colour).
// These values assume black background / white text; recalculate via
// tft.color565() if you change the colour scheme.
//   33%: color565(85, 85, 85)   = 0x52AA
//   66%: color565(170, 170, 170) = 0xAD55
static const uint16_t GREY_LUT[4] = { 0x0000, 0x52AA, 0xAD55, 0xFFFF };

// ── Callbacks ─────────────────────────────────────────────────────────────────

static int read_sd(uint32_t offset, uint8_t *buf, uint32_t size, void *ud) {
  File *f = (File *)ud;
  if (!f->seek(offset)) return AKS_ERR_IO;
  return (f->read(buf, size) == size) ? AKS_OK : AKS_ERR_IO;
}

// 1bpp: draw set pixels in COLOR_TEXT.
// 2bpp: blend each pixel through GREY_LUT; skip level 0 (background shows through).
static void blit_st7789(int16_t x, int16_t y, const uint8_t *bitmap,
                        uint16_t w, uint16_t h, uint8_t bpp, void *ud) {
  TFT_eSPI *d = (TFT_eSPI *)ud;

  if (bpp == 1) {
    uint8_t stride = (w + 7) / 8;
    for (uint16_t row = 0; row < h; row++)
      for (uint16_t col = 0; col < w; col++)
        if (bitmap[row * stride + col / 8] & (0x80u >> (col & 7)))
          d->drawPixel(x + col, y + row, COLOR_TEXT);

  } else if (bpp == 2) {
    // Row stride: ceil(width / 4) bytes; 2 bits per pixel, MSB first.
    uint8_t stride = (w + 3) / 4;
    for (uint16_t row = 0; row < h; row++) {
      for (uint16_t col = 0; col < w; col++) {
        uint8_t grey = (bitmap[row * stride + col / 4] >> (6 - (col & 3) * 2)) & 0x3;
        if (grey)
          d->drawPixel(x + col, y + row, GREY_LUT[grey]);
      }
    }
  }
}

// ── Akshara instance ──────────────────────────────────────────────────────────

Akshara akshara(blit_st7789, &tft);

// ── Script table ──────────────────────────────────────────────────────────────

struct ScriptEntry {
  const char *label;
  const char *sample;
  const char *filename;
};

static const ScriptEntry scripts[] = {
  { "ಕನ್ನಡ",   "ಭಾರತ ಭೂಮಿ",    "/noto_kannada_regular_20.aks"    },
  { "தமிழ்",   "இந்தியா",       "/noto_tamil_regular_20.aks"      },
  { "हिन्दी",  "भारत माता",     "/noto_devanagari_regular_20.aks" },
  { "తెలుగు",  "భారత దేశం",     "/noto_telugu_regular_20.aks"     },
  { "മലയാളം", "ഭാരതം",         "/noto_malayalam_regular_20.aks"  },
};

static const int NUM_SCRIPTS = (int)(sizeof(scripts) / sizeof(scripts[0]));
static const int FONT_SIZE   = 20;
static const int LINE_HEIGHT = FONT_SIZE + 4;   // 4px leading
static const int MARGIN_X    = 6;
static const int MARGIN_Y    = 10;
static const int DISPLAY_MS  = 3000;

// ── State ─────────────────────────────────────────────────────────────────────

static int  current_script = 0;
static File font_file;

// ── Helpers ───────────────────────────────────────────────────────────────────

static void show_script(int idx) {
  font_file.close();
  font_file = SD.open(scripts[idx].filename, FILE_READ);
  if (!font_file) {
    Serial.print("Cannot open ");
    Serial.println(scripts[idx].filename);
    return;
  }

  int err = akshara.setFont(read_sd, &font_file);
  if (err != AKS_OK) {
    Serial.print("setFont error: ");
    Serial.println(err);
    return;
  }

  tft.fillScreen(COLOR_BG);
  akshara.render(MARGIN_X, MARGIN_Y + LINE_HEIGHT,     scripts[idx].label);
  akshara.render(MARGIN_X, MARGIN_Y + LINE_HEIGHT * 2, scripts[idx].sample);
}

// ── Arduino entry points ──────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);

  tft.init();
  tft.setRotation(0);   // portrait; try 1 for landscape (320×172)
  tft.fillScreen(COLOR_BG);

  if (!SD.begin(SD_CS)) {
    Serial.println("SD init failed");
    tft.setTextColor(TFT_RED);
    tft.drawString("SD init failed", 10, 10, 2);
    return;
  }

  show_script(current_script);
}

void loop() {
  delay(DISPLAY_MS);
  current_script = (current_script + 1) % NUM_SCRIPTS;
  show_script(current_script);
}
