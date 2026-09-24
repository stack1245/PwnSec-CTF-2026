#!/usr/bin/env bash
set -euo pipefail

binary="$(dirname "$0")/../challenge/src/freal"

for _ in $(seq 1 10); do
    coproc target { exec "$binary" >/dev/null; }
    pid=$target_PID
    printf '1\n8388608\n4\n0\n1\n8388608\n' >&"${target[1]}"
    sleep 0.1
    awk '/freal/ && $2 ~ /r--p/ { if (!base) base=$1 } /\[heap\]/ { print base, $1 }' "/proc/$pid/maps"
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
done
