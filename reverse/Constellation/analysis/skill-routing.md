# Skill routing

- Primary: ctf-reverse
- Evidence: The official category is Reverse Engineering and the provided archive contains a large Windows PE executable plus a custom `.flag` artifact.
- Role: Recover the validation/decoding logic and produce a reproducible solver.
- Re-evaluate when: the executable reduces to a standalone cryptographic construction, or a memory-corruption primitive becomes the actual blocker.
