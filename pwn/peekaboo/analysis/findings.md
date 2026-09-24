# Findings

## Scope and primary artifacts

- Official archive SHA-256: `242e8768e1fd9d319f25ed4ef6e16987dcead7fda09c7c45b140d214cddcb43b`
- `prob` SHA-256: `57567baa2dd328da2d287630d9a20fb3efa193f0704af8a473ff47aae166ad59`
- Remote endpoint used before expiry: TLS on port 443, as recorded in `../instance.json`

## Confirmed behavior

- `prob` is a stripped x86-64 PIE with NX, stack canary, Full RELRO, IBT, and SHSTK properties.
- It seeds glibc `rand()` from three `/dev/urandom` bytes, uses the first `rand()` output to choose a page in `[0x100000000000, 0x100400000000)`, and copies the Base64 encrypted flag there.
- User code runs at `0x3133709a`. Seccomp permits `mmap`, `munmap`, `exit_group`, and `write` only when the buffer is in page `0x31339000` and the length is at most eight bytes.
- `MAP_FIXED_NOREPLACE` over a range returns `EEXIST` if the range overlaps the hidden page. Successful probes can be removed with `munmap`, enabling a 22-step binary search.
- The encryption key is the low byte of the next 32 glibc `rand()` outputs. The first 12 stored bytes are passed to `EVP_EncryptUpdate` as AAD; the cipher nonce remains twelve zero bytes. Storage is `AAD || tag || ciphertext`.

## Remote evidence captured before expiry

- Hidden mapping: `0x1001ac212000`
- Base64 blob: `5firVoD3pLZoBNpnZWijyP/zZ25rcDm8CKHB1BfUxaroee2ysiQd7NZJJpzSisirAmxqEQ==`
- Matching seed: `0x5abf7c`
- Authenticated plaintext: `pwnsec{ad7aa53d59d0f8af}`

The other address-matching seeds failed AES-256-GCM-SIV authentication, providing a negative control. A local run with a debugger-observed key and buffer decrypted `PWNSEC{local_validation_flag}\n`, confirming the zero-nonce/AAD interpretation independently.

## Fresh runtime verification

After `instance.json` was updated to the replacement instance, `solve.py` completed in 10.7 seconds with exit code 0, empty stderr, and the exact 24-byte authenticated flag on stdout.
