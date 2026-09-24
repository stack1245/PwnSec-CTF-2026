#!/usr/bin/env python3
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])

import z3
import model_f2 as f2
import invert_f1 as f1

BV8 = z3.BitVecSort(8)
SBOX = z3.K(BV8, z3.BitVecVal(0, 8))
for i, v in enumerate(f1.SBOX):
    SBOX = z3.Store(SBOX, z3.BitVecVal(i, 8), z3.BitVecVal(v, 8))


def sb(x):
    return z3.Select(SBOX, x)


def xtime(x):
    return (x << 1) ^ z3.If(z3.Extract(7, 7, x) == 1, z3.BitVecVal(0x1b, 8), z3.BitVecVal(0, 8))


def mul3(x):
    return xtime(x) ^ x


def shift_rows(s):
    return [s[4*((c+r)%4)+r] for c in range(4) for r in range(4)]


def mix_columns(s):
    out = []
    for c in range(4):
        a = s[4*c:4*c+4]
        out.extend((xtime(a[0])^mul3(a[1])^a[2]^a[3],
                    a[0]^xtime(a[1])^mul3(a[2])^a[3],
                    a[0]^a[1]^xtime(a[2])^mul3(a[3]),
                    mul3(a[0])^a[1]^a[2]^xtime(a[3])))
    return out


def xor(a, b):
    return [x ^ z3.BitVecVal(y, 8) if isinstance(y, int) else x ^ y for x, y in zip(a, b)]


def pshufb(s, mask):
    return [z3.BitVecVal(0,8) if x & 0x80 else s[x&15] for x in mask]


def f1_forward(inp):
    x0, x1, x2 = inp[:16], inp[16:32], inp[32:]
    for r in range(12):
        v = pshufb(x0, f1.data(0x545220+16*r))
        v = xor(v, f1.data(0x545160+16*r))
        v = xor(mix_columns(shift_rows([sb(x) for x in v])), f1.data(0x5450a0+16*r))
        v = [a ^ b ^ c for a,b,c in zip(v, x1, pshufb(x2, f1.data(0x5452e0+16*r)))]
        x0, x1, x2 = x1, x2, v
    return x0+x1+x2


def main():
    chars = [z3.BitVec(f"ch{i}", 8) for i in range(48)]
    stage = f1_forward(chars)
    s = z3.Solver()
    s.add(*[z3.And(x >= 0x20, x <= 0x7e) for x in chars])
    target_hex = "c56057e34954df62f399fbc8d38adf0a37ab7494f5633ef682303a6b635f464e8c5e5c355a241869485f481d1f8ef1d0"
    target_words = __import__('struct').unpack('<12I', bytes.fromhex(target_hex))
    for block in range(3):
        words = [z3.Concat(*stage[block*16+i*4:block*16+i*4+4]) for i in range(4)]
        final = f2.f2_block(words)
        desired_out = target_words[block*4:block*4+4]
        desired_final = [f2.bswap(f2.rol(x, k)) for x,k in zip(desired_out,(7,16,5,19))]
        s.add(*[x == y for x,y in zip(final, desired_final)])
    print(s.check())
    m = s.model()
    answer = bytes(m.eval(x).as_long() for x in chars)
    print(answer)
    print(answer.decode())


if __name__ == '__main__':
    main()
