#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import frida


HERE = Path(__file__).resolve().parent


def main() -> None:
    program = str(HERE / "final.exe")
    pid = frida.spawn([program])
    session = frida.attach(pid)
    script_name = sys.argv[1] if len(sys.argv) > 1 else "memscan.js"
    script = session.create_script((HERE / script_name).read_text(encoding="utf-8"))
    def on_message(message, data):
        if data is not None and message.get("payload", {}).get("event") == "module-dump":
            (HERE / "final-memory.bin").write_bytes(data)
        print(json.dumps(message, ensure_ascii=True))

    script.on("message", on_message)
    script.load()
    frida.resume(pid)
    for _ in range(100):
        time.sleep(0.1)


if __name__ == "__main__":
    main()
