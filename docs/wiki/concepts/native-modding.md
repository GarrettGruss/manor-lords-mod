---
type: Concept
title: Native modding and why the harness does not use it
description: How native C++ mods for Manor Lords reach game code that reflection does not list (reflection dumps, Ghidra, MinHook hooks, build guards), what it costs on each game update, how the cost can be reduced, the project decision to stay with reflection and paks, and the facts taken from one native mod.
tags: [engine, native, reflection, ghidra, hooks, decision]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-25T00:00:00Z }
sources:
  - resource: https://github.com/Maxhem2/manor-lords-fixes
  - resource: repo://openspec/changes/archive/2026-10-25-spike-squad-raid-skill/
  - resource: repo://openspec/changes/archive/2026-10-25-spike-raid-skill-near-enemy/
  - resource: repo://docs/wiki/concepts/engine-limits.md
---
# Native modding and why the harness does not use it

The harness and the Invasion Mod reach the game only through UE4SS reflection (Lua) and paks. This page explains the other route, native C++ mods, so that a reader can judge facts that come from such mods. The example is AI Tweaks 0.7.1 for game build 0.8.117 (`Maxhem2/manor-lords-fixes`, MIT). It was reviewed read-only on 2026-10-25. Its code was not built or run.

## Reflection and native code

- The game is C++ compiled to x64 machine code. It is not bytecode. No interpreter runs it.
- At compile time, Unreal's header tool writes reflection tables for every `UFUNCTION` and `UPROPERTY`. At startup the game builds `UClass` and `UFunction` objects from them. Each `UFunction` points to its native code.
- UE4SS reads these objects. That is why Lua can call `addMilitiaSquad` or read `fieldOperationMode` by name.
- C++ code that the developers did not mark has no reflection entry. Lua cannot call it. An example is the native choice of raid target buildings.

## How a native mod reaches unlisted code

1. **Field offsets** come from a reflection dump (for example a UE4SS header dump). A diff of two dumps shows how offsets moved between builds. AI Tweaks keeps this diff in `docs/reflected-offset-changes.json`.
2. **Native functions** have no names in the executable. The author decompiles the executable with Ghidra and identifies functions. A common start is a reflected `UFunction`: its small wrapper (thunk) calls the real native function. The author then follows calls and known field offsets.
3. **Loading:** a UE4SS Lua script calls `package.loadlib` on the mod DLL. The DLL now runs inside the game process.
4. **Guards:** the DLL checks the SHA-256 hash of the executable and the first 16 bytes of each target function. If any of them differ, it installs no hook.
5. **Hooks:** MinHook copies the first instructions of a function to a trampoline and writes a jump to the mod's function in their place. This happens in memory only. The game files on disk do not change.
6. **Calls and reads by address:** the mod calls a native function at module base plus a fixed offset, and reads fields at object address plus a fixed offset. No names are involved.

## The cost

- Every game build moves functions and fields. Each address and offset must be mapped again, and the logic checked again. AI Tweaks matches old functions to new ones by instruction patterns (`docs/native-map-0.8.111-to-0.8.117.json`), but some entries still need a manual check.
- Until the port is done, the mod is off on the new build. The hash guard enforces this.
- A wrong offset does not fail cleanly. It reads garbage or corrupts memory. AI Tweaks wraps each feature in an exception handler and turns the feature off after one fault.
- The build tooling is Windows C++ only.

A reflection name usually stays the same between builds. When it changes, Lua logs a clear error. For the harness, a game update mostly means a run of the test suite.

## Ways to reduce the cost

- **Signature scanning:** at startup, search the executable for a unique byte pattern of the function instead of using a fixed address. It survives most small updates. When the function itself changes, the scan finds nothing and the feature turns off. A person then updates the pattern.
- **A custom `UFunction`:** a native mod can create a `UFunction` at run time whose native pointer is its own code. Lua and Blueprints can then call it by name. This gives a stable name only. The native code behind it still needs the address or the signature scan.
- **Blueprint classes in a pak** add new reflected classes, but they can only call functions that are already reflected. They do not reach unlisted native code.

## Decision

The harness and the Invasion Mod use reflection and paks only, with named commands (CONTRIBUTING.md, Design rules). A native layer (DLL, hooks, signature scans) would be a new architecture decision for the owner. It pays off only for a feature that cannot be done any other way. As of 2026-10-25 no such decision exists.

## Facts taken from AI Tweaks

| Fact | Status |
|---|---|
| Squad skill 19 is the native raid skill. A native `SquadComponent` function toggles it with (squad, skill, enable, flag). | The toggle is reflected as `SquadComponent:SetSkillActive` (change `spike-squad-raid-skill`). With the skill on, the squad walks into the enemy village and stops, but no raid starts, also 55 units from a built enemy building at war (change `spike-raid-skill-near-enemy`). |
| AI Tweaks makes a squad raid one exact building. It hooks the native "buildings of region" accessor during the raid task. | Native only. Lua cannot do it. |
| The reflected `rallied` bool is not updated by the rally path in 0.8.117. Rallied men show up in the squad's unit array instead. | Not checked. |
| Native militia limit per region: about 1 squad per 36 people, plus 1 when 12 or more are left over, at least 1. Native recruitment stops at the first settled region. | Not checked. |
| `addMilitiaSquad` (reflected) is a thin thunk to the native roster call. | Matches change `spike-militia-weapon-rebellion`, where the reflected call registered militia. |
| Saved raid skills stay set after a load. AI Tweaks clears them on load. | Not checked. |
