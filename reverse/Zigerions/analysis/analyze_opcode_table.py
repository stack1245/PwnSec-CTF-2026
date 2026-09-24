#!/usr/bin/env python3
"""Inspect bit-level steganography candidates in the ROM's opcode metadata."""

from __future__ import annotations

import struct
from pathlib import Path


ROM = Path(__file__).resolve().parent / "AURA.gb"


def cstring(blob: bytes, offset: int) -> str:
    return blob[offset:blob.index(0, offset)].decode("ascii")


def pack(bits: list[int], lsb_first: bool) -> bytes:
    output = bytearray()
    for offset in range(0, len(bits) - 7, 8):
        value = 0
        for index, bit in enumerate(bits[offset:offset + 8]):
            value |= bit << (index if lsb_first else 7 - index)
        output.append(value)
    return bytes(output)


def main() -> None:
    blob = ROM.read_bytes()
    rows = []
    for offset in range(0xAF3, 0xE3B, 6):
        name_ptr, opcode, delta, category_ptr = struct.unpack_from("<HBbH", blob, offset)
        rows.append({
            "name": cstring(blob, name_ptr),
            "category": cstring(blob, category_ptr),
            "name_ptr": name_ptr,
            "category_ptr": category_ptr,
            "opcode": opcode,
            "delta": delta,
        })

    candidates = {
        "name-length": [len(row["name"]) & 1 for row in rows],
        "suffix-length": [len(row["name"].removeprefix("VMOP_")) & 1 for row in rows],
        "name-pointer": [row["name_ptr"] & 1 for row in rows],
        "category-pointer": [row["category_ptr"] & 1 for row in rows],
        "opcode": [row["opcode"] & 1 for row in rows],
        "delta": [row["delta"] & 1 for row in rows],
    }
    for label, bits in candidates.items():
        for reverse in (False, True):
            selected = bits[::-1] if reverse else bits
            for invert in (False, True):
                transformed = [bit ^ invert for bit in selected]
                for lsb_first in (False, True):
                    data = pack(transformed, lsb_first)
                    printable = sum(32 <= value < 127 for value in data)
                    if b"psctf" in data.lower() or printable >= len(data) - 2:
                        print(label, "reverse", reverse, "invert", invert, "lsb", lsb_first, repr(data))


if __name__ == "__main__":
    main()
