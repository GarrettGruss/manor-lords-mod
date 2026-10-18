# M02 iteration 03: subjugation-raid

Branch: `feat/M02-invasion-03-subjugation-raid`. Issue: #177. Stacked on PR #176 (iteration 04).

## Goal
The major raid type: a subjugation raid that tries to take a region. Vassals do not exist yet (M07), so the home region is the stand-in target. Vassal targeting is TBD for M07.

## Changes
- New `features/invasion/target.lua` (pure): a plunder raid targets the home region; a subjugation raid targets a vassal region, or the home region as stand-in when there are no vassals (`stand_in = true`). The list of vassals is empty until M07 (TBD).
- `invasion/init.lua`: one subjugation raid is planned when the first raid spawned, 60 to 120 game days later (config `invasion.subjugation`, TBD values), with a warning banner like the first raid. Size class large: squads = 3 x difficulty. Own ModState keys `sub_day`, `sub_warning_day`, `sub_squads`, `sub_seed`, `sub_spawned`. `spawn_raid(today, kind)` is shared with the plunder raid.
- The raid is the lord army of M03.02 (`lord_raid.lua`): an AI lord at war with the player and a challenge whose battlefield is the manor. The lord info carries `kind = "subjugation"`.
- `raid_behavior/rules.lua`: a subjugation raid has no plunder tick and no leave rule (it fights until it is beaten or wins). A region the raid wins is still given back to the player by the M03 check (the loss rule is TBD, decision 27, and M06). The tracker summary shows `kind`.
- Commands: `invasion_subjugation_state`, `invasion_subjugation_force_next` (tests).
- Scenario `invasion-no-double-raid` counts only plunder spawns (the subjugation raid may come inside its 120 days).

## Acceptance criteria
- S1: the subjugation raid is planned 60 to 120 days after the first raid spawn.
- S2: it is large: 3 x difficulty squads.
- S3: the spawn log has `kind=subjugation` and the stand-in target; the tracker shows `kind = subjugation` and a lord raid.
- S4: no plunder and no leave reason in 12 game days.

## Scenarios
- Fake game: `SubjugationTests`, `TargetRulesTests`, `test_a_subjugation_raid_has_no_plunder_and_never_leaves`.
- Real game: `invasion-subjugation-raid` at difficulty 1 and 2.

## Result
PASS in the real game (2026-10-18). `invasion-subjugation-raid`: difficulty 1 run `20261018-052118-5ef3`, difficulty 2 run `20261018-052600-5b3c`, S1 to S4 pass. `invasion-no-double-raid` still passes with the plunder-only filter (run `20261018-053028-f489`). Open: vassal target selection (M07); what the raid does when it takes the region (M06, decision 27); the plan is one subjugation raid only (more raids and tier rules later).
