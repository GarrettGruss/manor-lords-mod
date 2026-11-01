# The vassal warning is removed (owner decision 2026-11-01)

The spike of change `spike-vassals-without-ai-opponents` (PR #544, issue #543) showed that vassals work with AI opponents 0. So the warning "vassals are not enabled" and the check behind it are removed:
- the mod state key `vassals` (read from the game setup, or by the live check of `PawnCPP_AI` pawns);
- `rules.vassals_from_setup`, `rules.vassals_from_lord_count`, `rules.background_with_warning`;
- `config.scenario_settings.vassals_warning`;
- the fields `vassals` and `warning` of the command `scenario_settings_state`;
- the fake-game test file `test_fakegame_game_settings_guard.py` and the test scenario `scenario-settings-game-settings-guard` (the "locks nothing" checks moved to `test_fakegame_scenario_settings.py`, class `NoVassalsGuardTests`).
`HarnessGameSetup` stays (other code may use it). An old save that stored `vassals` keeps an unused key; it does no harm.
