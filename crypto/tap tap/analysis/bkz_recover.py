import ast
import re
import subprocess
from math import gcd
from pathlib import Path

from flint import fmpz_mod_poly_ctx, fmpz_poly
from sympy import integer_nthroot


root = Path(__file__).resolve().parents[1]
tree = ast.parse((root / "challenge" / "chall.py").read_text(encoding="utf-8"))
blob = next(
    node.value.value
    for node in reversed(tree.body)
    if isinstance(node, ast.Expr)
    and isinstance(node.value, ast.Constant)
    and isinstance(node.value.value, str)
)
ys = ast.literal_eval(blob.strip().splitlines()[0])

r = t = 90
q = 1 << 80
scale = 64
rows = []
for j in range(t):
    row = [0] * (t + r)
    row[j] = q
    rows.append(row)
for i in range(r):
    rows.append(ys[i : i + t] + [scale * int(i == j) for j in range(r)])

base = "/mnt/d/.dev/.competitions/.ctf/PwnSec CTF 2026/crypto/tap tap/analysis/fplll-local"
command = (
    f"base='{base}'; LD_LIBRARY_PATH=\"$base/usr/lib/x86_64-linux-gnu\" "
    '"$base/usr/bin/fplll" -a bkz -b 35 -f mpfr -p 256 -bkzmaxloops 20 -bkzautoabort'
)
print(f"BKZ-35 on {len(rows)} x {len(rows[0])}", flush=True)
cache = root / "analysis" / "reduced.txt"
if cache.exists():
    reduced_text = cache.read_text(encoding="utf-8")
else:
    result = subprocess.run(
        ["wsl", "-e", "bash", "-lc", command],
        input="[" + "\n".join("[" + " ".join(map(str, row)) + "]" for row in rows) + "]",
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode and not result.stdout.strip():
        raise RuntimeError(result.stderr)
    reduced_text = result.stdout
    cache.write_text(reduced_text, encoding="utf-8")
reduced = [
    [int(value) for value in match.group(1).split()]
    for match in re.finditer(r"\[([\d\s-]+)\]", reduced_text)
]

etas = []
for i, row in enumerate(reduced[:20]):
    if any(value % scale for value in row[t:]):
        continue
    eta = [value // scale for value in row[t:]]
    content = 0
    for value in eta:
        content = gcd(content, abs(value))
    eta = [value // content for value in eta]
    etas.append(eta)
    print("candidate", i, "degree", max(j for j, value in enumerate(eta) if value), flush=True)

polys = [fmpz_poly(eta) for eta in etas]
modulus = None
for anchor in range(8):
    anchor_results = []
    for other in range(anchor + 1, len(polys)):
        value = int(polys[anchor].resultant(polys[other]))
        if not value:
            continue
        anchor_results.append(abs(value))
        for first in range(len(anchor_results) - 1):
            current = gcd(anchor_results[first], anchor_results[-1])
            root_candidate, exact = integer_nthroot(current, 25)
            if exact and (1 << 48) < (1 << 128) - root_candidate < (1 << 50):
                print("MODULUS", root_candidate, "DELTA", (1 << 128) - root_candidate, flush=True)
                modulus = root_candidate
                break
        if modulus is not None:
            break
    if modulus is not None:
        break
    print("anchor", anchor, "done", flush=True)

if modulus is None:
    raise RuntimeError("modulus recovery failed")
ctx = fmpz_mod_poly_ctx(modulus)
characteristic = ctx(etas[0])
for eta in etas[1:]:
    characteristic = characteristic.gcd(ctx(eta))
print("CHARACTERISTIC_DEGREE", characteristic.degree(), flush=True)
print("CHARACTERISTIC", list(characteristic), flush=True)
print("TAPS", [(-int(characteristic[i])) % modulus for i in range(25)], flush=True)
