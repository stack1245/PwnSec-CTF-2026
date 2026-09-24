import ast
import hashlib
import json
import math
from pathlib import Path

from flint import fmpz_mat, fmpz_mod_ctx, fmpz_mod_mat
from mpmath import mp
from sympy import isprime


ROOT = Path(__file__).resolve().parents[1]
lines = (ROOT / "analysis" / "remote-output.txt").read_text(encoding="utf-8").splitlines()
seed = bytes.fromhex(lines[0].split("=", 1)[1].strip())
flag_len = int(lines[1].split("=", 1)[1])
values = ast.literal_eval(lines[2].split("=", 1)[1].strip())
assert len(values) == 48 * 48
cap = [values[i * 48 : (i + 1) * 48] for i in range(48)]


def block(row: int, col: int) -> list[list[int]]:
    return [line[col * 16 : (col + 1) * 16] for line in cap[row * 16 : (row + 1) * 16]]


blocks = [[block(i, j) for j in range(3)] for i in range(3)]
print(f"seed={seed.hex()} flag_len={flag_len} values={len(values)}")
print(f"max_bits={max(values).bit_length()} max={max(values)}")
print("block equality:")
for i in range(3):
    print([blocks[i][j] == blocks[0][j - i] if j >= i else not any(map(any, blocks[i][j])) for j in range(3)])
print(f"nonzero counts={[sum(v != 0 for row in blocks[0][j] for v in row) for j in range(3)]}")


