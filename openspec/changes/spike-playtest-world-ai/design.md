## Method

- Fixture: `playtest-noai` (`notes/fixture.md`). Load it with the harness fixture option. The base fixture is the control for question 3.
- Question 1: with the bridge, find the bandit pawn and faction actors, and read their state with camps 0. Then try the camp spawn path (`HarnessEncampment`, `HarnessBandits`), a bandit squad spawn, and creation of the bandit pawn. Check that `HarnessBattle` can own squads after that.
- Question 2: list AI lord pawns. Try to assign a region to an AI pawn (`region.ownerPawn`, the game's claim function). If no AI lord exists, try to spawn or enable one. Watch construction sites over 10 to 20 game days (fast speed). Use `vassals_adopt` and `notes/rebuild-order.md` of `add-vassal-sack-wipe` as the prior state.
- Question 3: run the existing test scenarios of `mod/InvasionMod/scenarios/invasion/` and `raid_behavior/` on the fixture. Force a raid with `invasion_plan_now`. Compare the numbers with the base fixture. Use ranges, not exact values.
- One note per question: `notes/bandit-camps.md`, `notes/ai-lord-construction.md`, `notes/hussite-raid.md`.

## Safety

- Never save. Never call a save function (`CLAUDE.md` Safety). Use `save_game` only if the owner asks.
- Back up `%LOCALAPPDATA%\ManorLords\Saved\SaveGames` before each run and check it after.
- Read `DANGEROUS_ACTIONS.md` before a probe. Do not write `Tags` arrays or pass Lua strings to FName arguments.
- Use one bridge client at a time. Single-player only. Cap the number of iterations.
- Do not change the real save files. The fixture copy is read only.
- Do not run the game while the owner plays.

## Decisions

The owner decides at the end which settings the mod requires. Open: what the mod does when a needed game actor (bandit pawn, AI lord) is missing.
