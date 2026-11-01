# Vassals with AI opponents 0

Answer: yes. The vassal handover works end to end with AI opponents 0, also for two vassals. The guard value `vassals` = 0 and its warning are wrong for this feature.

## Setup
- Fixture `playtest-noai` (AI opponents 0, no raids, no bandit camps), game day 116, 6 free regions.
- Test scenario `mod/InvasionMod/scenarios/vassals/spike_noai_vassals.py` (`vassals-spike-noai`): claim and settle one free region, wait for the handover, claim and settle a second one, watch 20 game days (speed 2), set policy heavy on slot 1, jump the season, read the tribute. It saves nothing.
- The mod ran from this branch (no mod code change).

## Runs
| Run id | Slot | Verdict |
|---|---|---|
| 20261101-154216-67e1 | 1 | pass |
| 20261101-154747-78a3 | 2 | pass |

No crash in either run. The save folder hash is unchanged except `rtsSettings.sav`.

## Results (both runs)
- `scenario_settings_state.vassals` = 0 and the warning text is set (at the start and at the end). Vassals still worked.
- Handover: slot 1 filled with lord Aldric about 16 s after the settle call (game day 117). The region (Eichenhau) owner is an `PawnCPP_AI_*` pawn. Slot 2: lord Bertram, region Goldhof, same way. The registry count is 2.
- Building: 4 buildings at the handover. Run 1: 11 after 5 game days, 14 after 10 and 20. Run 2: 11 after 5, 15 after 10 and 20. This is above `growth_min_buildings` (3) in `growth_check_days` (10). No slot was flagged `stalled`.
- Peace: no war with the player at any look (`war_seen` 0). `peace_calls` = 2 (the mod declared peace once per lord).
- Tribute and policy: after `vassals_set_policy slot=1 heavy` and a season jump, the tribute paid share 0.30 (30 goods) for slot 1 and share 0.20 (20) for slot 2 (fair). The policy works.
- Reader of the key: only `scenario_settings` reads the key `vassals` (the menu text `background_with_warning`, the state command, and the guard decision). The `vassals` feature does not read it. Nothing blocks vassals.
- Number of vassals: two worked. The AI opponent count does not limit the vassals (config `max_vassals` = 3 is the limit). A third was not tried.

## Recommendation (not implemented)
Remove the guard `vassals_from_lord_count` and the warning "vassals are not enabled" for AI opponents 0, or stop writing 0. Update the spec rules `rules.vassals_from_lord_count` in `openspec/specs/mod/scenario_settings/spec.md`. Do it in a new change.

## Not verified
- Fresh new game (not a loaded fixture) with AI opponents 0 and the Hussite template. The fixture is a loaded save.
- A third vassal, and a longer time than 20 game days.
