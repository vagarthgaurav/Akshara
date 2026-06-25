# Akshara

Akshara is a lightweight Indic script rendering library for microcontrollers. It renders Kannada, Tamil, Hindi, Telugu, Malayalam, Bengali, and Gujarati correctly on any C99 target, including conjuncts and vowel signs. Each font context uses around 100 bytes of RAM. There is no OS dependency, no malloc, and no HarfBuzz at runtime.

Rendering Indic text on a microcontroller is difficult because each consonant can combine with others into conjuncts, and some vowel signs appear on the opposite side from their Unicode position. A correct render requires a shaping engine like HarfBuzz, which is impractical on constrained hardware. Akshara moves all the shaping work to build time: HarfBuzz runs once on your desktop, and its output is frozen into a `.aks` file. At runtime the MCU looks up pre-shaped glyph clusters, reads the bitmap, and calls your blit callback. You provide the file-reading and rendering code for whatever display library you're using, such as GxEPD2, U8g2, or ST7789.

---

## Supported scripts

The library ships with pre-generated Noto Sans fonts (OFL Licensed) for all supported scripts. Each `.aks` file contains four sizes (16px, 20px, 22px, 24px).

| Script | Language | Pre-generated font | .aks size |
| ------ | -------- | ------------------ | --------- |
| Kannada | ಕನ್ನಡ | Noto Sans Kannada | 96 KB |
| Tamil | தமிழ் | Noto Sans Tamil | 70 KB |
| Devanagari | Several | Noto Sans Devanagari | 103 KB |
| Telugu | తెలుగు | Noto Sans Telugu | 139 KB |
| Malayalam | മലയാളം | Noto Sans Malayalam | 80 KB |
| Bengali | বাংলা | Noto Sans Bengali | 84 KB |
| Gujarati | ગુજરાતી | Noto Sans Gujarati | 87 KB |

> File sizes above are for four sizes (16/20/22/24 px), Regular weight, 1 bpp.

---

## Generating a font file

Not all projects need all four sizes, and you may want a different typeface instead of Noto Sans. The `akshara-generator` tool handles this. It is a separate GitHub repo with more detail on usage.

You need Python 3.10+, [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just) on your machine.

```bash
git clone --recurse-submodules https://github.com/vagarthgaurav/akshara.git
cd akshara
just script=kannada pack
```

This generates `fonts/generated/noto_kannada_regular.aks` using the bundled Noto Sans font. Swap `kannada` for any supported script name.

To pack custom sizes:

```bash
# Noto sans font in custom sizes
just script=kannada sizes=12,32 pack
```

To use your own TTF instead of Noto Sans, pass `font=` and `aks=` to override the defaults:

```bash
# Your own .ttf font in a single size

just script=kannada font=path/to/MyKannada-Regular.ttf aks=fonts/generated/my_kannada.aks sizes=16 pack
```

Both `font` and `aks` must be provided together. `aks` sets the output path, so omitting it would overwrite `noto_kannada_regular.aks` even when using a custom font.

## Arduino

### Install the library

