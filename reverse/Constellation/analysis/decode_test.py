import pathlib
import struct
import sys


ROOT = pathlib.Path(__file__).parents[1]
source = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "challenge" / "flag.flag"
destination = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "output" / "decoded-stream.bin"
blob = source.read_bytes()
field = (ROOT / "analysis" / "plan_field.bin").read_bytes()
order_blob = (ROOT / "analysis" / "plan_order.bin").read_bytes()
order = struct.unpack(f"<{len(order_blob) // 4}I", order_blob)

magic, output_size, mode, blocks, width, data_count, parity_count, seed, block_count_2 = struct.unpack_from(
    "<9I", blob
)
assert magic == 0xE70B1591
assert blocks == block_count_2
assert (width, data_count, parity_count, seed) == (192, 224, 32, 0xC1028A4D)

log = [0] * 256
for exponent, value in enumerate(field):
    log[value] = exponent


def gf_mul(a, b):
    if not a or not b:
        return 0
    return field[(log[a] + log[b]) % 255]


def gf_pow(value, exponent):
    if exponent == 0:
        return 1
    if value == 0:
        return 0
    return field[(log[value] * exponent) % 255]


def invert(a):
    n = len(a)
    aug = [row[:] + [int(i == j) for j in range(n)] for i, row in enumerate(a)]
    for col in range(n):
        pivot = next(row for row in range(col, n) if aug[row][col])
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = field[(255 - log[aug[col][col]]) % 255]
        aug[col] = [gf_mul(value, scale) for value in aug[col]]
        for row in range(n):
            if row != col and aug[row][col]:
                factor = aug[row][col]
                aug[row] = [x ^ gf_mul(factor, y) for x, y in zip(aug[row], aug[col])]
    return [row[n:] for row in aug]


metadata = blob[36 : 36 + blocks * 33]
payload = blob[36 + blocks * 33 :]
matrix = bytes(gf_pow(parity + 1, data) for parity in range(parity_count) for data in range(data_count))
result = bytearray()

for block_index in range(blocks):
    meta = metadata[block_index * 33 : (block_index + 1) * 33]
    erased = set(meta[1 : 1 + meta[0]])
    assert len(erased) == meta[0]
    raw_block = payload[block_index * 256 * width : (block_index + 1) * 256 * width]
    physical_shards = [bytearray(raw_block[i * width : (i + 1) * width]) for i in range(256)]
    permutation = sorted(
        range(256), key=lambda shard: (order[block_index * 256 + shard], shard)
    )
    shards = [None] * 256
    for physical_index, logical_index in enumerate(permutation):
        shards[logical_index] = physical_shards[physical_index]

    physical_erasure = all(not any(physical_shards[index]) for index in erased)
    logical_erasure = all(not any(shards[index]) for index in erased)
    assert physical_erasure or logical_erasure, (physical_erasure, logical_erasure)
    if physical_erasure and logical_erasure:
        assert not erased or not any(raw_block)
    if physical_erasure:
        erased = {permutation[index] for index in erased}

    missing_data = sorted(index for index in erased if index < data_count)
    surviving_parity = [p for p in range(parity_count) if data_count + p not in erased]
    if missing_data:
        assert len(missing_data) == len(surviving_parity)
        coefficients = [[matrix[p * data_count + d] for d in missing_data] for p in surviving_parity]
        inverse = invert(coefficients)
    else:
        inverse = []

    residuals = []
    for p in surviving_parity:
        rhs = bytearray(shards[data_count + p])
        for d in range(data_count):
            if d in erased:
                continue
            coefficient = matrix[p * data_count + d]
            if coefficient:
                rhs = bytearray(x ^ gf_mul(coefficient, y) for x, y in zip(rhs, shards[d]))
        residuals.append(rhs)

    for row, d in enumerate(missing_data):
        recovered = bytearray(width)
        for p, coefficient in enumerate(inverse[row]):
            if coefficient:
                recovered = bytearray(
                    x ^ gf_mul(coefficient, y) for x, y in zip(recovered, residuals[p])
                )
        shards[d] = recovered

    result.extend(b"".join(shards[:data_count]))
    print(block_index, "missing_data", missing_data, "parity_rows", surviving_parity)

result = result[:output_size]
destination.write_bytes(result)
print("decoded", len(result), "head", result[:64].hex(), "tail", result[-64:].hex())
