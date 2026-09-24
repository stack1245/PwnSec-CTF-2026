# Skill routing

- Primary: ctf-pwn
- Secondary: binary-exploitation-technique, checksec
- Evidence: The official category is pwn; the provided archive contains a native `prob` binary and `libcrypto.so.3`; the endpoint is a TLS-wrapped raw socket.
- Roles: ctf-pwn drives exploit development; binary-exploitation-technique qualifies the primitive and mitigation-aware chain; checksec inventories ELF protections.
- Re-evaluate when: the binary is a non-memory-corruption sandbox, or understanding its behavior becomes the primary blocker.
