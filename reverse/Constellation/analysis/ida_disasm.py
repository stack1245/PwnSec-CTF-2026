import pathlib

import ida_auto
import ida_bytes
import ida_kernwin
import ida_lines
import idaapi
import idc


OUT = pathlib.Path(__file__).with_name("ida_disasm.txt")
ida_auto.auto_wait()

with OUT.open("w", encoding="utf-8", newline="\n") as out:
    for start, end in ((0x140038E50, 0x140038F10), (0x1400396C0, 0x140039790)):
        out.write(f"===== {start:#x} =====\n")
        ea = start
        while ea < end:
            line = idc.generate_disasm_line(ea, 0)
            out.write(f"{ea:#x}: {ida_lines.tag_remove(line or '')}\n")
            ea = ida_bytes.next_head(ea, end)

ida_kernwin.msg(f"Wrote {OUT}\n")
idaapi.qexit(0)
