import pathlib

import ida_auto
import ida_hexrays
import ida_kernwin
import ida_name
import idaapi
import idautils


OUT = pathlib.Path(__file__).with_name("ida_session.txt")
ida_auto.auto_wait()

with OUT.open("w", encoding="utf-8", newline="\n") as out:
    for ea in idautils.Functions(0x140038E00, 0x140039A00):
        out.write(f"\n===== 0x{ea:x} {ida_name.get_name(ea)} =====\n")
        try:
            out.write(str(ida_hexrays.decompile(ea)))
            out.write("\n")
        except Exception as exc:
            out.write(f"decompile failed: {exc!r}\n")

ida_kernwin.msg(f"Wrote {OUT}\n")
idaapi.qexit(0)
