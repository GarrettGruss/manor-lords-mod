# Spec 07: Feature test kit (actions for scenarios)

Status: built and checked in the real game (2026-10-10). Roadmap phase: 9 (see `openspec/changes/archive/2026-10-15-legacy-00-harness-overview/README.md`).

## Goal
A scenario can create the situation that a mod feature needs, and observe the result. The kit gives named actions
(give silver, change the season, spawn raiders, set a region value) that are verified to work in the real game.
Each action has a checked effect, so the agent knows it did what it said.

## Non-goals
- Actions that need mouse input, such as placing a building by clicking. If no function exists for a UI action, the kit says so and a save fixture (spec 06) is the way.
- Balance decisions about the game.

## Background
- The bridge can read and set properties and call UFunctions (spec 01). Limits: no object-reference or out parameters. `eval_lua` is off.
- Candidates from the jmap (`openspec/changes/archive/2026-10-15-legacy-02-save-autoload/implementation-notes/jmap-findings.md`):
  `PawnCPP:ChangeTreasury`, `changeSilver`, `changeInfluence`; `RTSMultiEngineCPP:setDay`, `setGameSpeed`; `TemporalComponent:setWeatherSpeed`;
  `MLCheatManager` exec functions (`GiveItemByName`, `SpawnBanditSquad`, `SpawnRaidersOfType`, `RainNow`, `SetSettlementLevel`, `RemoveAllFamilies`, `CollapseAllBuildings`, `MaintainAllBuildings`) that need a CheatManager instance;
  `PawnCPP:requestSaveFile(slot, name)` to save a state as a new fixture.
- A mod can act inside the game with Lua (full UObject access), so an action can be a small helper mod when the bridge cannot do it.
- Writes change the game state. They must be undone or isolated: each run starts from a fixed save, so state does not leak between runs.

## Design

### The action catalog
A file `harness/runlib/actions.py` (exposed as `ctx.actions`) with one function per action, each with:
- a precondition check (for example, the game is loaded),
- the call,
- a postcondition check that reads the state back (the effect), and
- a result record `{"action", "ok", "before", "after"}` that goes into the scenario result.
`openspec/changes/archive/2026-10-15-legacy-07-feature-test-kit/implementation-notes/actions-catalog.md` lists each action with its status: `verified` (checked in the game), `partial`, or `not possible` (with the reason).

First actions to try (the agent decides the final list after probing):
1. `set_silver(n)` and `add_silver(n)`.
2. `set_influence(n)` (if a setter exists), `set_region_value(region, name, value)` for plain numeric properties (`Approval`, `regionalWealth`, `supplies_food`).
3. `give_item(name, amount)` through the cheat manager, if an instance can be found or created.
4. `set_season(name)` or `set_day(n)`.
5. `spawn_raiders(...)` and `trigger_event(...)`, if reflected functions exist.
6. `send_letter(...)` or read the `InBox` and `outbox` (letters between lords).
7. `save_state(slot_name)` to make a new fixture from the current game (with the spec 06 fixture tools).

### Probing method
For each candidate: find the function in the jmap, call it through the bridge on a loaded game, read the state before and after, and record the result in the catalog.
If a function crashes the game, record that and mark it `not possible`. Treat each probe as a run that may need a restart.

### Helper mod
If the bridge cannot do an action (object-reference parameters, for example), add a Lua helper mod `HarnessActions` with a small command channel:
the bridge or the scenario writes a command file `<run>/commands/<id>.json`, the mod runs it on the game thread, and writes `<run>/commands/<id>.result.json`.
Same rules as the bridge: atomic writes, unique ids, time limits, no `eval`, a fixed list of allowed commands.

Built as written, with one change: UE4SS Lua cannot list a folder, so the ids are the numbers `0001`, `0002`, ... in order, and the mod waits for the next number.
The commands are `ping` and `send_letter`. The client is `harness/runlib/commands.py`.

## Plan
1. Probe the candidate actions in the real game (a probe script, not production code). Write the catalog with real results.
2. Build `actions.py` for the verified actions, with unit tests on the checking logic (no game).
3. If needed, build `HarnessActions` with a mock test and a real test.
4. Write two example scenarios that use actions: `silver-change` (add silver, check the player value and the HUD value) and one that sets a situation and watches it over game days.
5. Run each scenario 3 times with the launcher.
6. Update the spec, the README and the roadmap.

## Open questions
- Is there a `MLCheatManager` instance in the shipping build, or can one be created?
- Do setters on properties like `Approval` hold, or does the game overwrite them at the next tick?
- Is there a reflected function that places a building or starts a raid?

## Acceptance criteria
- The catalog lists at least 6 actions with a clear status, and each `verified` action has before and after values from the real game.
- `actions.py` has unit tests for the checking logic.
- Two scenarios use actions and pass 3 times in a row with the launcher.
- A scenario that uses a `not possible` action fails with a clear message, not a crash.

## Result (2026-10-10)

Details and numbers: `implementation-notes/actions-catalog.md`.

- Probed in the real game in 18 probe runs (4 ended in a game crash, which the launcher recorded as a result). 14 actions are `verified` or `partial` and are in `actions.py`; 5 are `not possible` with a reason (`ctx.actions.<name>` raises `ActionNotPossible`).
- The cheat manager exists because the stock mod `CheatManagerEnablerMod` is on. The kit depends on that mod.
- Setters hold for silver, influence, wealth and the date. `Approval` and `supplies_food` are recalculated by the game within one to three game days. Weather values move back in seconds.
- `requestSaveFile` writes into the user's real save folder, even with a private `LOCALAPPDATA`. In the probe it overwrote the user's old slot `saveGame_9`. `save_state` was `not possible`; spec 24 replaced it with the guarded `save_game`. The run guard caught it.
- The helper mod `HarnessActions` was needed for `send_letter` (object parameter). Plain strings as `FName` values crashed the game; `FName(name)` works.
- Scenarios: `silver-change`, `winter-region`, `letter-delivery` (3 passes in a row each), and the hidden `selftest-action` (fails with a clear message, run once). The hidden `probe-actions` is the probe.
- Unit tests: `harness/tests/test_runlib_actions.py` (45 tests), `harness/tests/test_fakegame_harnessactions.py` (12 tests, lupa).

### Open
- The look of the world after `set_season` (trees, snow) was not checked, only the calendar.
- When exactly the game recalculates `Approval` is not known.
- `spawnRaiders`, `spawnBanditCamp`, `RemoveAllFamilies` and the on-screen letter banner were not verified.
- Actions assume a paused game. A running game changes silver and stock by itself.

### Acceptance
- Catalog with at least 6 actions with a clear status and before/after values: done (14 usable, 5 not possible).
- Unit tests for the checking logic: done.
- Two scenarios (and a third for the helper mod) pass 3 times in a row: done.
- A scenario with a `not possible` action fails with a clear message: done (`selftest-action`).
