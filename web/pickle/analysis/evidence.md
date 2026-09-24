# pickle analysis evidence

- Official challenge name: `pickle`
- Event: `PwnSec CTF 2026`
- Category / difficulty: `web` / `Easy`
- Verified endpoint: `https://d5680026f8c80379.chal.ctf.ae`

## Confirmed behavior

`webapp.py` base64-decodes `payload`, scans the decoded bytes for banned
substrings, and calls `pickletools.dis()`. Any exception from disassembly is
caught and converted to `"Error!"`; the same bytes are then passed to
`RestrictedUnpickler.load()`.

The exploit deliberately omits pickle's `STOP` opcode (`0x2e`). This gives the
following sequence:

1. `pickletools.dis()` executes no payload but raises at EOF, so the `REDUCE`
   text check is skipped.
2. `RestrictedUnpickler.load()` executes all preceding `REDUCE` opcodes and
   only then raises at EOF.
3. The application suppresses that unpickling exception while retaining text
   printed before EOF.

All strings are emitted with protocol-0 `UNICODE` opcodes whose contents use
`\\uXXXX` escapes. The decoded names are usable by `STACK_GLOBAL`, while the
raw pickle contains none of `.`, `flag`, or `getattr`.

The allowed global
`sessionstore.render.__globals__.__class__.__getitem__` resolves to the unbound
`dict.__getitem__` descriptor. Combined with
`sessionstore.render.__globals__.__getitem__('__builtins__')`, it recovers
`open`, `getattr`, and `print`. The payload opens `/app/flag.txt`, calls
`read()`, and prints the result into the application's redirected stdout.

## Local verification

Command, run with the competition virtual environment:

```text
python analysis/payload_probe.py
```

The test confirmed that disassembly raises `ValueError`, every raw byte filter
passes, and the supplied local placeholder file is printed by the restricted
unpickler. The placeholder is not treated as the remote flag.

## Remote verification

On 2026-09-12, the replacement hostname accepted connections on TCP 443. A
normal GET returned the Time Capsule page, and a valid terminated pickle sent
to `POST /restore` was rejected by the raw `.` blocklist. The exploit solver
then completed with exit code 0 and stdout containing only the 24-byte flag:

```text
pwnsec{d51962f679918668}
```

The recorded `flag` file contains the same 24 bytes with no trailing newline.
