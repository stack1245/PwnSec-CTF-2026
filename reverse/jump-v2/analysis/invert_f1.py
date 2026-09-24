#!/usr/bin/env python3
from pathlib import Path

BLOB = Path(__file__).with_name("embedded.elf").read_bytes()


def gf_mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        a = ((a << 1) ^ (0x11b if a & 0x80 else 0)) & 0xff
        b >>= 1
    return out


def rotl8(x, n):
    return ((x << n) | (x >> (8-n))) & 0xff


SBOX = []
for x in range(256):
    inv = 0 if x == 0 else pow(x, 254, 0x11b)  # replaced below: polynomial exponent
    if x:
        inv = 1
        for _ in range(254):
            inv = gf_mul(inv, x)
    SBOX.append(inv ^ rotl8(inv,1) ^ rotl8(inv,2) ^ rotl8(inv,3) ^ rotl8(inv,4) ^ 0x63)
INV_SBOX = [0] * 256
for i, x in enumerate(SBOX):
    INV_SBOX[x] = i


def shift_rows(s):
    return bytes(s[4*((c+r)%4)+r] for c in range(4) for r in range(4))


def inv_shift_rows(s):
    return bytes(s[4*((c-r)%4)+r] for c in range(4) for r in range(4))


def mix_columns(s):
    out = bytearray(16)
    for c in range(4):
        a = s[4*c:4*c+4]
        out[4*c:4*c+4] = bytes((
            gf_mul(a[0],2)^gf_mul(a[1],3)^a[2]^a[3],
            a[0]^gf_mul(a[1],2)^gf_mul(a[2],3)^a[3],
            a[0]^a[1]^gf_mul(a[2],2)^gf_mul(a[3],3),
            gf_mul(a[0],3)^a[1]^a[2]^gf_mul(a[3],2)))
    return bytes(out)


def inv_mix_columns(s):
    out = bytearray(16)
    for c in range(4):
        a = s[4*c:4*c+4]
        out[4*c:4*c+4] = bytes((
            gf_mul(a[0],14)^gf_mul(a[1],11)^gf_mul(a[2],13)^gf_mul(a[3],9),
            gf_mul(a[0],9)^gf_mul(a[1],14)^gf_mul(a[2],11)^gf_mul(a[3],13),
            gf_mul(a[0],13)^gf_mul(a[1],9)^gf_mul(a[2],14)^gf_mul(a[3],11),
            gf_mul(a[0],11)^gf_mul(a[1],13)^gf_mul(a[2],9)^gf_mul(a[3],14)))
    return bytes(out)


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def aesenc(s, key):
    return xor(mix_columns(shift_rows(bytes(SBOX[x] for x in s))), key)


def inv_aesenc(s, key):
    return bytes(INV_SBOX[x] for x in inv_shift_rows(inv_mix_columns(xor(s, key))))


def pshufb(s, mask):
    return bytes(0 if x & 0x80 else s[x & 15] for x in mask)


def inv_pshufb(s, mask):
    out = bytearray(16)
    for i, x in enumerate(mask):
        assert not x & 0x80
        out[x & 15] = s[i]
    return bytes(out)


def data(address):
    off = address - 0x400000
    return BLOB[off:off+16]


def forward(inp):
    x0, x1, x2 = inp[:16], inp[16:32], inp[32:48]
    for r in range(12):
        v = pshufb(x0, data(0x545220+16*r))
        v = xor(v, data(0x545160+16*r))
        v = aesenc(v, data(0x5450a0+16*r))
        v = xor(xor(v, x1), pshufb(x2, data(0x5452e0+16*r)))
        x0, x1, x2 = x1, x2, v
    return x0+x1+x2


def inverse(out):
    x0, x1, x2 = out[:16], out[16:32], out[32:48]
    for r in reversed(range(12)):
        v = xor(xor(x2, x0), pshufb(x1, data(0x5452e0+16*r)))
        v = inv_aesenc(v, data(0x5450a0+16*r))
        old0 = inv_pshufb(xor(v, data(0x545160+16*r)), data(0x545220+16*r))
        x0, x1, x2 = old0, x0, x1
    return x0+x1+x2


def main():
    known = bytes.fromhex("276d206321e61ff57e44218aea1ed48e53d97f2d88bfb8fe0aca01f5fd7689661d5a1e4bcb1807fbf7b96d3c247c4a25")
    assert forward(b"A"*48) == known
    assert inverse(known) == b"A"*48
    target = bytes.fromhex("5f0ec07d5d8d2527f35818fe071ae9708e6634c32c6331becd5454803cda19f13b553da3d58148280fe55a1b6ea35a2f")
    answer = inverse(target)
    print(answer)
    print(answer.decode())


if __name__ == "__main__":
    main()