Download the latest release ZIP from the [Releases](https://github.com/vagarthgaurav/akshara/releases) page, then in the Arduino IDE go to **Sketch → Include Library → Add .ZIP Library** and select it.

### Load from SD card

Copy the generated `.aks` file to the root of a FAT-formatted SD card, then wire up two callbacks (one to read the font file, one to draw bitmaps) and call `akshara_render`. See `examples/arduino/akshara_gxepd2/` for a complete GxEPD2 example including multi-size rendering.

### Bake the font into firmware flash (no SD card)

For boards without an SD card, convert the `.aks` file to a C header using `aks2h.py`, then include it in your sketch and pass `NULL` as the read callback with the array pointer as `read_ud`. See `examples/arduino/flash/` for a complete example.

### Supported display libraries

Akshara uses a blit callback, so it works with any display library. The included examples cover:

- GxEPD2 (e-paper)
- U8g2 (monochrome OLEDs and LCDs)
- ST7789 and Adafruit GFX (colour TFT)
- ILI9341 (colour TFT)

---

## Complexity of Indic script

Indic scripts are *abugidas*: each consonant carries an inherent vowel that is modified or suppressed by specific vowel signs. Unicode encodes these scripts in phonetic order, not visual order, so a rendering engine must reorder, merge, and substitute glyphs before drawing any pixels. On a desktop OS this is handled transparently by [HarfBuzz](https://github.com/harfbuzz/harfbuzz). On a microcontroller with no shaping engine, three things break.

**Conjunct consonants.** When two consonants are joined by a virama (vowel suppressor), they fuse into a single ligature glyph. Without shaping, the virama appears as a visible floating mark and the consonants remain separate.

**Vowel sign order.** Some vowel signs attach to the left of a consonant even though they follow it in Unicode codepoint order (Tamil ி, ீ; Malayalam ൊ, ോ). A naive renderer draws in codepoint order and places them on the wrong side.

**Contextual glyph forms.** Many consonants change shape depending on what follows: half-forms in Devanagari, below-base and post-base forms in Kannada and Telugu. Without a shaper, none of these substitutions happen.

---

### Example 1: Kannada "ಕನ್ನಡ" (the script's own name)

The middle cluster **ನ್ನ** is: NA + virama (U+0CCD) + NA. These two consonants fuse into one ligature glyph with the virama invisible.

| | Glyph sequence drawn |
| --- | --- |
| Without Akshara | `ಕ` `ನ` `್` `ನ` `ಡ`: five separate items (್ floats visibly between the two NAs) |
| With Akshara | `ಕ` `ನ್ನ` `ಡ`: three clusters (the conjunct glyph is looked up and blitted as one unit) |

---

### Example 2: Devanagari "नमस्ते" (namaste)

The cluster **स्त** is: SA + virama (U+094D) + TA. SA drops to its half-form स् and fuses with TA. The vowel sign **े** (E) then attaches to the right of the conjunct.

| | Glyph sequence drawn |
| --- | --- |
| Without Akshara | `न` `म` `स` `्` `त` `े`: six separate items (virama floats, no ligature, vowel sign detached) |
| With Akshara | `न` `म` `स्ते`: three clusters (SA+virama+TA collapses to the स्त half-form and े attaches correctly) |

---

### Example 3: Tamil "தமிழ்" (Tamil, the language's own name)

The vowel sign **ி** (I, U+0BBF) attaches to the *left* of the consonant ம even though it follows it in Unicode order. The pulli **்** (virama, U+0BCD) marks ழ as a final consonant.

| | Glyph sequence drawn |
| --- | --- |
| Without Akshara | `த` `ம` `ி` `ழ` `்`: ி lands to the right of ம (wrong side); ் floats as a bare diacritic |
| With Akshara | `த` `மி` `ழ்`: ி is positioned to the left of ம; ் appears as the pulli mark on ழ |

---

### Example 4: Kannada "ನಮಸ್ಕಾರ" (namaskāra / hello)

A longer word containing **ಸ್ಕಾ**: SA + virama + KA + AA vowel sign, a three-codepoint conjunct cluster with an attached vowel sign.

| | Glyph sequence drawn |
| --- | --- |
| Without Akshara | `ನ` `ಮ` `ಸ` `್` `ಕ` `ಾ` `ರ`: seven separate items (virama floats, vowel sign detached from its consonant) |
| With Akshara | `ನ` `ಮ` `ಸ್ಕಾ` `ರ`: four clusters (SA+virama+KA+AA is a single pre-shaped glyph) |

---

### Example 5: Malayalam "ആൾക്കൂട്ടം" (āḷkkūṭṭam / crowd)

This word has a chillu and two conjunct consonants, both specific to Malayalam rendering.

**ൾ** (U+0D7E) is a *chillu*: an atomic codepoint for a pure final-LL with no inherent vowel. Unlike a consonant + virama pair, a chillu is a single Unicode character that falls outside the consonant range (U+0D15–U+0D39), so the segmenter treats it directly as a one-codepoint cluster. **ക്കൂ** is KA + virama + KA + UU vowel sign, a geminate conjunct with an attached vowel. **ട്ടം** is TTA + virama + TTA + anusvara, another geminate with a modifier.

| | Glyph sequence drawn |
| --- | --- |
| Without Akshara | `ആ` `ൾ` `ക` `്` `ക` `ൂ` `ട` `്` `ട` `ം`: ten separate items (viramas float visibly, ക്ക and ട്ട remain unjoined) |
| With Akshara | `ആ` `ൾ` `ക്കൂ` `ട്ടം`: four clusters (ൾ looked up as an atomic single-codepoint cluster, both conjuncts formed correctly) |

---

Akshara avoids all of this at runtime by pre-computing the most-used combinations at build time. HarfBuzz runs once on your desktop to shape clusters for your chosen font, and the results are frozen into a `.aks` file. On the MCU, rendering a word is: segment → binary search → blit. The runtime has no shaping logic, no substitution tables, and no reordering engine.

## Conclusion

The diversity of languages and scripts gives us the opportunity to convey ideas, emotions, and stories. When I wanted to render an Indic font in my own project I quickly realised that there were very few options, and the ones that existed made text barely readable. This led me down a rabbit hole about languages, scripts, and how they work in a digital system. My hope with this project is that as many people as possible can use this in their own embedded projects and hopefully lower the barrier for people who do not natively read English.

This library is not limited to Indic scripts. Any abugida can be ported to it. As much as I would like to, I cannot read or understand all of them, but I am actively researching more scripts to add. Contributions are highly welcome. Please feel free to make a pull request.

## Glossary

Most of these terms come from linguistics or the Unicode standard. They appear throughout the documentation and the source code.

**Abugida**: a writing system where consonants are the primary unit and vowels are written as marks attached to them. Indic scripts are all abugidas. An alphabet treats vowels as full letters; a syllabary gives each symbol a whole syllable; an abugida does neither.

**Akshara**: Sanskrit for "letter" or "syllable", and the name of this library. In Indic script contexts it refers to one orthographic syllable: a consonant (or consonant cluster) with any attached vowel and modifier marks. In the library, one akshara is one pre-shaped unit that gets looked up and blitted.

**Consonant**: a base letter such as ಕ (KA in Kannada) or ক (KA in Bengali). Every consonant carries an *inherent vowel* (usually "a") unless it is explicitly suppressed or replaced by a vowel sign.

**Independent vowel**: a vowel written as a standalone letter at the start of a word or syllable, such as ಅ (A) or ಆ (AA). These appear as single-codepoint clusters.

**Vowel sign (dependent vowel)**: a diacritic mark that replaces the inherent vowel of a consonant. For example, ಕಾ is KA + the AA vowel sign (ಾ). Vowel signs never appear alone; they always attach to a consonant.

**Virama**: a mark that *suppresses* the inherent vowel of a consonant, leaving a pure consonant sound. When a virama sits between two consonants, they fuse into a conjunct. In Tamil it is called *pulli*; in Hindi/Devanagari, *halant*. Unicode encodes it as a combining character after the consonant it affects (e.g. U+0CCD for Kannada, U+094D for Devanagari).

**Conjunct consonant**: a ligature formed when two or more consonants are joined by a virama. The virama becomes invisible and the consonants merge into a single glyph. For example, ನ + ್ + ನ → ನ್ನ (the double-NA in ಕನ್ನಡ). Without a shaping engine, the virama appears as a floating mark and no ligature forms.

**Anusvara**: a small circle or dot placed above a letter, representing a nasal sound. It appears in most Indic scripts: ಂ in Kannada, ं in Devanagari, ং in Bengali. Unicode encodes it as a combining character after the base letter.

**Visarga**: two dots placed after a letter, representing an aspirated breath sound (similar to a final "h"). It looks like a colon: ಃ in Kannada, ः in Devanagari.

**Chandrabindu**: a crescent-moon-with-dot mark used in Devanagari and a few other scripts to indicate nasalisation (ँ). Like anusvara and visarga, it is a combining character.

**Nukta**: a small dot placed below a consonant in Devanagari to represent sounds borrowed from Persian and Arabic (क़, ख़, ग़, etc.). Not all scripts have one.

**Chillu**: a Malayalam-specific form of certain consonants that appear in final position with no inherent vowel and no virama. Unicode 5.1 assigned dedicated atomic codepoints for chillus (U+0D7A–U+0D7F). Each is treated as a single-codepoint cluster and does not follow the consonant + virama pattern.

**Half-form**: a reduced form of a consonant used in conjuncts, most common in Devanagari. When HA (ह) precedes another consonant, for example, it becomes ह्, which attaches to what follows. HarfBuzz selects these forms automatically during shaping.

## References

- [HarfBuzz](https://github.com/harfbuzz/harfbuzz): the open-source text shaping engine that runs on the host to produce the pre-shaped glyph clusters frozen into `.aks` files. Akshara owes its correctness to HarfBuzz; it just moves the work off the MCU.
- [BanglaText](https://github.com/mamunul/BanglaText): proved that the pre-shaping architecture works in practice: shape Bengali clusters on a desktop, freeze the output, look up and blit on an ESP32. Akshara generalises this approach to the other scripts and any C99 target.
- [FreeType](https://freetype.org): used by the host generator to rasterise individual glyphs into the 1 bpp / 2 bpp bitmaps packed into `.aks` files.
- [Noto Sans](https://fonts.google.com/noto): the OFL-licensed font family used for all pre-generated `.aks` files. Covers all seven supported scripts with consistent metrics and broad glyph coverage.
- [Unicode Standard](https://www.unicode.org/versions/latest/): the encoding model (abugida phonetic order, virama mechanics, independent/dependent vowels) that Akshara's segmenter implements.
- [LVGL](https://lvgl.io): the popular embedded graphics library whose limited Indic shaping support is the primary gap Akshara addresses.
- [uharfbuzz](https://github.com/harfbuzz/uharfbuzz): Python bindings for HarfBuzz used in the `akshara-generator` shaping stage.
- [freetype-py](https://github.com/rougier/freetype-py): Python bindings for FreeType used in the `akshara-generator` rasterisation stage.

---

## License

Akshara runtime is licensed under the [Apache License 2.0](LICENSE). You may use, modify, and distribute it freely in personal, commercial, and closed-source projects, including shipping it in commercial hardware products. Apache 2.0 includes an explicit patent grant: contributors grant you a license to any patents covering their contributions, which gives more legal certainty than MIT for companies embedding the library in firmware. You must retain the license notice and attribution in any distribution, and state what changes you made to modified files. The Noto Sans font files are licensed under the [SIL Open Font License 1.1](https://scripts.sil.org/OFL).
