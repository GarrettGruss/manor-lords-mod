# M02 iteration 06: great-raid-waves

Branch: `feat/M02-invasion-06-great-raid-waves`. Issue: #186. Stacked on PR #185 (iteration 03).

## Goal
When the great raid clock ends (iteration 02), the great raid runs: `difficulty` waves (decision 12), every wave large (15 squads, decision 16), then the relief army of the liege (15 squads at difficulty 1, 8 at 2, 0 at 3; decisions 26 and 28) under the control of the player, then the very large final battle (win condition, decision 1). The final battle is not scaled by difficulty. The loss of the final battle is TBD (decision 27): not implemented.

## Changes
- `great_raid.lua` (pure): phases (`clock`, `waves`, `final`, `won`) and `next_action` (when to spawn the next wave, when the relief army comes), `relief_templates`.
- `relief.lua`: `spawnArmy` with the player pawn as owner (side player).
- `invasion/init.lua`: ModState keys `gr_phase`, `gr_wave`, `gr_last_day`, `gr_seed`. A daily step runs the phases:
  1. The clock is due: wave 1 spawns (15 squads, kind `great`, the lord army of M03.02, no plunder, no leave).
  2. Each next wave comes `wave_gap_days` after the last one (TBD 10 days).
  3. `relief_delay_days` after the last wave (TBD 10 days): the relief army (`relief_squads(difficulty)` squads, player side) and the final army (`final_squads`, TBD 25, a fixed tier mix, hostile) spawn.
  4. When the final army is dead (tracker of `raid_behavior`), the phase is `won`: banner and log `INVASION great raid won`.
- Config `invasion.great_raid`: `wave_squads` 15, `wave_gap_days`, `relief_delay_days`, `final_squads`, `final_tier_difficulty`, `relief_templates`, `relief_offset`.
- `raid_behavior`: a `great` raid has no plunder and no leave (same as subjugation).
- Commands: `invasion_great_state`, `invasion_great_force_start` (clock ends now), `invasion_great_skip_wait` (the next phase step comes at once).
- Performance: the scenario measures game days per wall second before the waves, with 15 hostile squads, and with 15 + 15 (and the final battle) squads. Crash and frame findings go to `implementation-notes/great-raid-performance.md`.

## Acceptance criteria
- G1: at difficulty d, exactly d waves spawn, each with 15 squads.
- G2: the relief army has 15, 8 or 0 squads at difficulty 1, 2 or 3, and its units are on the player side.
- G3: the final army has the configured squads (not scaled by difficulty).
- G4: the phase becomes `won` after the final army is dead (fake game; the real battle is a probe).
- G5: the game does not crash with 15 + 15 squads on the map (a crash is recorded as a result).

## Scenarios
- Fake game: `GreatRaidTests`, rule tests for `next_action`.
- Real game: `invasion-great-raid-waves` at difficulty 1.

## Result
Done. Fake game: `GreatRaidTests`, `GreatRaidRulesTests` (invasion) and `GreatRaidWinTests` (raid_behavior, the relief army makes no units) pass.
Real game, difficulty 1: scenario `invasion-great-raid-waves` passed twice (runs 20261018-055536-6790 and 20261018-055939-5195). Wave 1 had 15 squads, the relief army 15 squads (spawned=true), the final army 25 squads. No crash with 15 + 15 + 25 squads on the map (G5). The win (G4) is covered in the fake game only: the real battle was not fought.
Speed (game days per wall second at speed 3): baseline 0.097, with 15 squads 0.061 to 0.099, with all squads 0.067 to 0.099. See `implementation-notes/great-raid-performance.md`.
Fix on the way: a partial spawn of a wave or the final army counts as spawned and is not retried (no double army). `raid_behavior/world.lua` ignores a non-number `ItemsLooted`.
TBD values kept: `wave_gap_days` 10, `relief_delay_days` 10, `final_squads` 25.
