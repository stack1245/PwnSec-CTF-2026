import ast
from math import gcd
from pathlib import Path

from flint import fmpz_mat, fmpz_poly
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

print("reducing", len(rows), "x", len(rows[0]), flush=True)
reduced = fmpz_mat(rows).lll(delta=0.99, eta=0.51, rep="zbasis")
etas = [
    [int(reduced[i, t + j]) // scale for j in range(r)]
    for i in range(min(40, reduced.nrows()))
    if all(int(reduced[i, t + j]) % scale == 0 for j in range(r))
]
polys = [fmpz_poly(eta) for eta in etas]
for anchor in range(min(8, len(polys))):
    values = []
    for other in range(anchor + 1, min(20, len(polys))):
        resultant = int(polys[anchor].resultant(polys[other]))
        if not resultant:
            continue
        values.append(abs(resultant))
        for previous in values[:-1]:
            common = gcd(previous, values[-1])
            root_candidate, exact = integer_nthroot(common, 25)
            if exact and (1 << 48) < (1 << 128) - root_candidate < (1 << 50):
                print("MODULUS", root_candidate, "DELTA", (1 << 128) - root_candidate, flush=True)
                raise SystemExit
print("FAILED", flush=True)
