import json
import pathlib
import sys
import threading

import frida


pid = int(sys.argv[1])
out_dir = pathlib.Path(__file__).parent
done = threading.Event()
parts = {}

source = r"""
const target = Process.mainModule.base.add(0x383a0);
let fired = false;
Interceptor.attach(target, {
  onEnter(args) {
    if (fired) return;
    fired = true;
    const p = args[2];
    const meta = {
      width: p.readU32(),
      data_shards: p.add(4).readU32(),
      parity_shards: p.add(8).readU32(),
      blocks: p.add(12).readU32()
    };
    const vectors = [
      ["field", 16, 24],
      ["matrix", 40, 48],
      ["order", 64, 72]
    ];
    send({type: "meta", value: meta});
    for (const [name, beginOff, endOff] of vectors) {
      const begin = p.add(beginOff).readPointer();
      const end = p.add(endOff).readPointer();
      const size = end.sub(begin).toInt32();
      send({type: "part", name: name, size: size}, begin.readByteArray(size));
    }
    send({type: "done"});
  }
});
send({type: "ready", target: target.toString()});
"""


def on_message(message, data):
    if message["type"] == "error":
        print(message, flush=True)
        done.set()
        return
    payload = message["payload"]
    print(payload, flush=True)
    if payload["type"] == "meta":
        (out_dir / "plan_meta.json").write_text(
            json.dumps(payload["value"], indent=2) + "\n", encoding="utf-8"
        )
    elif payload["type"] == "part":
        parts[payload["name"]] = bytes(data)
        (out_dir / f"plan_{payload['name']}.bin").write_bytes(data)
    elif payload["type"] == "done":
        done.set()


session = frida.attach(pid)
script = session.create_script(source)
script.on("message", on_message)
script.load()
done.wait()
session.detach()
