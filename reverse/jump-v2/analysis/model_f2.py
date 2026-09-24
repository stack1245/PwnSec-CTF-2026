#!/usr/bin/env python3
import struct
from pathlib import Path

import z3
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

MASK = 0xffffffff
BLOB = Path(__file__).with_name("embedded.elf").read_bytes()
MD = Cs(CS_ARCH_X86, CS_MODE_64)
MD.detail = True


def helper(start, body, end, args):
    regs = {"edi": args[0], "esi": args[1], "edx": args[2], "ecx": args[3]}
    def rn(reg):
        name = MD.reg_name(reg)
        return {"rax":"eax", "rdx":"edx", "rcx":"ecx", "rsi":"esi", "rdi":"edi"}.get(name, name)
    if start == 0x54450D:
        locals_ = {-0x14: args[0], -0x18: args[1], -0x1c: args[2], -0x20: args[3]}
    else:
        locals_ = {-4: args[0], -8: args[1], -0xc: args[2], -0x10: args[3]}

    def val(op):
        if op.type == X86_OP_REG:
            return regs[rn(op.reg)]
        if op.type == X86_OP_IMM:
            return op.imm & MASK
        if op.type == X86_OP_MEM:
            assert MD.reg_name(op.mem.base) == "rbp" and not op.mem.index
            return locals_[op.mem.disp]
        raise AssertionError(op.type)

    def put(op, value):
        if isinstance(value, int):
            value &= MASK
        if op.type == X86_OP_REG:
            regs[rn(op.reg)] = value
        elif op.type == X86_OP_MEM:
            assert MD.reg_name(op.mem.base) == "rbp" and not op.mem.index
            locals_[op.mem.disp] = value
        else:
            raise AssertionError(op.type)

    for ins in MD.disasm(BLOB[body - 0x400000:end - 0x400000], body):
        ops = ins.operands
        if ins.mnemonic == "mov":
            put(ops[0], val(ops[1]))
        elif ins.mnemonic == "not":
            put(ops[0], ~val(ops[0]))
        elif ins.mnemonic in {"add", "xor", "or", "and"}:
            a, b = val(ops[0]), val(ops[1])
            put(ops[0], {"add": lambda: a+b, "xor": lambda: a^b,
                         "or": lambda: a|b, "and": lambda: a&b}[ins.mnemonic]())
        elif ins.mnemonic == "imul":
            assert len(ops) == 3
            put(ops[0], val(ops[1]) * val(ops[2]))
        elif ins.mnemonic == "shl":
            put(ops[0], val(ops[0]) << val(ops[1]))
        elif ins.mnemonic == "lea":
            m = ops[1].mem
            total = m.disp
            if m.base:
                total += regs[rn(m.base)]
            if m.index:
                total += regs[rn(m.index)] * m.scale
            put(ops[0], total)
        else:
            raise AssertionError((hex(ins.address), ins.mnemonic, ins.op_str))
    return regs["eax"]


SPECS = [(0x544218, 0x54422C, 0x5443F8), (0x5443FA, 0x54440E, 0x54450B),
         (0x54450D, 0x544521, 0x5446C8)]
KEYS = [
    (0x5cdf0d71, 0x6b4d0809, 0x1497712c),
    (0x00761721, 0x03b3d70d, 0x00f904c9),
    (0x043b1893, 0xc1072960, 0x0330c256),
    (0x271c2df5, 0x94241560, 0x1e32763e),
    (0x11297387, 0x10b3134c, 0x053ef702),
    (0x505163d3, 0x6bacaa28, 0x8700f895),
    (0x0bf05553, 0x09e28673, 0xc361fb10),
    (0x1066928c, 0x98e47ca7, 0x576970a7),
]


def h(which, *args):
    return helper(*SPECS[which], args)


def f2_block(words):
    a, b, c, d = words
    for r, (k0, k1, k2) in enumerate(KEYS):
        na = a ^ h(0, b, k0, r, 0x6f74ac93)
        nd = b ^ h(1, c, k1, 0x1357 + r, 0x6f74ac93)
        nb = c ^ h(2, d, k2, 0x2468 + r, 0x6f74ac93)
        a, b, c, d = na, nb, a, nd
        if isinstance(a, int):
            a, b, c, d = (x & MASK for x in (a, b, c, d))
    return [a, b, c, d]


def rol(x, n):
    return ((x << n) | (x >> (32-n))) & MASK


def bswap(x):
    return int.from_bytes(x.to_bytes(4, "little"), "big")


def main():
    known_in = struct.unpack(">4I", bytes.fromhex("276d206321e61ff57e44218aea1ed48e"))
    known_out = [bswap(rol(x, k)) for x, k in zip(
        struct.unpack("<4I", bytes.fromhex("44eec618b9123fbf88094d771055c978")), (7,16,5,19))]
    got = [x & MASK for x in f2_block(known_in)]
    print("selftest", [hex(x) for x in got], [hex(x) for x in known_out])
    assert got == known_out

    target_hex = "c56057e34954df62f399fbc8d38adf0a37ab7494f5633ef682303a6b635f464e8c5e5c355a241869485f481d1f8ef1d0"
    target_words = struct.unpack("<12I", bytes.fromhex(target_hex))
    solved = []
    for block in range(3):
        inp = [z3.BitVec(f"w{block}_{i}", 32) for i in range(4)]
        final_words = f2_block(inp)
        desired_out = target_words[block*4:block*4+4]
        desired_final = [bswap(rol(x, k)) for x, k in zip(desired_out, (7,16,5,19))]
        s = z3.Solver()
        s.add(*[x == y for x, y in zip(final_words, desired_final)])
        print("block", block, s.check())
        candidates = []
        while len(candidates) < 16 and s.check() == z3.sat:
            m = s.model()
            values = [m.eval(x).as_long() for x in inp]
            candidates.append(values)
            s.add(z3.Or(*[x != y for x, y in zip(inp, values)]))
        print("candidates", len(candidates), "more" if s.check() == z3.sat else "complete")
        for values in candidates:
            print(" ".join(f"{x:08x}" for x in values))
        solved.extend(candidates[0])
    print("stage1=" + b"".join(struct.pack(">I", x) for x in solved).hex())


if __name__ == "__main__":
    main()
