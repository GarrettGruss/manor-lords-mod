# AES key search in the game files

Result: the key was NOT found. No key file was written.

## Pak facts
- Smallest pak: `pakchunk0_s2optional-Windows.pak`. Pak version 11. The index is encrypted.
- Test used: decrypt the first 16 bytes of the primary index with AES-256-ECB.
  A right key gives a small string length and the text `../` (the mount point).
  This test is fast, so millions of candidates are possible. It is not repak.

## What was tried (all read-only)
1. Text search for "aes" or "encryption key" in ini, json, txt, cfg and xml files in the game folder: no match.
2. Binary scan of `ManorLords-Win64-Shipping.exe` (161 MB, not packed, no high-entropy code section):
   - All 4-byte aligned 32-byte windows with at least 24 distinct byte values (6.6 million). Forms: direct, per-4-byte swapped, reversed.
   - All unaligned windows with at least 22 distinct byte values.
   - Hex strings (64 chars, optional `0x`) and base64 strings (44 chars), also in crude UTF-16 form: 1 candidate, wrong.
   - Keys built from code immediates: runs of `mov dword [mem], imm32` (in order and sorted by displacement),
     `mov r64, imm64` groups of 4 (all 24 orders), and `mov r32, imm32` runs.
3. The same aligned scan on 259 other files in the game folder (dlls, ini, json, and so on), without the paks: no match.

## Conclusion
The key is not stored as a plain 32-byte blob or as simple immediates. It is likely obfuscated
(for example XOR with a mask, or built at run time) or kept in a form this scan does not cover.

## Next options
- Disassemble the code that calls the pak key registration (`FCoreDelegates::GetPakEncryptionKeyDelegate`) and follow it.
- Ask the user if they already have the key from a trusted source.
- Read the key from the running game memory. This needs the user's approval, because the project rules limit game attachment.

## Memory scan (2026-10-10)
Result: the key WAS found. It is stored only in the gitignored file `modtools/work/aes_key.txt`.
Fingerprint (first 8 hex of SHA-256): `466bc88e`.

Method (read-only):
- Started the game exe directly (Steam closed), waited 90 s, opened the process with
  `PROCESS_QUERY_INFORMATION | PROCESS_VM_READ` only, then killed the game process.
- Listed committed, readable regions with `VirtualQueryEx` (no guard, no noaccess). Read them with `ReadProcessMemory`.
- Took every 4-byte aligned 32-byte window with at least 24 distinct byte values and not all printable.
  Tried direct, per-4-byte swapped and reversed forms.
- Tested each candidate with AES-256-ECB (Windows CNG) on the first 16 bytes of the encrypted index of `pakchunk0_s2optional-Windows.pak`.
- Small regions (under 64 MB) went first. The key was found in them: about 119 MB read, 25.8 million candidate tests.
  The large regions and the 1-byte stride pass were not needed.

Proof: `repak.exe --aes-key <KEY> list <pak>` works on all 22 paks in the Paks folder.
`pakchunk0-Windows.pak`: pak version 11, mount point `../../../`, 4750 entries, index encrypted.
Table files are in other paks (`DT_Items`, `DT_MercenaryCompanies` in s11; `DT_Alerts` in s4). No `DT_units` file was found by name.
