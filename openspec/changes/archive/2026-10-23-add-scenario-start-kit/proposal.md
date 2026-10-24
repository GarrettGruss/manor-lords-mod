# Proposal: add-scenario-start-kit

Issue: #425

## Why

Owner design (2026-10-23): the scenario "The Hussites Are Coming" starts the player with 10 villagers and 300 silver. The player can later buy arms (30 large shields and 30 spears) with a button on the liege screen.

## What changes

- `scenario_settings`: when the player clicks "Begin the game" (or the settings are applied by command) in a new game, the mod gives the kit once: 10 villagers and 300 silver (player pawn property `silver`). It is never given for a loaded save. ModState records that the kit was given.
- `liege_influence`: the liege screen gets a button "Request arms shipment". It costs 200 silver and delivers 30 large shields and 30 spears to the manor store at once. It has a cooldown of 180 game days. It is disabled with a reason when silver is below 200 or during the cooldown (days left shown). Silver is taken only when the delivery succeeds. The cooldown day is saved in ModState.
- All amounts are config values. The shields and spears are no longer part of the start kit.

## Open questions (proposed defaults)

1. "10 villagers": default is 10 people, the count in the top bar. It replaces the game's start population.
2. Starting Supplies setting of the game: the kit does not override it. The 300 silver replaces the start silver (the pawn property is set to 300).
3. How are goods put into the manor store? Not known (spike 1.3). `GiveItemByID` fills the region stock. Fallback: a pile at the manor.
4. Item ids: logs 16, planks 17, berries 171, bread 172 are known. The ids of the large shield and the spear are NOT known yet (spike 1.1).
5. The villager call is not known yet (spike 1.2).

## Impact

- Specs: `mod/scenario_settings` (ADDED), `mod/liege_influence` (ADDED).
- Code: `scenario_settings` and `liege_influence` features and their config.
- Tests: fake game tests and two real test scenarios, with pictures of the button.
