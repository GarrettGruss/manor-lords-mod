# M01 iteration 01: tags-module

Branch: `feat/M01-mod_state-01-tags-module`. Issue: `Mod M01.01: tags-module` #142.

## Goal
Build the `ModState` shared module for the pawn Tags, as designed in spec 24. Prove it in the real game with a harness save and a load.

## Changes
- Add the shared module `ModState` (path per spec 22) with `open`, `register`, `get`, `set`, `flush` and the version entry.
- Call `open` on `ReceiveBeginPlay` of the player pawn.
- Add a named command `mod_state_dump` to `HarnessCommands`. It returns all registered keys and values. The scenarios use it.
- Fake-game unit tests: parse, default, typo in a key (fails loudly), flush.

## Acceptance criteria
- A1: after `set` and `flush`, the live pawn Tags hold exactly one entry per key (no duplicates) with the new value.
- A2: after a harness save (`save_game`) and a load in a new run, `mod_state_dump` returns the same values for 3 keys (integer, boolean, string).
- A3: two saves with two different values keep two different values (no mixing).
- A4: a load of the `base` fixture (no mod marker) gives all defaults and no error in the log.
- A5: a key that was not registered makes `get` and `set` fail with a clear message.
- A6: Tags that do not start with the mod prefix are the same before and after a flush.

## Scenarios to write
- `scenarios/mod_state/roundtrip.py`: set 3 values, `save_game`, load the slot, assert A2.
- `scenarios/mod_state/two_saves.py`: A3.
- `scenarios/mod_state/default_load.py`: A4 and A6.

## Result
Result: done (2026-10-16). A1 to A6 pass in the real game. Details and run ids: `../implementation-notes/tags-module.md`.
- Module `mod/shared/ModState/ModState.lua`. Feature `mod/InvasionMod/Scripts/features/mod_state/`. Commands `InvasionMod.mod_state_dump`, `mod_state_get`, `mod_state_set`, `mod_state_add_foreign_tag` (test only).
- A1, A4, A5, A6: `mod-state-default-load`. A2: `mod-state-roundtrip`, 3 of 3. A3: `mod-state-two-saves`.
- A Tag is never removed. A changed key is overwritten in place.
- The load waits for the new pawn: at `ReceiveBeginPlay` the engine has no new pawn yet.
- 22 fake-game tests in `harness/tests/test_fakegame_modstate.py`.
