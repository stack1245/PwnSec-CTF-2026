#!/usr/bin/env python3
"""Recursively peel marker-delimited Zigerions payload layers."""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


MARKER = b"<<<PAYLOAD_START>>>"
XOR_KEY = bytes((165, 60, 255, 0, 85, 170))


def peel(blob: bytes) -> bytes | None:
    marker_pos = blob.find(MARKER)
    if marker_pos < 0:
        return None
    rest = blob[marker_pos + len(MARKER):]
    if len(rest) < 4:
        return None
    payload_len = struct.unpack_from("<I", rest)[0]
    scrambled = rest[4:4 + payload_len]
    if len(scrambled) != payload_len:
        raise ValueError(f"truncated payload: expected {payload_len}, got {len(scrambled)}")
    xored = bytes(byte ^ XOR_KEY[index % len(XOR_KEY)] for index, byte in enumerate(scrambled))
    return xored[::-1]


def identify(blob: bytes) -> str:
    if blob.startswith(b"\x7fELF"):
        return "ELF"
    if blob.startswith(b"MZ"):
        return "PE"
    if blob.startswith((b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf")):
        return "Mach-O"
    return blob[:16].hex()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    current = args.input.read_bytes()
    layer = 0
    while True:
        digest = hashlib.sha256(current).hexdigest()
        print(f"{layer:02d}: size={len(current)} sha256={digest} type={identify(current)}")
        next_blob = peel(current)
        if next_blob is None:
            (args.output / f"{layer:02d}.bin").write_bytes(current)
            break
        layer += 1
        current = next_blob
        (args.output / f"{layer:02d}.bin").write_bytes(current)


if __name__ == "__main__":
    main()
