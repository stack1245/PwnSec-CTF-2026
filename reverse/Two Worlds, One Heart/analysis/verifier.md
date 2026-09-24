# Verifier evidence

- Official archive SHA-256: `16f7079aec0118b57faca43cc0b2fa73963887b9d3bc5837f944e9eddf8b11d9`
- `portal33.exe` SHA-256: `d35911333fae7cfc7a305c93e2f14cad678487ef724d4ea610c3e047a42194f0`
- Format: PE32 console executable, Intel i386, eight sections.
- The input length check at VA `0x408e1e` requires `0x28` (40) bytes.
- The first direct call to VA `0x401600` executes the function as 32-bit code.
- The wrapper at VA `0x4016b3` uses `retf` with selectors `0x33` and `0x23` to call the same bytes at VA `0x401600` as 64-bit code and return to 32-bit mode.

The 32-bit interpretation checks five little-endian 32-bit words. For target
`T[i]`, it computes `ROL32(word[i] XOR previous, 11)`, where `previous` is
`0x1337c0de` for the first word and `T[i-1]` afterward.

The 64-bit interpretation skips that block because the bytes `31 c0 48 85 c0`
decode as `xor eax,eax; test rax,rax`. It then checks two 64-bit words and one
32-bit word:

```text
ROL64(qword[0] XOR 0x5a33c0d313379090, 19) == 0x87326027c52b7005
ROL64(qword[1] XOR 0x87326027c52b7005, 29) == 0x7e6e88add6ebc7e2
ROL32(word[9] XOR 0xd6ebc7e2, 13)          == 0x5e929579
```

`solve.py` reads these immediates from the original PE, applies the inverse
rotations and XOR operations, and independently replays both verifier paths.
