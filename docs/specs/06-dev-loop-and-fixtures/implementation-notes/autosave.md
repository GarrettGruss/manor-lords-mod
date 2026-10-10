# Autosave protection (spec 06 and 07 risk)

Date: 2026-10-10. Goal: the game's own autosave must not write into the user's REAL save folder during a run.
Evidence: jmap search, reads in the real game, runs `autosave-1` (scenario `autosave-protection`) and `final-smoke`.

## What the game has (jmap `ManorLords-5.5.4-...jmap`)

| Name | Type | Meaning |
|---|---|---|
| `MLGameInstance.Settings.autosavePeriod` | float in a struct `RTSSettings` (offset 144) | stored period in seconds. Read in the real game: **600** |
| `MLGameInstance:SetAutosavePeriod(autosavePeriod: float)` | native, BlueprintCallable | not called (see below) |
| `MLGameInstance:SetAutosavePeriodOnPawn(newAutosavePeriod: float) -> bool` | BlueprintEvent (`BP_MLGameInstance_C`) | casts the player pawn and calls its `Set Autosave Timer` |
| `MyPawnCPP_BP3_C:Set Autosave Timer(Time: double)` | BP function | (re)starts the pawn timer with `K2_SetTimer` |
| `MyPawnCPP_BP3_C.autosaveHandle` | `TimerHandle` struct (offset 6504) | the timer. Read: `Handle` = 503316508 at first |
| `MyPawnCPP_BP3_C:Request Autosave` | BP function | the function the timer calls. **Never call it** (CLAUDE.md) |

There is no autosave property on the pawn other than the handle. The class `RTSSettings` has no live object (`objects` finds 0): the settings are the struct `MLGameInstance.Settings`.
Reading `Settings` through the bridge worked (the whole struct, `lang_txt` "en_US", `autosavePeriod` 600).

## The timer counts real time, also while the game is paused

Read with `KismetSystemLibrary:K2_GetTimerRemainingTimeHandle(pawn, autosaveHandle)` (it needs object and struct arguments, so it runs in the Lua mod, not through the bridge).
In the paused game after boot: 415.2 s, then 407.0 s, then 398.7 s over about 17 s of wall time. So the clock pause does **not** stop it.
Without protection the first autosave fires about 10 minutes after the load, also in a paused game that stays open (for example with `--keep-open`).
I did not wait for it and did not force it. The claim "an autosave writes into the REAL folder with a private LOCALAPPDATA" is not re-verified here:
it follows from `IoHandler` using the real folder (spec 07 catalog: `requestSaveFile` overwrote `saveGame_9`). The user's real `autosave.sav` is dated 2026-10-08 and did not change in any run.

## The safe way (implemented and verified)

`MLGameInstance:SetAutosavePeriodOnPawn(31536000)` (one year in seconds) restarts the pawn timer far in the future.

What was checked in the real game (call from the Lua mod `HarnessActions`, command `disable_autosave`, run `keepopen-2`):

| Check | Value |
|---|---|
| Timer before the call | handle 503316508, remaining 391.5 s |
| Call result | `true` |
| Timer after the call | handle 5385486358, remaining 31,535,608 s, `timer_exists` true |
| `Settings.autosavePeriod` after | still 600 (the call changes only the timer, nothing is stored) |
| User save folder: 204 files, SHA-1 before and after | identical. `autosave.sav` mtime unchanged (2026-10-08) |
| Run `autosave-1`, scenario `autosave-protection` (HarnessBoot made the call before READY) | at READY: remaining 31,535,386 s. After 60 running game seconds (speed 1x, `ctx.time.run_game_seconds(60)`): same handle 4680843538, remaining 31,535,320 s (counted down by 66 s) |
| Launcher guard of `autosave-1` and `final-smoke` | "the user's save files did not change" |

Mod code: shared module `mod/shared/HarnessAutosave/HarnessAutosave.lua` (`status`, `disable`, `is_disabled`).
`HarnessBoot` has a new state `DISABLING_AUTOSAVE` between `WAITING_FOR_READY` and `PAUSING`. It retries for 30 s, then fails the boot with a clear reason.
It also fails the boot if the timer is not at least 1,000,000 s away afterwards (`autosave timer was not pushed away`).
Log line: `autosave disabled: timer remaining 600.0 s -> 31535400.0 s (settings period 600.0 s)`.
`HarnessActions` (version 3) has the commands `autosave_status` (read only) and `disable_autosave`. `ctx.actions.autosave_status()` reads it from a scenario.

Tests: `boot_state_machine.py` (7 modes; the new mode `autosavefails`: the call answers true but the timer stays, so the boot fails),
`test_fakegame_harnessautosave.py` (5 tests), the scenario `autosave-protection` in the real game.

## Not done and not verified

- `MLGameInstance:SetAutosavePeriod` (the native function) was **not called**. It may store the setting in `rtsSettings.sav` in the real save folder. `SetAutosavePeriodOnPawn` does the job without it.
- The timer may be reset when the game creates a new pawn (a second load in the same run). The boot step runs once per boot. A scenario that loads another save must call `disable_autosave` again.
- The 60 s check shows the timer stays far away. It does not show that no other code path starts an autosave (for example a menu action). A long run (over 10 minutes) was not made on purpose.
- The effect of an autosave (writing the real folder) was not observed, by design.
