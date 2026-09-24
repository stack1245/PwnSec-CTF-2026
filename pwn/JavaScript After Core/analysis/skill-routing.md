# Skill routing

- Primary: ctf-pwn
- Evidence: The challenge supplies a pinned JavaScriptCore revision and a shell patch, and requires violating JavaScript string immutability across two native callback invocations.
- Role: Identify the pre-fix JavaScriptCore memory-corruption primitive, reproduce it against the supplied build, and turn it into a reliable single-shot TLS exploit.
- Re-evaluate when: Static and dynamic evidence shows this is a pure shell logic bug without a native memory-corruption primitive, or bytecode/runtime understanding becomes the blocker.
