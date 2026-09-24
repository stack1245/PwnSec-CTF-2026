#!/usr/bin/env python3
import angr
import claripy

ELF = __file__.replace("angr_solve.py", "embedded.elf")
INPUT = 0x5463A0
TARGET = 0x4C5B6A

p = angr.Project(ELF, auto_load_libs=False)
s = p.factory.blank_state(addr=0x4C4A16)
s.regs.rsp = 0x7fff0001f000
chars = [claripy.BVS(f"c{i}", 8) for i in range(48)]
s.memory.store(INPUT, claripy.Concat(*chars))
for c in chars:
    s.solver.add(c >= 0x20, c <= 0x7e)
s.solver.add(claripy.Concat(*chars[:7]) == claripy.BVV(b"pwnsec{"))
s.solver.add(chars[-1] == ord("}"))

simgr = p.factory.simulation_manager(s)
simgr.explore(find=TARGET)
print(simgr)
if not simgr.found:
    print("active", [hex(x.addr) for x in simgr.active[:5]])
    for e in simgr.errored[-5:]:
        print(hex(e.state.addr), repr(e.error))
    raise SystemExit(1)
s = simgr.found[0]

filters = [
    (0xEE1E21D3,0x47A950EA,0xFFFFD7FF,0xD69387A1),
    (0x839147A7,0x7FC32323,0x7FF7FFFF,0x6187C472),
    (0x8FC6507E,0x7E57D78F,0xF7FFFFFF,0xD75652BB),
    (0x2F0C5C28,0xE7A95C45,0xFFFDFFBF,0x1644139F),
    (0x10BCBF2A,0xE661B56D,0xFFFF7FFF,0xE19E5C29),
    (0xF36DC466,0xD4BBA89D,0xDFFFF7FF,0xD94BB5CF),
    (0x89909155,0xD721F072,0xFEF7FFFF,0xE27381E8),
    (0xEB363EB0,0xB2E621B4,0xFFFFEFFF,0xE1B6E526),
    (0x9996E133,0x8BE61102,0xFFFFFCFF,0x7FEF1C20),
    (0xF2D215F6,0x88EFCBEE,0xFEFFFFFF,0xE01DA4FB),
    (0x1B679102,0xD4AD5630,0x6FFFFFFF,0x6251D31B),
    (0xEDB3D91C,0xB34BE313,0xFFF3FFFF,0xA9C1C8B5),
    (0x103B25D7,0x3F084E11,0xFFFFFFFF,0x6B5E3D1E),
]
for i, (k1,k2,mask,target) in enumerate(filters):
    x = s.memory.load(0x546424 + 4*i, 4, endness=p.arch.memory_endness)
    s.solver.add(((x ^ k1) + k2) & mask == target)

print("sat", s.solver.satisfiable())
if s.solver.satisfiable():
    answer = bytes(s.solver.eval(c) for c in chars)
    print(answer)
