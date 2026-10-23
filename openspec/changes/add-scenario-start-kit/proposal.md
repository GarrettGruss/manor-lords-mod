# Proposal: add-scenario-start-kit

Issue: #425

## Why

Owner design (2026-10-23): the scenario "The Hussites Are Coming" starts the player with a small kit: 10 villagers, 30 large shields and 30 spears. The kit helps the player prepare for the first raid.

## What changes

- When the player clicks "Begin the game" (or the settings are applied by command) in a new game, the feature `scenario_settings` gives the kit once.
- The kit is never given for a loaded save. ModState records that the kit was given, so it is given only once.
- The goods come with `MLCheatManager:GiveItemByID` (known in the harness: `HarnessLoot`, `harness/runlib/actions.py`). The villagers come with a family call that is still to be found (spike task 1.2).
- The kit amounts are config values, not fixed numbers in code.

## Open questions (proposed defaults)

1. What does "10 villagers" mean? Default: 10 people, the count shown in the top bar. The kit sets the start population to 10; it does not add 10 to the game's start population.
2. Does the kit override the game's Starting Supplies setting? Default: no. The kit is added on top of it.
3. Where do the goods go? Default: the stock of the player region (as `GiveItemByID` does), so they are in the storehouse or the manor store. If no store exists at the start, spike task 1.3 finds out where they go. The fallback is a pile at the manor.
4. Item ids: logs 16, planks 17, berries 171, bread 172 are known. The ids of the large shield and the spear are NOT known yet (spike task 1.1).

## Impact

- Spec: `mod/scenario_settings` (one ADDED requirement).
- Code: `mod/InvasionMod/Scripts/features/scenario_settings/` and its config.
- Tests: fake game test and one real test scenario.
