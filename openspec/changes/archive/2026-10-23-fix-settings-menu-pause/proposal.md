## Why

Issue: #418. The owner asks: when the game starts and the mod menu is open, the game shall be paused. In a normal Steam launch (no harness, no autoboot) the game is not paused. The living spec already says the mod keeps the game paused until "Begin the game", but the tests only cover harness runs. There, HarnessBoot waits for the intro cinematic to end and then calls `pauseGame`. In a player launch the cinematic plays. The mod calls `pauseGame` when the menu opens, probably during the cinematic. The game probably un-pauses or sets the speed at the end of the cinematic. The live `mod.log` of the owner shows "game is new" and, 24 s later, "settings applied", with no "not paused" warning.

## What Changes

- The game stays paused for the whole time the menu is open in a new game, also during and after the intro cinematic, and also without the harness.
- The mod re-applies the pause if the game clock moves while the menu is open.
- A new spec scenario, "A player launch without the harness", and a test scenario and a fake-game test for it.
- The cause is confirmed first with a real run without the HarnessBoot pause.

## Impact

- Spec: `mod/scenario_settings`, requirement "The settings menu opens when a new game starts" (MODIFIED).
- Code: `mod/InvasionMod/Scripts/features/scenario_settings/init.lua`.
- Tests: `harness/tests/test_fakegame_scenario_settings.py` and a new test scenario.
