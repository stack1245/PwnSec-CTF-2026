#!/usr/bin/env python3
"""Extract the PyInstaller CArchive embedded in the challenge ELF."""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path, PurePosixPath


MAGIC = b"MEI\x0c\x0b\x0a\x0b\x0e"
COOKIE = struct.Struct("!8sIIII64s")
ENTRY = struct.Struct("!iIIIBc")
PYC310_HEADER = bytes.fromhex("6f0d0d0a") + bytes(12)


def safe_path(root: Path, raw_name: str) -> Path:
    parts = [part for part in PurePosixPath(raw_name.replace("\\", "/")).parts
             if part not in ("", ".", "..", "/")]
    return root.joinpath(*parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    blob = args.binary.read_bytes()
    cookie_pos = blob.rfind(MAGIC)
    if cookie_pos < 0:
        raise SystemExit("PyInstaller cookie not found")

    magic, package_len, toc_offset, toc_len, py_version, py_lib = COOKIE.unpack_from(blob, cookie_pos)
    package_start = cookie_pos + COOKIE.size - package_len
    toc_pos = package_start + toc_offset
    toc_end = toc_pos + toc_len
    args.output.mkdir(parents=True, exist_ok=True)
    print(f"cookie={cookie_pos:#x} package_start={package_start:#x} python={py_version} library={py_lib.rstrip(bytes([0])).decode()}")

    while toc_pos < toc_end:
        entry_size, offset, compressed_size, uncompressed_size, compressed, typecode = ENTRY.unpack_from(blob, toc_pos)
        name_start = toc_pos + ENTRY.size
        name_end = toc_pos + entry_size
        name = blob[name_start:name_end].rstrip(bytes([0])).decode("utf-8", "replace")
        data = blob[package_start + offset:package_start + offset + compressed_size]
        if compressed:
            data = zlib.decompress(data)
        if len(data) != uncompressed_size:
            raise ValueError(f"size mismatch for {name!r}: {len(data)} != {uncompressed_size}")
        destination = safe_path(args.output, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        if typecode in (b"m", b"s"):
            destination.with_name(destination.name + ".pyc").write_bytes(PYC310_HEADER + data)
        print(f"{typecode.decode(errors='replace')} {compressed_size:9d} -> {uncompressed_size:9d} {name}")
        toc_pos += entry_size


if __name__ == "__main__":
    main()
