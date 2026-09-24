# Freal World Manipulation analysis evidence

## Inputs

- `challenge/public.zip`: SHA-256 `a430f617f71719c359cfc112010f8bc85cd6c2d6301a4dce7a8f3e21c513bb6e`
- `challenge/src/freal`: SHA-256 `ac344f5e738ebbc0c067d3637e24640bb593d1f703051a6cb6a5628163db0acb`
- Archive password supplied by the challenge page: `infected`
- Service: TLS on port 443, with mutable locator stored only in `instance.json`

## Binary observations

- ELF64 x86-64 PIE, dynamically linked, not stripped.
- NX follows from the non-executable `GNU_STACK` program header.
- Full RELRO follows from `GNU_RELRO` plus `BIND_NOW`.
- Stack canaries are present (`__stack_chk_fail` imports and canary checks).
- CET-compatible `endbr64` instructions are present, but the supplied ELF does not advertise enforced shadow-stack protection.

Important static offsets:

| Object | Offset |
|---|---:|
| `decimal` | `0x5060` |
| `__dso_handle` | `0x5008` |
| `puts@GOT` | `0x4f40` |
| `ret` | `0x101a` |
| `pop rdi; ret` | `0x14cf` |

## Root cause and exploit primitives

1. `view(-11)` makes `checked_slot` address `__dso_handle`. Its self-reference passes `coherent_pointer`, so `view` emits the relocated `__dso_handle` pointer and leaks the PIE base.
2. `add` accepts allocations up to `0x800000` bytes. After more than `0x1fffffff` page-rounded bytes are live, `calibrated()` succeeds.
3. `multiply` tests floating-point exceptions before performing the multiplication. Two parsed values `1e308` multiplied under upward rounding overflow to infinity, yet the code expands the global index bound from the allocation usable sizes.
4. A freed first 8 MiB mmap allocation raises glibc's dynamic mmap threshold. Subsequent 8 MiB allocations come from a contiguous `[heap]` mapping. Ten local probes placed its start between roughly PIE+`0x01700000` and PIE+`0x3b900000`.
5. Filling one 8 MiB allocation with repeated `p64(PIE+0x5060)` guarantees that one address in an 8 MiB-spaced scan over the 1 GiB heap randomization window dereferences to `decimal`.
6. The successful OOB slot becomes a write-through pointer to `decimal`. Rewriting slot 0 and its usable size gives direct arbitrary read and write through ordinary `view(0)` and `load(0)` operations.
7. The solver leaks `puts@GOT`, walks backward to the in-memory libc ELF header, resolves `system` and `__environ` through the remote GNU hash table, and leaks the stack.
8. The current `main` frame is located by its self-reference (`[rsp+8] == rsp+0x10`) and a saved return address inside libc. The solver writes a PIE `ret`, PIE `pop rdi; ret`, a command address, and remote `system` to that return slot.

## Verification evidence

- Shared environment synchronization: `python -m pip install -r requirements.txt` completed and `python -m pip check` reported `No broken requirements found.`
- The complete exploit chain was exercised against a local `socat` wrapper. With the final command temporarily replaced by `echo pwnsec{local_test}`, `solve.py` exited 0 and emitted exactly `pwnsec{local_test}`. The command and flag matcher were then restored to the remote challenge values.
- The first remote instance returned HTTP 404 with `Deployment not found. It may have expired...` and was replaced with the fresh endpoint `b31501f4e8de5bb6.chal.ctf.ae:443`.
- The unmodified restored solver completed against that fresh TLS endpoint with exit code 0 and stdout exactly `pwnsec{34910c7c74c2525b}`.
- The verified result was written as one line to the canonical `flag` file.

## Final verification

The local end-to-end run, live remote run, dependency check, and solved-status workspace validation all passed. No verification work remains.
