/*
 * akshara_gxepd2.ino — render Kannada text on a GxEPD2 e-paper display.
 *
 * Two font source options (select one via #define below):
 *
 * Option A — font baked into firmware flash (default):
 *   cd host/
 *   python akshara_gen.py --font AnekKannada-Regular.ttf \
 *                        --script kannada --size 24 --bpp 1 \
 *                        --output anek_kannada.aks
 *   python aks2h.py anek_kannada.aks AKSHARA_FONT \
 *                   > ../examples/akshara_gxepd2/anek_kannada_aks.h
 *
 * Option B — font loaded from SD card at runtime:
 *   Copy anek_kannada.aks to the root of a FAT-formatted SD card.
 *   Connect SD via SPI and set SD_CS below.
 *
 * Required libraries (Arduino Library Manager):
 *   - Akshara   (this library)
 *   - GxEPD2   (by ZinggJM)
 *   - SD       (built-in, only needed for Option B)
 */

// ── Font source selection ─────────────────────────────────────────────────────
// Comment out AKSHARA_FONT_FROM_FLASH to load the font from SD card instead.
//#define AKSHARA_FONT_FROM_FLASH

#include <GxEPD2_BW.h>

#include <akshara.h>

#ifdef AKSHARA_FONT_FROM_FLASH
#include "anek_kannada_aks.h"
#else
#include <SD.h>
#endif

// ── SD card pin (Option B only) ───────────────────────────────────────────────
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
static const int EPD_CS = 3;
static const int EPD_DC = 2;
static const int EPD_RST = 1;
static const int EPD_BUSY = 0;
static const int EPD_SCK = 4;
static const int EPD_MOSI = 6;
static const int EPD_MISO = -1;

// ── Display instance ──────────────────────────────────────────────────────────
// 4 Greyscale display
// GxEPD2_4G_4G<GxEPD2_290_T94, GxEPD2_290_T94::HEIGHT> display(
//   GxEPD2_290_T94(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY)
//);

// Weact studio display
GxEPD2_BW<GxEPD2_290_BS, GxEPD2_290_BS::HEIGHT>
  display(GxEPD2_290_BS(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

// ── Read callback: font array in flash ────────────────────────────────────────
static int read_flash(uint32_t offset, uint8_t *buf, uint32_t size, void *ud) {
  memcpy(buf, (const uint8_t *)ud + offset, size);
  return AKS_OK;
}

// ── Read callback: .aks file on SD card ───────────────────────────────────────
// ud must point to an open SD File object. Each call seeks then reads; this is
// fine for e-paper where display refresh dominates latency.
#ifndef AKSHARA_FONT_FROM_FLASH
static int read_sd(uint32_t offset, uint8_t *buf, uint32_t size, void *ud) {
  File *f = (File *)ud;
  if (!f->seek(offset))
    return AKS_ERR_IO;
  uint32_t got = f->read(buf, size);
  return (got == size) ? AKS_OK : AKS_ERR_IO;
}
#endif
// ── Blit callback: GxEPD2 via Adafruit_GFX ───────────────────────────────────
// bitmap is 1bpp, rows MSB-first, stride = ceil(w/8) bytes — same layout as
// Adafruit_GFX::drawBitmap, so no conversion needed.
static void blit_gxepd2(int16_t x, int16_t y, const uint8_t *bitmap,
                        uint16_t w, uint16_t h, uint8_t bpp, void *ud) {
  Adafruit_GFX *gfx = (Adafruit_GFX *)ud;
  if (bpp == 1)
    gfx->drawBitmap(x, y, (uint8_t *)bitmap,
                    (int16_t)w, (int16_t)h, GxEPD_BLACK);
}

void setup() {
  Serial.begin(115200);
  display.init(115200);
  display.setRotation(1);

  akshara_ctx_t ctx;
  int err;

#ifdef AKSHARA_FONT_FROM_FLASH
  err = akshara_init(&ctx,
                    read_flash, blit_gxepd2,
                    (void *)anek_kannada_aks, &display);
#else
  if (!SD.begin(SD_CS)) {
    Serial.println("SD init failed");
    return;
  }
  File font_file = SD.open("/baloo_kannada.aks", FILE_READ);
  if (!font_file) {
    Serial.println("Cannot open /baloo_kannada.aks");
    return;
  }
  err = akshara_init(&ctx,
                    read_sd, blit_gxepd2,
                    &font_file, &display);
#endif

  if (err != AKS_OK) {
    Serial.print("akshara_init error: ");
    Serial.println(err);
#ifndef AKSHARA_FONT_FROM_FLASH
    font_file.close();
#endif
    return;
  }

  const char *line1 = "ಕನ್ನಡ ಸಾಹಿತ್ಯ";
  const char *line2 = "ಬೆಳಕಿನ ಹಾದಿಯಲ್ಲಿ";

  display.setFullWindow();
  display.firstPage();
  do {
    display.fillScreen(GxEPD_WHITE);
    akshara_render(&ctx, 10, 20, line1);
    akshara_render(&ctx, 10, 60, line2);
  } while (display.nextPage());

  Serial.println("Done.");

#ifndef AKSHARA_FONT_FROM_FLASH
  font_file.close();
#endif
}

void loop() {}
