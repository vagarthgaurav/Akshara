/*
 * akshara_ili9341.ino — render Kannada on a 2.4" 240×320 ILI9341 TFT
 * Raspberry Pi Pico (RP2040) + Adafruit ILI9341 library
 *
 * Font is baked into flash as a C array — no SD card needed.
 *
 * ── Wiring ────────────────────────────────────────────────────────────────────
 *
 * ┌──────────────────┬──────────────┬─────────────┐
 * │  LCD Pin         │  Pico Pin    │  GPIO       │
 * ├──────────────────┼──────────────┼─────────────┤
 * │  VCC             │  3V3 (pin 36)│  —          │
 * │  GND             │  GND (pin 38)│  —          │
 * │  CLK (SCK)       │  Pin 24      │  GPIO 18    │
 * │  MOSI (DIN/SDA)  │  Pin 25      │  GPIO 19    │
 * │  CS              │  Pin 22      │  GPIO 17    │
 * │  DC (RS)         │  Pin 21      │  GPIO 16    │
 * │  RST             │  Pin 20      │  GPIO 15    │
 * │  BL (backlight)  │  3V3 or Pin 19│  GPIO 14  │
 * └──────────────────┴──────────────┴─────────────┘
 *
 * ── Required libraries (Arduino Library Manager) ─────────────────────────────
 *
 *   - Akshara             (this library)
 *   - Adafruit ILI9341    (by Adafruit)
 *   - Adafruit GFX Library(by Adafruit)
 *   - Adafruit BusIO      (by Adafruit)
 */

#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <SPI.h>
#include <Akshara.h>
#include "noto_kannada_regular_22.h"   // AKSHARA_FONT[]

// ── Display pins ──────────────────────────────────────────────────────────────
#define TFT_CS    17
#define TFT_DC    16
#define TFT_RST   15
#define TFT_BL    14

// ── Display object ────────────────────────────────────────────────────────────
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);

// ── Colour scheme ─────────────────────────────────────────────────────────────
static const uint16_t COLOR_BG   = ILI9341_WHITE;
static const uint16_t COLOR_TEXT = ILI9341_BLUE;

// Precomputed RGB565 ramp blending white bg (0xFFFF) → blue text (0x001F).
// Index = 2-bit level: 0=transparent, 1=33%, 2=66%, 3=solid.
// 33%: (171,171,255) → 0xAD5F   66%: (87,87,255) → 0x52BF
static const uint16_t GREY_LUT[4] = { 0xFFFF, 0xAD5F, 0x52BF, 0x001F };

// ── Akshara callbacks ─────────────────────────────────────────────────────────

// Flash read: ud points to the start of the AKSHARA_FONT array.
static int read_flash(uint32_t offset, uint8_t *buf, uint32_t size, void *ud) {
  memcpy(buf, (const uint8_t *)ud + offset, size);
  return AKS_OK;
}

// Supports both 1bpp (monochrome) and 2bpp (4-grey anti-aliased) .aks fonts.
static void blit_ili9341(int16_t x, int16_t y, const uint8_t *bitmap,
                         uint16_t w, uint16_t h, uint8_t bpp, void *ud) {
  Adafruit_ILI9341 *d = (Adafruit_ILI9341 *)ud;

  if (bpp == 1) {
    uint8_t stride = (w + 7) / 8;
    for (uint16_t row = 0; row < h; row++)
      for (uint16_t col = 0; col < w; col++)
        if (bitmap[row * stride + col / 8] & (0x80u >> (col & 7)))
          d->drawPixel(x + (int16_t)col, y + (int16_t)row, COLOR_TEXT);

  } else if (bpp == 2) {
    // Row stride: ceil(width / 4) bytes; 2 bits per pixel, MSB first.
    uint8_t stride = (w + 3) / 4;
    for (uint16_t row = 0; row < h; row++)
      for (uint16_t col = 0; col < w; col++) {
        uint8_t grey = (bitmap[row * stride + col / 4] >> (6 - (col & 3) * 2)) & 0x3;
        if (grey)
          d->drawPixel(x + (int16_t)col, y + (int16_t)row, GREY_LUT[grey]);
      }
  }
}

// ── Akshara instance ──────────────────────────────────────────────────────────
Akshara akshara(blit_ili9341, &tft);

static const int LINE_HEIGHT = 22 + 6;
static const int MARGIN_X    = 8;
static const int MARGIN_Y    = 20;

// ── Arduino entry points ──────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);

  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, HIGH);

  tft.begin();
  tft.setRotation(1);
  tft.fillScreen(COLOR_BG);

  // Pass NULL as read fn; AKSHARA_FONT pointer goes in read_ud — read_flash uses it.
  if (akshara.setFont(read_flash, (void *)AKSHARA_FONT) != AKS_OK) {
    Serial.println("setFont failed");
    tft.setTextColor(ILI9341_RED);
    tft.setTextSize(1);
    tft.setCursor(8, 80);
    tft.print("setFont failed");
    return;
  }

  akshara.render(MARGIN_X, MARGIN_Y,               "ಕನ್ನಡ");
  akshara.render(MARGIN_X, MARGIN_Y + LINE_HEIGHT, "ನಮಸ್ಕಾರ");
}

void loop() {}
