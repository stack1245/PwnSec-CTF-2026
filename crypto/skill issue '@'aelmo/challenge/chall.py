from os import getenv, urandom
from hashlib import shake_256, sha512
from Crypto.Util.number import getPrime
from sage.all import *
n = 16
flag = getenv("FLAG","pwnsec{????????????????????????????????????????????????}").encode()
p = getPrime(2048)
seed = urandom(16)

def stream(tag, out_len):
    out = b""
    ctr = 0
    while len(out) < out_len:
        out += shake_256(seed + tag + ctr.to_bytes(2, "little")).digest(64)
        ctr += 1
    return out[:out_len]

def mask(k, out_len):
    kb = int(k).to_bytes((int(k).bit_length() + 7) // 8, "big")
    out = b""
    ctr = 0

    while len(out) < out_len:
        out += sha512(b"iLOVEtea" +len(kb).to_bytes(2, "big") +kb +seed +ctr.to_bytes(4, "little")).digest()
        ctr += 1
    return out[:out_len]
def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def diag(tag):
    out = []
    ctr = 0

    while len(out) < n:
        for x in stream(tag + ctr.to_bytes(2, "little"), 64):
            v = 2 + x % 241
            if v not in out and all(abs(v - y) != 1 for y in out):
                out.append(v)
                if len(out) == n:
                    break
        ctr += 1
    return out

def slab(tag, msg=b""):
    raw = bytearray(urandom(n * n))
    if msg:
        pos = int.from_bytes(stream(tag, 2), "little")
        pos %= n * n - len(msg) + 1
        raw[pos:pos + len(msg)] = msg
    return matrix(ZZ, n, n, list(raw))

def mix(m, d):
    return matrix(ZZ, n, n, [(1 + d[i] - d[j]) * ZZ(m[i, j]) for i in range(n) for j in range(n)])

def stack(x, y, z):
    o = zero_matrix(ZZ, n)
    return block_matrix(ZZ,[[x, y, z],[o, x, y],[o, o, x]],subdivide=False)

assert len(flag) <= n * n
sealed = xor(flag, mask(p, len(flag)))

d0 = diag(b"a")
d1 = diag(b"b")
d2 = diag(b"c")

m0 = slab(b"0")
m1 = slab(b"1")
m2 = slab(b"2", sealed)

x0 = mix(m0, d0)
x1 = mix(m1, d1)
x2 = mix(m2, d2)

r = Zmod(p)
x = stack(x0, x1, x2).change_ring(r)

cap = x**4097 +3*x**257 +11*x**17 +42*x +99*identity_matrix(r, 3*n)


print(f"seed = {seed.hex()!r}")
print(f"flag_len = {len(flag)}")
print(f"cap = {[ZZ(v) for v in cap.list()]}")
