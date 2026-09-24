import ast
import re
from pathlib import Path


lines = (Path(__file__).parent / "extracted" / "ycc.c").read_text().splitlines()
for number in range(0, 61):
    start = next(
        index
        for index, line in enumerate(lines)
        if line.startswith(f"static YValue *yfn_{number}(")
    )
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("static YValue *yfn_")
        ),
        len(lines),
    )
    body = "\n".join(lines[start:end])
    print(f"--- yfn_{number} ---")
    for match in re.finditer(r'y_mk_str\(("(?:\\.|[^"\\])*")\)', body):
        print(repr(ast.literal_eval(match.group(1))))
