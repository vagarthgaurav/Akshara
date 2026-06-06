# Akshara host tool recipes
# Run from the project root: just <recipe>
# Requires: just, uv

host := "host"
fonts_dir := "fonts"

# Default font paths — override on the command line:
#   just pack font=~/fonts/NotoSansKannada-Regular.ttf
font        := "~/fonts/NotoSansKannada-Regular.ttf"
script      := "kannada"
size        := "24"
bpp         := "1"
aks         := fonts_dir / ("noto_" + script + "_regular_" + size + ".aks")

# Show available recipes
default:
    @just --list

# ── Pipeline ──────────────────────────────────────────────────────────────────

# Generate clusters, shape, rasterize, and pack a .aks file
# Usage: just pack
#        just pack script=tamil size=16
#        just pack font=~/fonts/NotoSansTamil-Regular.ttf script=tamil size=16
pack:
    cd {{host}} && uv run python packer.py \
        --font {{font}} \
        --script {{script}} \
        --size {{size}} \
        --bpp {{bpp}} \
        --output ../{{aks}}

# Render a string to PNG using a .aks file (validates the packed output)
# Usage: just render
#        just render aks=fonts/noto_tamil_regular_16.aks
#        just render text="ನಮಸ್ಕಾರ"
render out="out.png":
    cd {{host}} && uv run python test/render_png.py \
        ../{{aks}} ../{{out}} \

# Pack then immediately render — useful for a quick visual check after rule changes
# Usage: just build-and-render
#        just build-and-render script=tamil text="வணக்கம்"
build-and-render text="ನಮಸ್ಕಾರ ಕನ್ನಡ" out="out.png": pack
    just render text="{{text}}" out="{{out}}"

# Convert a .aks file to a C header for baking into firmware flash
# Usage: just aks2h
#        just aks2h aks=fonts/noto_tamil_regular_16.aks array=NOTO_TAMIL_16
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
