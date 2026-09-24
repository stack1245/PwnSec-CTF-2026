import sys
import time

import numpy as np


def find(target: int, batch_size: int = 1 << 20) -> list[int]:
    matches = []
    modulus = np.uint64(2147483647)
    multiplier = np.uint64(16807)
    for start in range(0, 1 << 24, batch_size):
        end = min(start + batch_size, 1 << 24)
        word = np.arange(start, end, dtype=np.uint64)
        word[word == 0] = 1
        state = np.empty((31, end - start), dtype=np.uint32)
        state[0] = word
        for i in range(1, 31):
            word = (multiplier * word) % modulus
            state[i] = word
        for i in range(34, 345):
            np.add(state[i % 31], state[(i - 3) % 31], out=state[i % 31])
        values = (state[344 % 31] >> np.uint32(1)) & np.uint32(0x3FFFFF)
        indices = np.flatnonzero(values == target)
        matches.extend(start + int(index) for index in indices)
    return matches


before = time.perf_counter()
print(find(int(sys.argv[1], 16)))
print(time.perf_counter() - before)