def stream(tag: bytes, out_len: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < out_len:
        out.extend(hashlib.shake_256(seed + tag + counter.to_bytes(2, "little")).digest(64))
        counter += 1
    return bytes(out[:out_len])


def diag(tag: bytes) -> list[int]:
    out = []
    counter = 0
    while len(out) < 16:
        for value in stream(tag + counter.to_bytes(2, "little"), 64):
            candidate = 2 + value % 241
            if candidate not in out and all(abs(candidate - item) != 1 for item in out):
                out.append(candidate)
                if len(out) == 16:
                    break
        counter += 1
    return out


d0 = diag(b"a")
print(f"d0={d0}")


def relation_lattice(i0: int, i1: int, target: int) -> list[list[int]]:
    y = blocks[0][0]
    u = y[i0] + y[i1] + [-y[row][target] for row in range(16)]
    basis = [[int(row == col) for col in range(48)] + [u[row]] for row in range(48)]
    reduced = fmpz_mat(basis).lll()
    return [[int(reduced[row, col]) for col in range(49)] for row in range(48)]


def normalize_segment(segment: list[int], missing: int) -> list[int] | None:
    scale = math.gcd(*(abs(value) for i, value in enumerate(segment) if i != missing))
    if scale == 0:
        return None
    result = [value // scale for value in segment]
    result[missing] = 0
    return result


def valid_column(piece: list[int], target: int) -> bool:
    for row, value in enumerate(piece):
        if row == target:
            continue
        coefficient = 1 + d0[row] - d0[target]
        if value % coefficient or not 0 <= value // coefficient <= 255:
            return False
    return True


def recover_column(target: int) -> list[int]:
    others = [index for index in range(16) if index != target]
    for offset in range(4):
        i0, i1 = others[offset], others[offset + 1]
        for vector in relation_lattice(i0, i1, target):
            for start in (0, 16):
                piece = normalize_segment(vector[start : start + 16], target)
                if piece is None:
                    continue
                for candidate in (piece, [-value for value in piece]):
                    if valid_column(candidate, target):
                        return candidate
    raise RuntimeError(f"failed to recover column {target}")


column_cache = ROOT / "analysis" / "a-offdiag-columns.json"
if column_cache.exists():
    columns = json.loads(column_cache.read_text(encoding="utf-8"))
else:
    columns = []
    for target in range(16):
        column = recover_column(target)
        columns.append(column)
        raw = [None if row == target else column[row] // (1 + d0[row] - d0[target]) for row in range(16)]
        print(f"column {target}: {raw}", flush=True)
    column_cache.write_text(json.dumps(columns), encoding="utf-8")

a_offdiag = [[columns[col][row] for col in range(16)] for row in range(16)]


def matmul(left: list[list[int]], right: list[list[int]], modulus: int) -> list[list[int]]:
    right_t = list(zip(*right))
    return [[sum(a * b for a, b in zip(row, col)) % modulus for col in right_t] for row in left]


def matadd(*matrices: list[list[int]], modulus: int) -> list[list[int]]:
    return [[sum(matrix[i][j] for matrix in matrices) % modulus for j in range(16)] for i in range(16)]


def matscale(matrix: list[list[int]], scalar: int, modulus: int) -> list[list[int]]:
    return [[scalar * value % modulus for value in row] for row in matrix]


def matpow(matrix: list[list[int]], exponent: int, modulus: int) -> list[list[int]]:
    result = [[int(i == j) for j in range(16)] for i in range(16)]
    base = [[value % modulus for value in row] for row in matrix]
    while exponent:
        if exponent & 1:
            result = matmul(result, base, modulus)
        base = matmul(base, base, modulus)
        exponent >>= 1
    return result


y = blocks[0][0]


def commutator_entry(i: int, j: int) -> int:
    return sum(a_offdiag[i][k] * y[k][j] - y[i][k] * a_offdiag[k][j] for k in range(16))


p = None
pair0, pair1, pair2 = (0, 1), (2, 3), (4, 5)
r0, r1 = commutator_entry(*pair0), commutator_entry(*pair1)
r2 = commutator_entry(*pair2)
v0s = [r0 + delta * y[pair0[0]][pair0[1]] for delta in range(-255, 256)]
v1s = [r1 + delta * y[pair1[0]][pair1[1]] for delta in range(-255, 256)]
v2s = [r2 + delta * y[pair2[0]][pair2[1]] for delta in range(-255, 256)]
largest_common = (0, None, None)
for v0 in v0s:
    if not v0:
        continue
    for v1 in v1s:
        common = math.gcd(abs(v0), abs(v1))
        if common > largest_common[0]:
            largest_common = (common, v0s.index(v0) - 255, v1s.index(v1) - 255)
        if common <= max(values):
            continue
        for v2 in v2s:
            triple_common = math.gcd(common, abs(v2))
            for small_factor in range(1, 1 << 16):
                if triple_common % small_factor:
                    continue
                candidate = triple_common // small_factor
                if candidate > max(values) and candidate.bit_length() == 2048 and isprime(candidate):
                    p = candidate
                    break
            if p is not None:
                break
        if p is not None:
            break
    if p is not None:
        break
if p is None:
    print(f"largest pair gcd bits={largest_common[0].bit_length()} deltas={largest_common[1:]}")
    raise RuntimeError("failed to recover modulus")
print(f"p={p}", flush=True)

differences = [0]
for j in range(1, 16):
    delta = (-commutator_entry(0, j) * pow(y[0][j], -1, p)) % p
    if delta > p // 2:
        delta -= p
    if not -255 <= delta <= 255:
        raise RuntimeError(f"invalid diagonal difference at {j}: {delta}")
    differences.append(delta)

possible_q0 = [
    q0
    for q0 in range(256)
    if all(0 <= q0 - differences[index] <= 255 for index in range(16))
]
print(f"diagonal candidates={possible_q0}", flush=True)

identity = [[int(i == j) for j in range(16)] for i in range(16)]
recovered_a = None
for q0 in possible_q0:
    candidate_a = [row[:] for row in a_offdiag]
    for index in range(16):
        candidate_a[index][index] = q0 - differences[index]
    candidate_y = matadd(
        matpow(candidate_a, 4097, p),
        matscale(matpow(candidate_a, 257, p), 3, p),
        matscale(matpow(candidate_a, 17, p), 11, p),
        matscale(candidate_a, 42, p),
        matscale(identity, 99, p),
        modulus=p,
    )
    if candidate_y == y:
        recovered_a = candidate_a
        break
if recovered_a is None:
    raise RuntimeError("failed to recover diagonal")
print(f"diagonal={[recovered_a[i][i] for i in range(16)]}", flush=True)


def babai_closest(basis: list[list[int]], target: list[int]) -> list[int]:
    reduced_matrix = fmpz_mat(basis).lll(delta=0.99)
    reduced = [
        [int(reduced_matrix[row, col]) for col in range(len(target))]
        for row in range(len(target))
    ]
    mp.dps = 800
    orthogonal: list[list] = []
    norms = []
    for row in reduced:
        current = [mp.mpf(value) for value in row]
        for previous, norm in zip(orthogonal, norms):
            coefficient = sum(mp.mpf(a) * b for a, b in zip(row, previous)) / norm
            current = [value - coefficient * base for value, base in zip(current, previous)]
        orthogonal.append(current)
        norms.append(sum(value * value for value in current))
    residual = [mp.mpf(value) for value in target]
    lattice_vector = [0] * len(target)
    for row, ortho, norm in reversed(list(zip(reduced, orthogonal, norms))):
        coefficient = int(mp.nint(sum(value * base for value, base in zip(residual, ortho)) / norm))
        if coefficient:
            residual = [value - coefficient * base for value, base in zip(residual, row)]
            lattice_vector = [value + coefficient * base for value, base in zip(lattice_vector, row)]
    return lattice_vector


def generic_matmul(left: list[list[int]], right: list[list[int]], modulus: int) -> list[list[int]]:
    right_t = list(zip(*right))
    return [[sum(a * b for a, b in zip(row, col)) % modulus for col in right_t] for row in left]


def generic_matpow(matrix: list[list[int]], exponent: int, modulus: int) -> list[list[int]]:
    size = len(matrix)
    result = [[int(i == j) for j in range(size)] for i in range(size)]
    base = [[value % modulus for value in row] for row in matrix]
    while exponent:
        if exponent & 1:
            result = generic_matmul(result, base, modulus)
        base = generic_matmul(base, base, modulus)
        exponent >>= 1
    return result


def generic_polynomial(matrix: list[list[int]], modulus: int) -> list[list[int]]:
    size = len(matrix)
    powers = [(4097, 1), (257, 3), (17, 11), (1, 42)]
    result = [[99 * int(i == j) % modulus for j in range(size)] for i in range(size)]
    for exponent, coefficient in powers:
        term = generic_matpow(matrix, exponent, modulus)
        for i in range(size):
            for j in range(size):
                result[i][j] = (result[i][j] + coefficient * term[i][j]) % modulus
    return result


def recover_superblock(
    diagonal_block: list[list[int]],
    public_superblock: list[list[int]],
    mix_diagonal: list[int],
    first_superblock: list[list[int]] | None = None,
    public_first_superblock: list[list[int]] | None = None,
) -> list[list[int]]:
    off_positions = [(i, j) for i in range(16) for j in range(16) if i != j]
    off_index = {position: index for index, position in enumerate(off_positions)}
    coefficient_rows = []
    rhs_rows = []
    az = matmul(diagonal_block, public_superblock, p)
    za = matmul(public_superblock, diagonal_block, p)
    if first_superblock is not None:
        if public_first_superblock is None:
            raise RuntimeError("missing public first superblock")
        bz = matmul(first_superblock, public_first_superblock, p)
        zb = matmul(public_first_superblock, first_superblock, p)
        az = matadd(az, bz, modulus=p)
        za = matadd(za, zb, modulus=p)
    for i in range(16):
        for j in range(16):
            coefficients = [0] * len(off_positions)
            for u in range(16):
                if u != j:
                    coefficients[off_index[(u, j)]] += y[i][u]
            for v in range(16):
                if i != v:
                    coefficients[off_index[(i, v)]] -= y[v][j]
            coefficient_rows.append([value % p for value in coefficients])
            rhs = [(az[i][j] - za[i][j]) % p] + [0] * 16
            rhs[1 + i] = (rhs[1 + i] + y[i][j]) % p
            rhs[1 + j] = (rhs[1 + j] - y[i][j]) % p
            rhs_rows.append(rhs)

    context = fmpz_mod_ctx(p)
    coefficient_matrix = fmpz_mod_mat(coefficient_rows, context)
    reduced_transpose, rank = coefficient_matrix.transpose().rref()
    if rank != len(off_positions):
        raise RuntimeError(f"unexpected Sylvester rank: {rank}")
    independent_rows = []
    for row in range(rank):
        independent_rows.append(next(col for col in range(256) if int(reduced_transpose[row, col]) != 0))
    square = fmpz_mod_mat([coefficient_rows[index] for index in independent_rows], context)
    rhs_matrix = fmpz_mod_mat([rhs_rows[index] for index in independent_rows], context)
    affine = square.solve(rhs_matrix)

    samples_a = []
    samples_b = []
    sample_positions = []
    for row, (i, j) in enumerate(off_positions):
        mix_coefficient = 1 + mix_diagonal[i] - mix_diagonal[j]
        inverse_mix = pow(mix_coefficient, -1, p)
        constant = int(affine[row, 0])
        coeffs = [int(affine[row, 1 + index]) for index in range(16)]
        samples_a.append([(-value * inverse_mix) % p for value in coeffs])
        samples_b.append((constant * inverse_mix) % p)
        sample_positions.append((i, j))

    sample_count = 24
    lattice_basis = []
    for index in range(sample_count):
        lattice_basis.append(
            [p if index == other else 0 for other in range(sample_count)] + [0] * 16
        )
    for secret_index in range(16):
        lattice_basis.append(
            [samples_a[sample][secret_index] for sample in range(sample_count)]
            + [int(secret_index == other) for other in range(16)]
        )
    closest = babai_closest(lattice_basis, samples_b[:sample_count] + [0] * 16)
    diagonal = closest[-16:]

    recovered = [[0] * 16 for _ in range(16)]
    for index in range(16):
        recovered[index][index] = diagonal[index]
    for row, (i, j) in enumerate(off_positions):
        recovered[i][j] = (int(affine[row, 0]) + sum(int(affine[row, 1 + k]) * diagonal[k] for k in range(16))) % p
        centered = recovered[i][j] if recovered[i][j] <= p // 2 else recovered[i][j] - p
        mix_coefficient = 1 + mix_diagonal[i] - mix_diagonal[j]
        if centered % mix_coefficient or not 0 <= centered // mix_coefficient <= 255:
            raise RuntimeError(f"invalid recovered entry {(i, j)}")
        recovered[i][j] = centered

    possible_shifts = [
        shift for shift in range(-min(diagonal), 256 - max(diagonal))
        if all(0 <= value + shift <= 255 for value in diagonal)
    ]
    if first_superblock is None:
        stacked = [
            diagonal_block[i] + recovered[i] if i < 16 else [0] * 16 + diagonal_block[i - 16]
            for i in range(32)
        ]
        block_offset = 16
    else:
        stacked = []
        for block_row in range(3):
            for i in range(16):
                row = []
                for block_col in range(3):
                    if block_col < block_row:
                        row.extend([0] * 16)
                    elif block_col == block_row:
                        row.extend(diagonal_block[i])
                    elif block_col == block_row + 1:
                        row.extend(first_superblock[i])
                    else:
                        row.extend(recovered[i])
                stacked.append(row)
        block_offset = 32
    polynomial = generic_polynomial(stacked, p)
    base_public = [row[block_offset : block_offset + 16] for row in polynomial[:16]]
    derivative = matadd(
        matscale(matpow(diagonal_block, 4096, p), 4097, p),
        matscale(matpow(diagonal_block, 256, p), 3 * 257, p),
        matscale(matpow(diagonal_block, 16, p), 11 * 17, p),
        matscale(identity, 42, p),
        modulus=p,
    )
    pivot = next((i, j) for i in range(16) for j in range(16) if derivative[i][j])
    shift = (
        (public_superblock[pivot[0]][pivot[1]] - base_public[pivot[0]][pivot[1]])
        * pow(derivative[pivot[0]][pivot[1]], -1, p)
    ) % p
    if shift > p // 2:
        shift -= p
    if shift not in possible_shifts:
        raise RuntimeError(f"invalid scalar shift: {shift}, expected one of {possible_shifts}")
    if any(
        (base_public[i][j] + shift * derivative[i][j]) % p != public_superblock[i][j]
        for i in range(16)
        for j in range(16)
    ):
        raise RuntimeError("recovered superblock does not reproduce the public polynomial")
    for index in range(16):
        recovered[index][index] += shift
    return recovered


d1 = diag(b"b")
recovered_b = recover_superblock(recovered_a, blocks[0][1], d1)
print(f"b diagonal={[recovered_b[i][i] for i in range(16)]}", flush=True)

d2 = diag(b"c")
recovered_c = recover_superblock(
    recovered_a,
    blocks[0][2],
    d2,
    first_superblock=recovered_b,
    public_first_superblock=blocks[0][1],
)
print(f"c diagonal={[recovered_c[i][i] for i in range(16)]}", flush=True)

m2 = bytes(
    recovered_c[i][j] // (1 + d2[i] - d2[j])
    for i in range(16)
    for j in range(16)
)
sealed_position = int.from_bytes(stream(b"2", 2), "little") % (256 - flag_len + 1)
sealed = m2[sealed_position : sealed_position + flag_len]
key_bytes = p.to_bytes((p.bit_length() + 7) // 8, "big")
mask_bytes = bytearray()
counter = 0
while len(mask_bytes) < flag_len:
    mask_bytes.extend(
        hashlib.sha512(
            b"iLOVEtea"
            + len(key_bytes).to_bytes(2, "big")
            + key_bytes
            + seed
            + counter.to_bytes(4, "little")
        ).digest()
    )
    counter += 1
flag = bytes(left ^ right for left, right in zip(sealed, mask_bytes))
print(f"sealed_position={sealed_position} flag={flag!r}", flush=True)
