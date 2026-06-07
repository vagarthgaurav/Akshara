/*
 * akshara_u8g2.ino — render all five Indic scripts on a u8g2-compatible display,
 * cycling through each script every few seconds.
 *
 * ── Setup ─────────────────────────────────────────────────────────────────────
 *
 * 1. Generate the .aks font files (from the host/ directory):
 *
 *   python akshara_gen.py --font NotoSansKannada-Regular.ttf \
 *                         --script kannada --size 22 --bpp 1 \
 *                         --output noto_kannada_regular_22.aks
 *   python akshara_gen.py --font NotoSansTamil-Regular.ttf \
 *                         --script tamil --size 22 --bpp 1 \
 *                         --output noto_tamil_regular_22.aks
 *   python akshara_gen.py --font NotoSansDevanagari-Regular.ttf \
 *                         --script devanagari --size 22 --bpp 1 \
 *                         --output noto_devanagari_regular_22.aks
 *   python akshara_gen.py --font NotoSansTelugu-Regular.ttf \
 *                         --script telugu --size 22 --bpp 1 \
 *                         --output noto_telugu_regular_22.aks
 *   python akshara_gen.py --font NotoSansMalayalam-Regular.ttf \
 *                         --script malayalam --size 22 --bpp 1 \
 *                         --output noto_malayalam_regular_22.aks
 *
 *   Or use the Justfile (size=22 is the default):
 *     just script=kannada pack && just script=tamil pack && \
 *     just script=devanagari pack && just script=telugu pack && \
 *     just script=malayalam pack
 *
 *   Size 22 fits two script lines on a 128×64 display (44px content + margins).
 *   Use size=16 if you need more lines; use 24 for 128×128 or larger displays.
 *
 * 2. Copy all five .aks files to the root of a FAT-formatted SD card.
 *
 * 3. Connect the SD card via SPI and set SD_CS below.
 *
 * 4. Swap the U8G2 display constructor for your hardware (see comment below).
 *
 * Required libraries (Arduino Library Manager):
 *   - Akshara   (this library)
 *   - U8g2      (by oliver)
 *   - SD        (built-in)
 *
 * u8g2 works on AVR, ESP32, ESP8266, STM32, nRF52, RP2040, and more.
 * The display constructor is the only line that varies between hardware.
 */

#include <U8g2lib.h>
#include <SD.h>
#include <Akshara.h>

static const int SD_CS = 10;

// ── Display instance ──────────────────────────────────────────────────────────
// Swap this constructor for your display. Full list at:
//   https://github.com/olikraus/u8g2/wiki/u8g2setupcpp
//
// Common choices:
//   U8G2_SSD1306_128X64_NONAME_2_HW_I2C  — 128×64 OLED, I²C (most common)
//   U8G2_SSD1306_128X32_UNIVISION_2_HW_I2C
//   U8G2_SH1106_128X64_NONAME_2_HW_I2C
//   U8G2_ST7565_ERC12864_2_4W_HW_SPI     — 128×64 LCD, SPI
//   U8G2_SSD1327_MIDAS_128X128_2_HW_I2C  — 128×128 OLED (fits all 5 scripts at 24px)
//
// The _2_ variant (2-page buffer) balances RAM and refresh speed.
// Replace with _F_ for full frame buffer if you have the RAM.

U8G2_SSD1306_128X64_NONAME_2_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

// ── Callbacks ─────────────────────────────────────────────────────────────────

// ud must point to an open SD File object.
static int read_sd(uint32_t offset, uint8_t *buf, uint32_t size, void *ud) {
  File *f = (File *)ud;
  if (!f->seek(offset)) return AKS_ERR_IO;
  return (f->read(buf, size) == size) ? AKS_OK : AKS_ERR_IO;
}

// Akshara bitmaps are 1bpp MSB-first; u8g2's drawXBM expects LSB-first XBM
// format. Draw pixel-by-pixel to avoid bit-reversal. The per-cluster bitmap
// is small (≤ ~24×24 px at 16px font size) so this is fast enough.
static void blit_u8g2(int16_t x, int16_t y, const uint8_t *bitmap,
                      uint16_t w, uint16_t h, uint8_t bpp, void *ud) {
  U8G2 *u8 = (U8G2 *)ud;
  if (bpp != 1) return;  // 2bpp not supported on monochrome OLEDs
  uint8_t stride = (uint8_t)((w + 7) / 8);
  for (uint16_t row = 0; row < h; row++) {
    for (uint16_t col = 0; col < w; col++) {
      if (bitmap[row * stride + col / 8] & (0x80u >> (col & 7)))
        u8->drawPixel(x + (int16_t)col, y + (int16_t)row);
    }
  }
}

// ── Akshara instance ──────────────────────────────────────────────────────────
Akshara akshara(blit_u8g2, &u8g2);

// ── Script table ──────────────────────────────────────────────────────────────

struct ScriptEntry {
  const char *label;      // script name in its own script
  const char *sample;     // a short sample phrase
  const char *filename;   // .aks file on SD card
};

static const ScriptEntry scripts[] = {
  { "ಕನ್ನಡ",   "ಭಾರತ ಭೂಮಿ",     "/noto_kannada_regular_22.aks"    },
  { "தமிழ்",   "இந்தியா",        "/noto_tamil_regular_22.aks"      },
  { "हिन्दी",  "भारत माता",      "/noto_devanagari_regular_22.aks" },
  { "తెలుగు",  "భారత దేశం",      "/noto_telugu_regular_22.aks"     },
  { "മലയാളം", "ഭാരതം",          "/noto_malayalam_regular_22.aks"  },
};

static const int NUM_SCRIPTS  = (int)(sizeof(scripts) / sizeof(scripts[0]));
static const int LINE_HEIGHT   = 24;  // 22px font + 2px leading
static const int MARGIN_X      = 2;
static const int MARGIN_Y      = 2;
static const int DISPLAY_MS    = 2500; // ms to show each script

// ── State ─────────────────────────────────────────────────────────────────────
static int   current_script = 0;
static File  font_file;

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

  u8g2.firstPage();
  do {
    u8g2.clearBuffer();
    // Label line (script name)
    akshara.render(MARGIN_X, MARGIN_Y + LINE_HEIGHT, scripts[idx].label);
    // Sample phrase on next line
    akshara.render(MARGIN_X, MARGIN_Y + LINE_HEIGHT * 2, scripts[idx].sample);
  } while (u8g2.nextPage());
}

// ── Arduino entry points ──────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  u8g2.begin();

  if (!SD.begin(SD_CS)) {
    Serial.println("SD init failed");

    // Render an ASCII error message so the display is not blank.
    u8g2.firstPage();
    do {
      u8g2.setFont(u8g2_font_6x10_tf);
      u8g2.drawStr(0, 12, "SD init failed");
    } while (u8g2.nextPage());
    return;
  }

  show_script(current_script);
}

void loop() {
  delay(DISPLAY_MS);
  current_script = (current_script + 1) % NUM_SCRIPTS;
  show_script(current_script);
}
