# Spec 26: Game start and victory settings (spike)

Status: A1, A2, A3 met (2026-10-16): writing goals = Endless (2) on MLGameInstance stops the victory on a claim, 3 of 3. Note `claim-victory-test.md`. Issue: #130. Branch: `feat/26-game-start-settings`.
Needed by: the Invasion Mod (M00 feasibility decision 6 and open question 2).

## Goal
Find out how the game sets its scenario settings at the start of a game (start type, victory condition, difficulty and similar), and whether Lua can read and change them.
Two uses for the mod:
1. Stop the victory cinematic that a region claim can trigger. A claim of region Eichenhau ended a start with the victory cinematic (spec 15 `settler-camp.md`). The mod needs claims for vassals.
2. A "plundered village" start (ruins, a small and scared population, low supplies), if the start settings allow it.

## Known
- A region claim met the victory condition of that start and showed the victory cinematic (`settler-camp.md` line 10).
- The game has a WIP domination victory screen that is not used (spec 12 `unused-assets.md`).
- Sacks and fire work at run time (spec 10 S6), so a plundered start can at least be made after the start.

## Questions
- Q1: Where are the start settings stored (game instance, a settings object, a data table, the save)? Which fields hold the victory condition?
- Q2: Can Lua change the victory condition after the game started, and does the game then not trigger the cinematic on a claim?
- Q3: Is there a start type with no victory condition (a "sandbox" or endless setting)? Does the mod need only to pick it?
- Q4: Which function triggers the victory, and can a hook see it before the cinematic? (Observe only first.)
- Q5: Can the start state be changed at the start (ruins, population, supplies) through settings, or only by Lua after the start?

## Plan
1. Static: search the jmap and the data tables for victory, scenario, start, game mode, difficulty and settings classes and fields. Read the new-game menu flow. Write `implementation-notes/start-settings.md`.
2. Live read (bridge, existing fixture): read the settings objects in a running game, for each fixture with a different start type if there are several.
3. Test: change the victory field with Lua, then claim a region (as in spec 15) and check that no cinematic plays. Use a fixture save; no save call.
4. Plundered start: list which start fields change ruins, population and supplies. If none, write the Lua fallback (sack and fire in the first days).

## Acceptance criteria
- A1: `implementation-notes/start-settings.md` names the settings objects and the victory fields, with evidence.
- A2: One run shows a region claim with no victory cinematic after a Lua change, or the spec says why it is not possible and gives the next option.
- A3: A statement for the plundered start: settings, Lua after the start, or not possible.

## Non-goals
- No new game mode menu in this spike.
- No change to the user's game settings files.
