# Spec 13: Inspection of existing community mods

Status: inspection done (2026-10-11). Follow-up spikes are proposed in `implementation-notes/summary.md`; none ran yet.

## Goal
Learn from existing Manor Lords mods. The user downloaded 15 mods into `C:\Users\garre\Downloads` (already extracted next to their
archives). Some may target older game versions. For each mod, find out what it changes, how (Lua through UE4SS, a pak, a native DLL,
a save), which game objects and functions it uses, and what that teaches us for the harness and the invasion mod.

Several mods touch our open questions:
- `StorageAndManorUnlock` and `ManorLimit99`: manor storage and more manors per region (spec 12, criteria M1 and M2).
- `RefugeesExpanded` (a native C++ mod with source): refugees (spec 10, criterion P3, no method yet).
- `Battlefield Loot And Bandit Loot`: loot (criterion R3, now a stand-in ledger).
- `AdaptiveEnemies`, `AdaptiveMilitia`, `AdaptiveOrigins`, `AdaptiveRetinueManager`, `BetterBattlefieldMod`, `LargerFormations`,
  `ML Battle Scenarios`: raids, enemies, units and battles (spec 10 raid and combat criteria, spike S11).
- `MLModMenu`, `MLUE4SS-zDev`: tools (an in-game mod menu, a UE4SS build).
- `AllYearOrchards`, `TreeRegeneration`: seasons and resources (less relevant; read for techniques).

## Non-goals
- Installing, running or loading any of these mods in the game. That is a later step, one mod at a time, after review and with the user's approval.
- Running any file from the downloads (DLL, EXE, Lua, scripts). They are untrusted data.
- Copying mod code, assets or saves into this repo. Notes describe and cite (file and line, short quotes only). The mods belong to their authors.
- Changing the user's game folder or saves.

## Plan
1. Inventory: one row per mod in `implementation-notes/inventory.md` (name, version, target game version, type, files, size, author and license text if given).
2. Inspection by agents, in parallel, by group. One note per mod: `implementation-notes/<mod-slug>.md`. Each note answers:
   - What it does for the player (from its readme and its code).
   - How: mechanism (UE4SS Lua, pak with which assets, native DLL, save file), hooks, game classes, functions, properties and data tables it touches.
   - Game version it targets, and signs that it is stale (names that our jmap of 0.8.111 does not have).
   - Risk review: what native code does (from source if given; DLLs are not run, only listed), any file, network or process access.
   - Lessons for us: facts that answer a spec 10 or spec 12 question, techniques the harness or the invasion mod can use, and a test idea.
3. Check the key claims against our own data (jmap names, earlier notes) before they change a decision.
4. Summary in `implementation-notes/summary.md`: a table of lessons by criterion (M1, M2, P3, R3, raids, units) and proposed follow-up spikes.
5. Update spec 10 and spec 12 READMEs where a finding changes a plan.

## Rules for the inspection
- Read only in `C:\Users\garre\Downloads`. Do not run, install, or move anything there.
- Archives are already extracted. If something must be unpacked (a `.pak`), unpack it with the trusted local `repak` (`list`, `info`, `unpack`) into a new empty folder in the session scratchpad, never into the repo or the game folder.
  A pak asset may be converted to JSON with the repo's `harness/tools/pakmod.py` (UAssetGUI). Do not run anything from the mod folders.
- Binary files (`.dll`, `.lib`): record name, size and SHA-256. Do not run them. Reading printable strings is allowed.
- Lua and C++ source: read and describe. Quote at most a few lines.
- No AES key, no game asset and no copied mod file goes into git, notes, commits or chat.

## Open questions
- Which mods still work on game version 0.8.111? (Answered only by a later in-game test.)
- Is there a license for each mod that allows study and reuse of ideas or code? Answer: no mod gives a license (RE-UE4SS itself is MIT). We use ideas and facts only.
- Does any mod already solve M2 (normal buildings inside the manor) or P3 (refugees)? Answer: no mod solves M2; two lift the one-Keep limit by data. RefugeesExpanded gives a P3 lead (`growPopulation` on day 1 of a month). Both need a game test.

## Acceptance criteria
- [x] `inventory.md` lists all 15 mods with type, files, target version and license text (or "none given").
- [x] Each mod has a note with the five answers above. Binary files have size and SHA-256.
- [x] `summary.md` maps findings to spec 10 and spec 12 criteria and lists follow-up spikes, each with the claim that needs a game test.
- [x] Claims that change a decision are checked against the jmap or earlier notes, and the check is written down.
- [x] Nothing from the downloads was run, installed or copied into the repo.
