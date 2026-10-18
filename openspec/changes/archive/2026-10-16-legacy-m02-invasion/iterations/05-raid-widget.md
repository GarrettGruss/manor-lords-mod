# M02 iteration 05: raid-widget

Branch: `feat/M02-invasion-05-raid-widget`. Issue: #189. Stacked on PR #188 (iteration 06).

## Goal
One custom menu for all raid information (decision 4): countdown to the next raid, size estimate, great raid clock, difficulty and terms. The player can pick the difficulty in it.

## Changes
- Pak `raidmenu_P.pak` (`mod/InvasionMod/paks/`): a cooked Widget Blueprint `/Game/HarnessMod/WBP_RaidMenu`, made by `mod/InvasionMod/ue/make_raid_widget.py` (same method as spec 16, `PolicyMenu`). A dark panel with a title, 5 text lines (`RaidLine0..4`) and 3 buttons (`DifficultyButton0..2`).
- Feature `raid_widget` (requires `invasion`): `lines.lua` (pure text rules), `init.lua` (load the class with the asset registry, fill the texts, poll the buttons through `scheduler.lua`, key F8 toggles). No LoopAsync.
- `invasion` exports `raid_info()` and `pick_difficulty(value)` (the named command uses the same function). `sack_and_terms/terms.lua` exports `summary()`.
- Commands `raid_widget_open`, `raid_widget_close`, `raid_widget_state`. Config `raid_widget`.
- The buttons show only while a pick is allowed (not picked and no raid spawned yet).
- `mod.json` names the pak.

## Acceptance criteria
- W1: the widget opens and is in the viewport.
- W2: the five lines equal the values of the mod state (next raid days, size estimate, great raid clock, difficulty, terms).
- W3: a real mouse click on a difficulty button picks that difficulty (`difficulty_chosen` true, the difficulty line changes).
- W4: F8 closes and opens the widget.

## Scenarios
- Fake game: `test_fakegame_raid_widget.py` (text rules, information table, missing pak message).
- Real game: `invasion-raid-widget --pak raidmenu`.

## Result
PASS in the real game (2026-10-18), runs 20261018-062226-4322 and 20261018-062450-e3c3. W1 to W4 pass. The button was found by hover at (0.340, 0.740) of the window in both runs; the click picked difficulty 1. Screenshots in the run folders (git-ignored).
Open: the widget has no terms buttons (accept or decline stay named commands) and no start screen: it opens with F8. The pick button is plain grey (no art). Difficulty 3 or 2 were not clicked (the same code path, value from the button index).
