# ML Battle Scenarios 1 (0.2) (inspection note)

Date: 2026-10-11. Source: `C:\Users\garre\Downloads\ML Battle Scenarios 1 (0.2)-316-1-1774790095` (Nexus file id 316; 1774790095 is a Unix time, 2026-03-29). The `.7z` was already extracted. Nothing was loaded in the game. No README, no author, no license text.
Archive: `ML Battle Scenarios 1 (0.2)-316-1-1774790095.7z`, 4526370 bytes, SHA-256 `e3b343b510d414bdc43a569d3d8f95a1bfd49ee5995c8d2f06c6ff1404f18979`.

## Files
| File | Size | SHA-256 |
|---|---|---|
| `saveGame_68.sav` | 3530885 | `ba2a660c97825747fd5794018ac1a037490f80ba056ae613c9e1ffedd5dce8e0` |
| `saveGame_68_descr.sav` | 2169 | `5fcb8be20b3358bf1bb8a699131091300c3aeb011e56bc1e6d028152812d0abe` |
| `saveGame_68.png` | 770048 | `aa246694cd6b39da74606c57bfc142a70bf897b23349b615ac7b08b2f5872166` |
| `saveGame_68_coat_0.png` | 282624 | `5500061181ec7102665f198991f45fffa86a9c5f1cc374a5bb81386b27a8b42b` |
| `saveGame_68_coat_1.png` | 69632 | `c01391e970cdcccf30dec8a0acdaddb1d0299825780630b71f1ea757c75d2c79` |
| `saveGame_68_coat_2.png` | 49152 | `8c911436d84f19313765db26d970c43f31614da5380e4b314c29b32f0f4bf948` |
| `saveGame_68_coat_3.png` | 102400 | `b86c7f5da004d7e728fbc9c399e85c7ccf3ea2bb47c1cb568a04a3ca0fb1df27` |
| `saveGame_68_coat_4.png` | 32752 | `b7af5abdfa148e66474d3dd1ec9e1012f0b1431dcb6dc3800e1b2832d2ad84cd` |
The task text said "2 .sav files": there are two (`saveGame_68.sav`, the world; `saveGame_68_descr.sav`, the description for the load menu). The images are the screenshot and 5 coats of arms.

## What it does for the player
It is a save game, not a mod. The player copies it into the save folder as slot 68 and loads it. The description says: "Scenario 1 - Village Defense with Castle on Hill" (the `saveName` field). The screenshot shows a defender army in front of a stone castle on a hill, with green banners.

## What is inside (printable strings and header only)
- `saveGame_68_descr.sav` is an uncompressed UE save (magic `GVAS`). It holds class `/Script/ManorLords.MLSaveGameDescr` with fields: `Version` = "Version 0.8.065", `saveVersion` = 1 (the Int field after the name), `LevelName` = `TwinLakes`, `saveName` = the scenario name, `saveSlot` = `saveGame_68`, `UncompressedSize` of about 92 MB (read as the Int value 0x0583F960; not cross-checked), and a `date` (DateTime).
- `saveGame_68.sav` has an 8 byte prefix and then `GVAS`; the body is compressed (names show only in fragments: `MLSaveGame`, `savedRegion`, `Bilweisholz`, `Population`, `approvalFactorType`, `ExpirationDay`, `pay_mercenaries`, `moneyInBox`, `Heintzhildebolt_male`, `RegensburgGuildsmen`, `romMilitiaEquip...`). One `Squad`, one `Militia`, one `Mercenar`, one `Brigand` string only. So squads and units cannot be read without the game's decompression.
- Result: map is TwinLakes (a different map from our fixture `base` on Jagged Cliffs). The scenario is a village defense: the player army with a castle; the enemy is not named in the readable strings.

## Game version and signs it is stale
The save is from **0.8.065**. Our game is 0.8.111. Old saves load in Manor Lords only if the game accepts the version; 0.8.065 is 46 builds older. No jmap check is possible for a save. Names inside the compressed body cannot be compared. Risk: a load could fail, crash, or change content (new buildings, a changed economy, the old unit tables).

## Risk review
- No code. A save cannot run code, but a bad or foreign save may crash the loader. We did not load it.
- Slot 68 may overwrite the user's own `saveGame_68` if it exists. Our rule: never write into the user's real save folder. The launcher runs with a private `LOCALAPPDATA` for saves; the safe path is to copy the save into the private folder, never into `%LOCALAPPDATA%\ManorLords\Saved\SaveGames`.
- Loading triggers the autosave timer (about 10 min after a load); `HarnessBoot` already sets it one year away.
- License: none given. The save belongs to the author. Using it as a test fixture needs the user's approval, and credit.

## Lessons for us
- Battle test fixtures: a saved army-in-place scenario removes the setup cost (no `spawn_army`, no marching). It fits tests of combat balance and unit stats (A/B with a pak) because the start state is identical in every run. The stand-in approach (spawn by template, 36 men) is already verified; a save adds terrain, a castle and walls. A fixture of our own, made on the current 0.8.111 build, is better than this 0.8.065 file.
- Raids and enemy scaling: none. Squad steering: none. Unit stats: none.
- How fixtures are used by the community: `.sav` plus `_descr.sav` plus PNGs, copied as a numbered slot. Our harness fixture format (private save folder) should keep the same three file kinds.

## Test idea for the harness
Not now. If the user approves later: make our own scenario save on 0.8.111 (a village with a militia and a baron army 30 000 units away), store it under `harness/fixtures` (git-ignored if large), and add a `battle-defense` scenario that loads it, runs 5 game days, and asserts ranges for losses on both sides over 3 runs. Check the loader first with a read-only run on a copy of this file in the private folder, expecting "refused" or "loaded" and recording which one.
