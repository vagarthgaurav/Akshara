/*
 * akshara.c — single-file entry point for Arduino, PlatformIO, and any other
 * build system that expects one .c file per library.
 *
 * ── How to use ────────────────────────────────────────────────────────────
 *
 * Arduino / PlatformIO / single-file drop-in:
 *   Add akshara.c and Akshara.h to your project.  This file pulls in all four
 *   implementation files as a unity build.  Do NOT also compile aks_parser.c,
 *   segmenter.c, lookup.c, or blit.c — you will get duplicate symbol errors.
 *
 * Zephyr / ESP-IDF / FreeRTOS / CMake / Makefile / bare-metal:
 *   Add the four implementation files to your build target instead:
 *     aks_parser.c  segmenter.c  lookup.c  blit.c
 *   akshara.c is not needed and should not be compiled in these environments.
 *
 * ── Why no preprocessor guard? ───────────────────────────────────────────
 *
 * There is no portable way to make a .c file silently disappear when compiled
 * alongside an amalgamation — the linker would still see duplicate symbols.
 * Documentation is the right tool here; this is the same approach used by
 * FatFs, u8g2, and most embedded C libraries.
 */

#include "aks_parser.c"
#include "segmenter.c"
#include "lookup.c"
#include "blit.c"
