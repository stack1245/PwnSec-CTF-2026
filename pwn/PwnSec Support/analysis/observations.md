# Preserved observations

- `challenge/public.zip` SHA-256: `5bc18048f33f8b9df6f8cf246c7526fdd9f34fa411ba055b84b781ff3e1bbd49`.
- `challenge/l3afvm` is a stripped x86-64 PIE ELF. NX and GNU RELRO are present.
- The binary requests `sqrtf@GLIBC_2.43`; the supplied Debian bookworm image cannot satisfy that version. `analysis/l3afvm.compat` changes only the ELF version mapping for `sqrtf` and is not an input to `solve.py`.
- Local `--trace` load map: `data=0x00010000..0x003f9d04 code=0x003f9d10..0x006b2fd0 (178476 instructions)`.
- The local handout's `FLAG` is the 24-byte test value `pwnsec{test_local_build}`. It is not the remote answer.
- The extracted Lua application is preserved under `analysis/lua/`.
- `/admin` concatenates the token into SQL without `sql_param()`. The payload `' UNION SELECT 1, 'root' FROM users -- ` reaches the Lua console even when `sessions` is empty.
- `note_save(address, value)` stores a 32-bit word into writable VM memory. Its exposed function address is `code_base + 0x4150`.
- `FLAG` begins at `code_base - 0x24`. The `LC` that supplies the buffer to `lua_pushlstring` in `rand_hex` is at `code_base + 0x50c0`, and its immediate word is at instruction offset `+8`.
- Therefore `note_save(n + 0xf78, n - 0x4174)` redirects `rand_hex(24)` to the flag while remaining independent of the randomized `FLAGPAD` size.
