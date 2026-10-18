# M02 iteration 04: difficulty

Branch: `feat/M02-invasion-04-difficulty`. Issue: #175.

## Goal
The player picks the difficulty (1 to 3) at the start (decision 11). Everything that scales reads it, and scaling rounds up (decision 28).

## Changes
- New file `Scripts/features/invasion/difficulty.lua` (pure rules): `valid`, `scale_up(base, difficulty, max_difficulty)` (ceiling), `relief_squads(difficulty)` (15 at 1, 8 at 2, 0 at 3), `wave_count(difficulty)`.
- ModState key `difficulty_chosen` (0 or 1). The value `difficulty` already exists (iteration 01) and is read by raid size (M02) and the Public Order debuff (M04).
- Start prompt: until a pick is made, the mod shows a banner every `prompt_every_days` game days: "Pick difficulty 1 to 3". The config default is used until then. The menu comes with the widget (iteration 05).
- Named command `invasion_pick_difficulty` (value 1 to 3): sets the difficulty and `difficulty_chosen`. It is refused after the first pick and after the first raid spawned. `invasion_set_difficulty` stays for tests.
- `invasion_state` and `invasion_clock_state` neighbours: new command `invasion_difficulty_state` returns difficulty, chosen, relief squads, wave count.

## Acceptance criteria
- D1: before a pick, `difficulty_chosen` = 0 and the config default is in use; a prompt banner is logged (`INVASION difficulty prompt`).
- D2: after a pick of 1, 2 or 3, `difficulty` equals the pick, `difficulty_chosen` = 1, a second pick is refused.
- D3: planned squads equal multiplier x difficulty after the pick; relief squads are 15, 8, 0; waves are 1, 2, 3.
- D4: the Public Order debuff of M04 uses the picked value (state of `bandits_state` shows the difficulty).

## Scenarios
- Fake game tests (D1 to D3).
- `scenarios/invasion/difficulty_pick.py` (D1 to D4).

## Result
PASS in the real game (2026-10-18). Scenario `invasion-difficulty-pick`, difficulty 2 run `20261018-051059-708f`, difficulty 3 run `20261018-051215-fb86`: D1 to D4 pass. Fake game `DifficultyTests` pass. The pick is a named command; the menu and a start screen come with the widget (iteration 05). Scaling helpers in `difficulty.lua` round up; the relief army and wave count are ready for iteration 06.
