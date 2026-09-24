# Evidence and technique mapping

## Preserved source

- Source: `../challenge/codex-clipboard-693933eb-7841-4998-80ed-4c1a134a7b2c.png`
- SHA-256: `a63bd7ab2a2fcbcf6dd70fbe65575bcf23dfebee323da9234c8713ad1fd21651`
- Official challenge name: `Spiny Trace 1 - Initial Access`
- Event: `PwnSec CTF 2026`
- Category: `Forensics`
- Difficulty: `Easy`
- Points: `1`

The screenshot states that the attacker did not exploit a service or send an
attachment. Instead, the victim ran the code, believing it was a routine
verification step. It requests the MITRE ATT&CK sub-technique in the format
`T1234.001`; the submission field has the generic placeholder `pwnsec{...}`.

## Mapping

MITRE ATT&CK defines `T1204.004`, **User Execution: Malicious Copy and Paste**,
as gaining execution by socially engineering a user into copying and pasting
code into a command interpreter. MITRE explicitly identifies fake CAPTCHA or
error-resolution prompts as the ClickFix pattern. This uniquely matches the
victim-run verification lure and the explicit absence of an attachment.

`T1204.002` (**Malicious File**) is excluded because the prompt says no
attachment was sent. `T1204.001` (**Malicious Link**) does not describe the
decisive execution action: the user ran supplied code.

## Rejected submission and revised candidate

- Rejected by the platform: `pwnsec{T1204.004}` (reported by the user)
- The challenge's explicit answer format is an unwrapped ATT&CK ID.
- Revised submission candidate: `T1204.004`
- Status: unverified until the raw ID is accepted by the platform.

## Reference

- MITRE ATT&CK, [User Execution: Malicious Copy and Paste, T1204.004](https://attack.mitre.org/techniques/T1204/004/)
