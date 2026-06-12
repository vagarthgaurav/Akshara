# Akshara aks-generator tool recipes
# Run from the project root: just <recipe>
# Requires: just, uv

host := "akshara-generator"
fonts_dir := "fonts"

# script is required — always pass it before the recipe name:
#   just script=tamil pack
# font defaults to fonts/original/NotoSans<Script>-Regular.ttf; override if needed.
script      := ""
font        := if script == "kannada"    { fonts_dir / "original/NotoSansKannada-Regular.ttf" } \
          else if script == "tamil"      { fonts_dir / "original/NotoSansTamil-Regular.ttf" } \
          else if script == "devanagari" { fonts_dir / "original/NotoSansDevanagari-Regular.ttf" } \
          else if script == "malayalam"  { fonts_dir / "original/NotoSansMalayalam-Regular.ttf" } \
          else if script == "telugu"     { fonts_dir / "original/NotoSansTelugu-Regular.ttf" } \
          else if script == "bengali"    { fonts_dir / "original/NotoSansBengali-Regular.ttf" } \
          else if script == "gujarati"    { fonts_dir / "original/NotoSansGujarati-Regular.ttf" } \
          else                           { "" }
sizes       := ""        # comma-separated pixel sizes (e.g. "16,22,24"); e.g. just script=kannada sizes=16,22 pack
bpp         := "1"
font_bold   := ""        # path to Bold weight font; enables Bold section in output
aks         := fonts_dir / "generated" / ("noto_" + script + "_regular.aks")
text        := ""
size        := ""        # font size in px for render-book (e.g. just size=22 render-book)
weight      := "0"       # font weight for render-book: 0=Regular 1=Bold
render_bpp  := ""        # bpp for render-book: 1 or 2 (default: any matching size+weight)

# Show available recipes
default:
    @just --list

# ── Pipeline ──────────────────────────────────────────────────────────────────

# Generate clusters, shape, rasterize, and pack a .aks file
# Usage: just script=tamil pack
#        just script=tamil sizes=16,22,24 pack
#        just script=kannada font_bold=fonts/original/NotoSansKannada-Bold.ttf sizes=16,22 pack
pack:
    cd {{host}} && uv run python packer.py \
        --font ../{{font}} \
        {{if font_bold != "" { "--font-bold ../" + font_bold } else { "" }}} \
        --script {{script}} \
        {{if sizes != "" { "--sizes " + sizes } else { "" }}} \
        --bpp {{bpp}} \
        --output ../{{aks}}
    just sync-arduino

# Sync runtime/ C source files into the Arduino library package.
# Run this after any edit to runtime/ to keep the two copies identical.
sync-arduino:
    cp runtime/Akshara.h runtime/aks_internal.h runtime/aks_parser.c runtime/segmenter.c runtime/lookup.c runtime/blit.c library-outputs/arduino/Akshara/src/

# Render a string to PNG using a .aks file (validates the packed output)
# Usage: just script=tamil render
render out="out.png":
    cd {{host}} && uv run python test/render_png.py \
        ../{{aks}} ../{{out}} \
        --words test/test-words/{{script}}.txt

# Pack then immediately render — useful for a quick visual check after rule changes
# Usage: just script=tamil build-and-render
#        just script=tamil build-and-render text="வணக்கம்"
build-and-render text="ನಮಸ್ಕಾರ ಕನ್ನಡ" out="out.png": pack
    just render text="{{text}}" out="{{out}}"

# Convert a .aks file to a C header for baking into firmware flash
# Usage: just script=tamil aks2h
#        just script=kannada aks2h array=NOTO_KANNADA
aks2h array="AKSHARA_FONT" header="noto_{{script}}_regular.h":
    cd {{host}} && uv run python aks2h.py \
        ../{{aks}} {{array}} > ../examples/akshara_gxepd2/{{header}}

# Render a plain-text book file as paginated PNGs (flowing text with word wrap)
# Usage: just script=kannada text=/path/to/book.txt render-book
#        just script=kannada text=/path/to/book.txt size=22 pages=50 out-dir=/tmp/pages render-book
#        just script=kannada text=/path/to/book.txt size=22 weight=1 render-book  # Bold
#        just script=kannada text=/path/to/book.txt size=22 render_bpp=2 render-book  # 2bpp
render-book out-dir="/tmp/aks_book" pages="5":
    cd {{host}} && uv run python test/render_book.py \
        ../{{aks}} {{text}} \
        --out-dir {{out-dir}} \
        --pages {{pages}} \
        {{ if size != "" { "--size " + size } else { "" } }} \
        --weight {{weight}} \
        {{ if render_bpp != "" { "--bpp " + render_bpp } else { "" } }}

# ── Testing ───────────────────────────────────────────────────────────────────

# Run all aks-generator tests
test:
    cd {{host}} && uv run pytest test/ -v

# Run only cluster enumeration tests
test-clusters:
    cd {{host}} && uv run pytest test/test_clusters.py -v

# Count clusters that would be generated (dry run, no rasterization)
# Usage: just script=tamil count-clusters
count-clusters:
    cd {{host}} && uv run python cluster_enum.py --script {{script}} --count

# ── Utilities ─────────────────────────────────────────────────────────────────

# Install Python dependencies
install:
    cd {{host}} && uv sync

# Print the resolved variable values (debug recipe substitution)
vars:
    @echo "font:   {{font}}"
    @echo "script: {{script}}"
    @echo "bpp:    {{bpp}}"
    @echo "aks:    {{aks}}"
