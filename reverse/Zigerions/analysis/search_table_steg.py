#!/usr/bin/env python3
"""Search simple encodings of the unreachable opcode metadata table."""

from __future__ import annotations

import itertools
import string
import struct
from pathlib import Path


ROM = Path(__file__).resolve().parent / "AURA.gb"
TARGET = b"psctf{"


def cstring(blob: bytes, offset: int) -> str:
    return blob[offset:blob.index(0, offset)].decode("ascii")


def packed_bits(bits: list[int], lsb: bool, skip: int) -> bytes:
    bits = bits[skip:]
    output = bytearray()
    for offset in range(0, len(bits) - 7, 8):
        value = 0
        for index, bit in enumerate(bits[offset:offset + 8]):
            value |= bit << (index if lsb else 7 - index)
        output.append(value)
    return bytes(output)


def report(label: str, data: bytes) -> None:
    lower = data.lower()
    if TARGET in lower:
        print("TARGET", label, repr(data))
        return
    longest = b""
    current = bytearray()
    for value in data + bytes([0]):
        if value in b"\r\n\t" or 32 <= value < 127:
            current.append(value)
        else:
            if len(current) > len(longest):
                longest = bytes(current)
            current.clear()
    if len(longest) >= 12:
        print("PRINT", label, repr(longest))


def main() -> None:
    blob = ROM.read_bytes()
    records = []
    for offset in range(0xAF3, 0xE3B, 6):
        name_ptr, opcode, delta, category_ptr = struct.unpack_from("<HBbH", blob, offset)
        full_name = cstring(blob, name_ptr)
        records.append({
            "opcode": opcode,
            "delta": delta,
            "name_ptr": name_ptr,
            "category_ptr": category_ptr,
            "name": full_name,
            "suffix": full_name.removeprefix("VMOP_"),
            "category": cstring(blob, category_ptr),
        })

    grid = {record["opcode"]: record for record in records}
    orders = {
        "table": records,
        "reverse": records[::-1],
        "column": [grid[y * 16 + x] for x in range(16) for y in range(16) if y * 16 + x in grid],
        "row-zig": [grid[y * 16 + x] for y in range(16) for x in (range(16) if y % 2 == 0 else range(15, -1, -1)) if y * 16 + x in grid],
        "column-zig": [grid[y * 16 + x] for x in range(16) for y in (range(16) if x % 2 == 0 else range(15, -1, -1)) if y * 16 + x in grid],
    }
    category_ids = {name: index for index, name in enumerate(dict.fromkeys(record["category"] for record in records))}

    for order_name, rows in orders.items():
        values = {
            "opcode": [row["opcode"] for row in rows],
            "delta": [row["delta"] & 0xFF for row in rows],
            "name-len": [len(row["name"]) for row in rows],
            "suffix-len": [len(row["suffix"]) for row in rows],
            "category-len": [len(row["category"]) for row in rows],
            "category-id": [category_ids[row["category"]] for row in rows],
            "name-first": [ord(row["suffix"][0]) for row in rows],
            "name-last": [ord(row["suffix"][-1]) for row in rows],
            "name-ptr-low": [row["name_ptr"] & 0xFF for row in rows],
            "name-ptr-high": [row["name_ptr"] >> 8 for row in rows],
            "category-ptr-low": [row["category_ptr"] & 0xFF for row in rows],
            "category-ptr-high": [row["category_ptr"] >> 8 for row in rows],
            "name-sum": [sum(map(ord, row["suffix"])) & 0xFF for row in rows],
        }
        for value_name, sequence in values.items():
            for operation, constant in itertools.product(("xor", "add"), range(256)):
                data = bytes(((value ^ constant) if operation == "xor" else (value + constant) & 0xFF) for value in sequence)
                report(f"{order_name}/{value_name}/{operation}/{constant}", data)
            predicates = {
                **{f"bit-{bit}": [(value >> bit) & 1 for value in sequence] for bit in range(8)},
                "vowel": [int(chr(value & 0x7F).upper() in "AEIOU") for value in sequence],
                "alpha-half": [int(chr(value & 0x7F).upper() >= "N") for value in sequence],
            }
            for predicate_name, bits in predicates.items():
                for reverse, invert, lsb, skip in itertools.product((False, True), (False, True), (False, True), range(8)):
                    selected = bits[::-1] if reverse else bits
                    if invert:
                        selected = [bit ^ 1 for bit in selected]
                    report(f"{order_name}/{value_name}/{predicate_name}/r{reverse}/i{invert}/l{lsb}/s{skip}", packed_bits(selected, lsb, skip))
            for adjust in range(16):
                nibbles = [((value + adjust) & 0xF) for value in sequence]
                for swap in (False, True):
                    data = bytes(((b << 4 | a) if swap else (a << 4 | b)) for a, b in zip(nibbles[::2], nibbles[1::2]))
                    report(f"{order_name}/{value_name}/nibble/{adjust}/swap{swap}", data)


if __name__ == "__main__":
    main()
