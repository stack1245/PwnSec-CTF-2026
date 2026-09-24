#!/bin/sh
set -eu

src=./misc/ycc/analysis/extracted
out=./misc/ycc/analysis/local_build
mkdir -p "$out"
cc -O2 -std=gnu99 -Wl,--build-id=none -I"$src" \
  -o "$out/ycc" "$src/ycc.c" "$src/runtime.c" -lm
YCC_RUNTIME_DIR="$src" "$out/ycc" --compile "$src/ysh.y" -o "$out/ysh"
file "$out/ycc" "$out/ysh"
