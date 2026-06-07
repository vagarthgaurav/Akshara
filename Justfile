# Akshara host tool recipes
# Run from the project root: just <recipe>
# Requires: just, uv

host := "host"
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
          else                           { "" }
size        := "24"
bpp         := "1"
aks         := fonts_dir / ("noto_" + script + "_regular_" + size + ".aks")

# Show available recipes
default:
    @just --list

# ── Pipeline ──────────────────────────────────────────────────────────────────

# Generate clusters, shape, rasterize, and pack a .aks file
# Usage: just script=tamil pack
#        just script=tamil size=16 pack
#        just script=tamil font=fonts/original/NotoSansTamil-Regular.ttf pack
pack:
    cd {{host}} && uv run python packer.py \
        --font ../{{font}} \
        --script {{script}} \
        --size {{size}} \
        --bpp {{bpp}} \
        --output ../{{aks}}

# Render a string to PNG using a .aks file (validates the packed output)
# Usage: just script=tamil render
#        just script=tamil size=16 render
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
#        just script=tamil size=16 aks2h array=NOTO_TAMIL_16
aks2h array="AKSHARA_FONT" header="noto_{{script}}_regular_{{size}}.h":
    cd {{host}} && uv run python aks2h.py \
        ../{{aks}} {{array}} > ../examples/akshara_gxepd2/{{header}}

# ── Testing ───────────────────────────────────────────────────────────────────

# Run all host-side tests
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
    @echo "size:   {{size}}"
    @echo "bpp:    {{bpp}}"
    @echo "aks:    {{aks}}"
