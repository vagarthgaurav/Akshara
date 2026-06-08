#!/usr/bin/env python3
"""
aks2h.py — convert a .aks binary to a C header suitable for baking into firmware.

Usage:
    python aks2h.py <input.aks> <array_name> [> output.h]

Example:
    python aks2h.py noto_kannada_regular_24.aks AKSHAR_FONT > ../examples/akshara_gxepd2/noto_kannada_regular_24.h
"""

import sys
from pathlib import Path


def aks2h(aks_path: Path, array_name: str) -> str:
    data = aks_path.read_bytes()
    size = len(data)

    # Wrap at 16 bytes per line for readability.
    chunks = [data[i : i + 16] for i in range(0, len(data), 16)]
    hex_lines = ",\n    ".join(
        ", ".join(f"0x{b:02x}" for b in chunk) for chunk in chunks
    )

    return (
        f"#pragma once\n"
        f"/* Generated from {aks_path.name} ({size} bytes) — do not edit. */\n"
        f"#include <stdint.h>\n"
        f"\n"
        f"static const uint8_t {array_name}[{size}] = {{\n"
        f"    {hex_lines}\n"
        f"}};\n"
    )


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    aks_path = Path(sys.argv[1])
    array_name = sys.argv[2]

    if not aks_path.exists():
        print(f"error: {aks_path} not found", file=sys.stderr)
        sys.exit(1)

    print(aks2h(aks_path, array_name), end="")


if __name__ == "__main__":
    main()
