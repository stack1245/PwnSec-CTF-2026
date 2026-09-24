import pathlib

import ida_auto
import ida_funcs
import ida_hexrays
import ida_kernwin
import ida_name
import idaapi
import idautils


OUT = pathlib.Path(__file__).with_name("ida_report.txt")
NEEDLES = (
    "input file path",
    "input open failed",
    "invalid archive path",
    "invalid materialization plan",
    "invalid materialization field",
    "write failed",
    "invalid host path",
    "invalid input path",
    "invalid input name",
)


ida_auto.auto_wait()
strings = list(idautils.Strings())
targets = [s for s in strings if any(n in str(s).lower() for n in NEEDLES)]
functions = {}

for s in targets:
    for xref in idautils.XrefsTo(s.ea):
        fn = ida_funcs.get_func(xref.frm)
        if fn:
            functions[fn.start_ea] = fn

with OUT.open("w", encoding="utf-8", newline="\n") as out:
    out.write(f"imagebase: 0x{idaapi.get_imagebase():x}\n")
    out.write(f"functions: {sum(1 for _ in idautils.Functions())}\n")
    out.write("\nstrings and xrefs:\n")
    for s in targets:
        out.write(f"0x{s.ea:x} {str(s)!r}\n")
        for xref in idautils.XrefsTo(s.ea):
            fn = ida_funcs.get_func(xref.frm)
            name = ida_name.get_name(fn.start_ea) if fn else "<no function>"
            out.write(f"  xref 0x{xref.frm:x} in {name}\n")

    out.write("\ndecompiled functions:\n")
    for ea in sorted(functions):
        name = ida_name.get_name(ea)
        out.write(f"\n===== 0x{ea:x} {name} =====\n")
        try:
            out.write(str(ida_hexrays.decompile(ea)))
            out.write("\n")
        except Exception as exc:
            out.write(f"decompile failed: {exc!r}\n")

ida_kernwin.msg(f"Wrote {OUT}\n")
idaapi.qexit(0)
