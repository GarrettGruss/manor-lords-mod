## Why

Issue: #315 (bug #311).

`HarnessBoot` pushes the autosave timer one year away before `READY`. A world load restarts the game's 10 minute timer. In run `qs-autosave-1` (`--keep-open`), the owner loaded a save, and the game made a real autosave about 580 s later into the user's REAL save folder. The boot protection covers only the first world.

## What Changes

- The harness pushes the autosave timer away again after every world load in the same game session, with the same call as at boot (`MLGameInstance:SetAutosavePeriodOnPawn`).
- It logs each push, and it logs an error when the push fails after a load. A failure after `READY` does not stop the game, because the boot state machine has ended.
- The HarnessActions command `disable_autosave` stays as the manual fallback.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `harness/game-boot`: the autosave requirement covers every world load, not only the boot.

## Impact

- `mod/shared/HarnessAutosave/HarnessAutosave.lua`, `mod/HarnessBoot` (the load hook), fake game tests.
- No save function is called. `test_save_call_sites.py` stays green.
