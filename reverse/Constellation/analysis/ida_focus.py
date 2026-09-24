import pathlib

import ida_auto
import ida_funcs
import ida_hexrays
import ida_kernwin
import ida_name
import idaapi
import idautils


OUT = pathlib.Path(__file__).with_name("ida_focus.txt")
SEEDS = {
    0x140033DF0: "configure_paths",
    0x1400368C0: "parse_materialization_plan",
    0x1400383A0: "materialize",
    0x140039200: "consume_stream_record",
    0x140061370: "GetKeyState_iat",
    0x1400620A8: "container_magic",
    0x1400620B0: "container_seed",
    0x140062018: "plan_magic",
    0x140032020: "sort_or_shuffle_shards",
    0x140031B60: "copy_input_chunk",
    0x140007050: "append_raw_string",
    0x140036540: "build_xor_keystream",
}


ida_auto.auto_wait()
functions = {}
for seed in SEEDS:
    fn = ida_funcs.get_func(seed)
    if fn and fn.start_ea == seed:
        functions[fn.start_ea] = fn
frontier = set(SEEDS)
seen = set()

for _depth in range(3):
    next_frontier = set()
    for target in frontier - seen:
        seen.add(target)
        for xref in idautils.XrefsTo(target):
            fn = ida_funcs.get_func(xref.frm)
            if fn:
                functions[fn.start_ea] = fn
                next_frontier.add(fn.start_ea)
    frontier = next_frontier

with OUT.open("w", encoding="utf-8", newline="\n") as out:
    for target, label in SEEDS.items():
        out.write(f"{label} 0x{target:x}\n")
        for xref in idautils.XrefsTo(target):
            fn = ida_funcs.get_func(xref.frm)
            name = ida_name.get_name(fn.start_ea) if fn else "<none>"
            out.write(f"  0x{xref.frm:x} {name}\n")

    for ea in sorted(functions):
        out.write(f"\n===== 0x{ea:x} {ida_name.get_name(ea)} =====\n")
        try:
            out.write(str(ida_hexrays.decompile(ea)))
            out.write("\n")
        except Exception as exc:
            out.write(f"decompile failed: {exc!r}\n")

ida_kernwin.msg(f"Wrote {OUT}\n")
idaapi.qexit(0)
