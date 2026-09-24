#!/usr/bin/env python3
"""Concrete emulator for the extracted jump-v2 payload."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from unicorn import Uc, UC_ARCH_X86, UC_HOOK_BLOCK, UC_HOOK_CODE, UC_HOOK_INSN, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MODE_64
from unicorn.x86_const import UC_X86_INS_SYSCALL, UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDI, UC_X86_REG_RDX, UC_X86_REG_RIP, UC_X86_REG_RSI, UC_X86_REG_RSP, UC_X86_REG_XMM0, UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3


BASE = 0x400000
MAP_SIZE = 0x148000
STACK_BASE = 0x7FFF00000000
STACK_SIZE = 0x20000
INPUT_ADDRESS = 0x5463A0
STATE_START = 0x5463D0
STATE_END = 0x546460


def load_elf(path: Path) -> tuple[bytes, int, list[tuple[int, int, int]]]:
    blob = path.read_bytes()
    entry = struct.unpack_from("<Q", blob, 0x18)[0]
    phoff = struct.unpack_from("<Q", blob, 0x20)[0]
    phentsize, phnum = struct.unpack_from("<HH", blob, 0x36)
    segments = []
    for index in range(phnum):
        offset = phoff + index * phentsize
        p_type, _flags, p_offset, p_vaddr, _paddr, p_filesz, _memsz, _align = struct.unpack_from(
            "<IIQQQQQQ", blob, offset
        )
        if p_type == 1:
            segments.append((p_offset, p_vaddr, p_filesz))
    return blob, entry, segments


def emulate(path: Path, input_bytes: bytes, trace_path: Path | None) -> bytes:
    if len(input_bytes) != 48:
        raise ValueError("input must be exactly 48 bytes")

    blob, entry, segments = load_elf(path)
    uc = Uc(UC_ARCH_X86, UC_MODE_64)
    uc.mem_map(BASE, MAP_SIZE)
    for offset, address, size in segments:
        uc.mem_write(address, blob[offset : offset + size])
    uc.mem_write(INPUT_ADDRESS, input_bytes)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.reg_write(UC_X86_REG_RSP, STACK_BASE + STACK_SIZE - 0x1000)

    output = bytearray()
    blocks: list[tuple[int, int]] = []
    seen: set[int] = set()
    writes: list[str] = []
    accesses: list[str] = []
    snapshots: list[str] = []
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    output_phase = [False]

    def on_code(_uc: Uc, address: int, size: int, _data: object) -> None:
        if address == 0x51ECE3:
            output_phase[0] = True
        if not output_phase[0]:
            return
        ins = next(md.disasm(bytes(_uc.mem_read(address, size)), address), None)
        if ins is not None:
            op = f"{ins.mnemonic} {ins.op_str}".rstrip()
            if ins.mnemonic in {"mov", "movzx", "movsx", "xor", "add", "sub", "imul", "mul", "rol", "ror", "shl", "shr", "sar", "bswap", "not", "and", "or", "neg"}:
                if not any(f"xmm{i}" in ins.op_str for i in range(5, 16)):
                    accesses.append(f"OUT {address:#x} {op}")
        if address == 0x53AE00:
            output_phase[0] = False

    def on_block(_uc: Uc, address: int, _size: int, _data: object) -> None:
        if address == 0x50AEE3:
            accesses.append(f"XOR eax={_uc.reg_read(UC_X86_REG_RAX):#x} rcx={_uc.reg_read(UC_X86_REG_RCX):#x}")
        if address in {0x4C5B5B, 0x4C5B60, 0x4C5B65, 0x4C5B6A}:
            memory = bytes(_uc.mem_read(INPUT_ADDRESS, 0xBC))
            snapshots.append(f"after={address:#x} memory={memory.hex()}")
        if address not in seen:
            seen.add(address)
            blocks.append((address, _size))

    def on_write(_uc: Uc, _access: int, address: int, size: int, value: int, _data: object) -> None:
        if address < STATE_END and address + size > STATE_START:
            writes.append(f"{address:#x} {size} {value:#x} rip={_uc.reg_read(UC_X86_REG_RIP):#x}")

    def on_read(_uc: Uc, _access: int, address: int, size: int, _value: int, _data: object) -> None:
        if INPUT_ADDRESS <= address < STATE_END:
            accesses.append(f"R {address:#x} {size} rip={_uc.reg_read(UC_X86_REG_RIP):#x}")
        if 0x545000 <= address < 0x5453A0 and _uc.reg_read(UC_X86_REG_RIP) in {0x530C1E,0x5008DC,0x4D8AC8,0x50D61A}:
            accesses.append(f"KEY rip={_uc.reg_read(UC_X86_REG_RIP):#x} addr={address:#x} size={size}")

    def on_syscall(_uc: Uc, _data: object) -> None:
        number = _uc.reg_read(UC_X86_REG_RAX)
        arg0 = _uc.reg_read(UC_X86_REG_RDI)
        arg1 = _uc.reg_read(UC_X86_REG_RSI)
        arg2 = _uc.reg_read(UC_X86_REG_RDX)
        if number == 1:
            output.extend(bytes(_uc.mem_read(arg1, arg2)))
            result = arg2
        elif number == 60:
            _uc.emu_stop()
            result = 0
        elif number == 157:
            result = 0
        elif 0x1337 <= number <= 0x1344:
            writes.append(f"syscall={number:#x} arg0={arg0:#x}")
            result = (1 << 64) - 38
        else:
            raise RuntimeError(f"unhandled syscall {number:#x}")
        _uc.reg_write(UC_X86_REG_RAX, result)

    uc.hook_add(UC_HOOK_BLOCK, on_block)
    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.hook_add(UC_HOOK_CODE, lambda u, a, _s, _d: accesses.append(f"XOR eax={u.reg_read(UC_X86_REG_RAX):#x} rcx={u.reg_read(UC_X86_REG_RCX):#x}"), None, 0x50AEE3, 0x50AEE3)
    for marker in (0x512A66, 0x4C6C16, 0x4DF362, 0x4FAE45):
        uc.hook_add(UC_HOOK_CODE, lambda u, a, _s, _d: accesses.append(f"OP {a:#x} eax={u.reg_read(UC_X86_REG_RAX):#x}"), None, marker, marker)
    for marker in (0x53C3FD, 0x4D0848, 0x4FFBA1, 0x50F89A, 0x51AFFD):
        uc.hook_add(UC_HOOK_CODE, lambda u, a, _s, _d: accesses.append(f"F3 {a:#x} eax={u.reg_read(UC_X86_REG_RAX):#x} edx={u.reg_read(UC_X86_REG_RDX):#x} ecx={u.reg_read(UC_X86_REG_RCX):#x}"), None, marker, marker)
    for marker in (0x544218, 0x5443FA, 0x54450D):
        uc.hook_add(UC_HOOK_CODE, lambda u, a, _s, _d: accesses.append(f"CALL {a:#x} a={u.reg_read(UC_X86_REG_RDI)&0xffffffff:#x} b={u.reg_read(UC_X86_REG_RSI)&0xffffffff:#x} c={u.reg_read(UC_X86_REG_RDX)&0xffffffff:#x} d={u.reg_read(UC_X86_REG_RCX)&0xffffffff:#x}"), None, marker, marker)
    for marker in (0x5443F9, 0x54450C, 0x5446C9):
        uc.hook_add(UC_HOOK_CODE, lambda u, a, _s, _d: accesses.append(f"RET {a:#x} eax={u.reg_read(UC_X86_REG_RAX)&0xffffffff:#x}"), None, marker, marker)
    for marker in (0x533A2A, 0x52A8B3):
        uc.hook_add(UC_HOOK_CODE, lambda u, a, _s, _d: accesses.append("F1 " + f"{a:#x} " + " ".join(int(u.reg_read(r)).to_bytes(16,'little').hex() for r in (UC_X86_REG_XMM0,UC_X86_REG_XMM1,UC_X86_REG_XMM2,UC_X86_REG_XMM3))), None, marker, marker)
    uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(UC_HOOK_MEM_READ, on_read)
    uc.hook_add(UC_HOOK_INSN, on_syscall, None, 1, 0, UC_X86_INS_SYSCALL)
    uc.emu_start(entry, BASE + MAP_SIZE, count=20_000_000)

    if trace_path is not None:
        lines = [f"blocks={len(blocks)}"]
        for address, size in blocks:
            code = bytes(uc.mem_read(address, size))
            rendered = []
            for instruction in md.disasm(code, address):
                text = f"{instruction.mnemonic} {instruction.op_str}".rstrip()
                if instruction.mnemonic in {"nop", "pause", "lfence"}:
                    continue
                if any(f"xmm{index}" in instruction.op_str for index in range(5, 16)):
                    continue
                rendered.append(f"{instruction.address:#x}: {text}")
            lines.extend(rendered or [f"{address:#x}: <junk block size={size:#x}>"])
        lines.append("writes:")
        lines.extend(accesses)
        lines.extend(snapshots)
        lines.extend(writes)
        trace_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    state = bytes(uc.mem_read(0x546424, 14 * 4))
    print("state=" + state.hex())
    print("output=" + output.decode("latin-1"))
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--elf", type=Path, default=Path(__file__).with_name("embedded.elf"))
    parser.add_argument("--input", default="A" * 48)
    parser.add_argument("--trace", type=Path)
    args = parser.parse_args()
    emulate(args.elf, args.input.encode("latin-1"), args.trace)


if __name__ == "__main__":
    main()
