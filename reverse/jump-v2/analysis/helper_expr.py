import angr
import claripy

p = angr.Project(__file__.replace("helper_expr.py", "embedded.elf"), auto_load_libs=False)
for start, ret in [(0x544218, 0x5443F9), (0x5443FA, 0x54450C), (0x54450D, 0x5446C9)]:
    args = [claripy.BVS(f"a{i}_{start:x}", 32) for i in range(4)]
    s = p.factory.call_state(start, *args)
    sm = p.factory.simulation_manager(s)
    sm.explore(find=ret)
    assert sm.found, (hex(start), sm)
    expr = sm.found[0].regs.eax
    print(hex(start), expr.depth, len(str(expr)))
    print(claripy.simplify(expr))
