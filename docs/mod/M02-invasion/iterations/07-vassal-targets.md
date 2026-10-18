# M02 iteration 07: vassal-targets

Issue: #220. Branch: `feat/M02-invasion-07-vassal-targets` (stacked on PR #218, M08.02). Follow-up of iteration 03.

## Goal
The subjugation raid picks a vassal region as its target when a vassal exists (M00: early raids hit vassals first). When the raid holds that target long enough, the vassal falls: `vassals.lose_vassal(slot, "taken")`.

## Design (TBD values are marked)
- `invasion` has a vassal provider (`invasion.set_vassal_provider(fn)`). The raid spawn asks it for target regions. Without a provider, or without a vassal, the home region stands in as before (`stand_in = true`).
- The `tribute` feature registers the provider: handed-over vassals that are not the fallback capital and have not submitted (`vassals.target_regions`).
- A plunder raid still hits the home region.
- "Succeeds" (TBD simple rule): the subjugation raid on a vassal region has been active for `siege_days` game days (8) and still has at least `siege_min_living` (50 percent) of its initial units. Then the vassal is lost with reason `taken` (slot freed, refugees through M09). The region owner is NOT moved (it crashes the game, M07.04 notes).
- If the raid is beaten first (destroyed, or fewer units than the share) the vassal stays and its loyalty rises (M08.02 defended rule).
- One decision for each raid (`resolved`).

## Changes
- `invasion/init.lua`: `set_vassal_provider`, target from the provider.
- `raid_behavior/init.lua`: `active_raids()` (summaries).
- `vassals/init.lua`: `target_regions()`.
- `tribute`: `siege.lua` with a poll through the scheduler; pure rules in `rules.lua`; config `tribute.siege`; command `tribute_siege_state`.

## Acceptance criteria
- V1: with one vassal, the spawn log of the subjugation raid names the vassal region, `stand_in=false`.
- V2: with no vassal, the target is the home region with `stand_in=true`.
- V3: after `siege_days` active days with enough living units the vassal count goes from 1 to 0, the lost event has reason `taken`.
- V4: a raid that is destroyed before `siege_days` leaves the vassal.
- V5: the region owner of the vassal region is not written.
- V6: no crash in the run.

## Scenarios
- Fake game: `TargetRulesTests` and siege tests.
- Real game: `invasion-vassal-targets`.

## Result
not started
