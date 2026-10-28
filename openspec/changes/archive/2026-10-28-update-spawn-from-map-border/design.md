# Design: update-spawn-from-map-border

## Current state

All mod spawns use the game call `RTSMultiEngineCPP:spawnArmy(position, template names, owner pawn, company id, arrives in N days)`. The mod always passes company id 0 and arrival time 0:

- `mod/shared/HarnessLords/HarnessLords.lua` `lord_spawn_army`: position = player pawn + (dx, dy), limit 60000.
- `mod/shared/HarnessBattle/HarnessBattle.lua` `spawn_at`: a given point.
- `mod/InvasionMod/Scripts/features/invasion/relief.lua`: a given spot.

## Lead 1: the arrival-days argument (try first)

The fifth argument of `spawnArmy` is "arrives in N days". The game uses it for its own raiders, which come in from off the map. Spike A tests a value greater than 0 and answers:

- Does the army appear at once, or after N days?
- Where does it appear (the position argument, or the map border)? Does it walk to the target region?
- Does `spawnArmy` return squad ids before arrival, so the mod can track the army?
- Does the AI lord, war and challenge setup still work?
- Which owner pawn is needed (a lord, the player pawn)?

If the game brings the army in natively, the change is small: pass `arrival_days` from config and count timers from arrival. No custom border code.

## Fallback: a border spawn and a march order

If Spike A fails (the army appears at the position at once, or not at all):

1. The target is the target region (the player manor, or a vassal region for subjugation).
2. Pick a border point. Default rule: the border point nearest to the target, or on the road towards it when a road reaches the border. Spike B finds the map bounds and the playable area.
3. The point must be on walkable land. It must not be in water or outside the playable area. Spike B names the query that checks it. If a point fails, move along the border to the next candidate.
4. Spawn the squads there with `spawnArmy(..., 0)`. Then order a march to the target. Spike C finds the march call.
5. A pure module (for example `features/invasion/border.lua`) holds the border point logic, so fake game tests can check it. Harness code must not name the mod (`test_boundary.py`).

## Timers and banners

Default: the raid starts at arrival. The 30-day banner counts to arrival. If the march takes N days, the spawn happens N days before the planned raid day. The raid tracker (`raid_behavior`, `lord_raid`) reports the raid only after arrival, so leave rules and `final_raid_ended` do not see an army that is still marching. A forced raid (`invasion_force_next`) spawns at the border and arrives as normal.

## Risks

- Maps differ. Border points and the playable area must come from the game (Spike B), not from constants.
- A long march may meet water or a cliff. The march order must use the game's own path finding.
- Other mod code must not treat a marching army as missing.
- Two UE4SS Lua crashes happened right after large spawns (a great wave of 448 raiders). A spawn at the border with an arrival time may spread the load over game time. This is a possible side benefit, not a requirement. If wave spawns still crash, that is a separate change.

## Results of the spikes (2026-10-28)

| Question | Result | Notes |
|---|---|---|
| A: arrival days greater than 0 | Ignored for a lord army. The army appears at once at the given position and walks. | `notes/arrival-days.md` |
| B: map bounds, walkable land | The map edge actor has splines with the playable square. No navmesh exists. 8 of 8 border points 3000 units outside the edge worked in the real game. | `notes/map-border.md` |
| C: march order | Not needed for hostile armies (lord AI with a challenge). Not possible for the relief army. | `notes/march-order.md` |

## Built design

- `features/invasion/border.lua`: pure rules (`pick`, `direction`, `bounds_of`, `is_outside`) and `read_bounds` (the map edge actor, class `Medium_Map_Bounds_C`).
- `lord_raid.plan_border(options)` picks the point for the player manor. `lord_raid.start(templates, settings, point)` spawns each squad at the point (`HarnessLords.lord_spawn_army` with absolute `x`, `y`).
- `invasion/init.lua` spawns `march_lead_days` before the raid day, shows the direction banner at the spawn and "Raiders are here" at arrival, and moves the wave gap to the arrival (`on_arrival`).
- `raid_behavior`: a raid with `lord.marching` has no leave, plunder or steal rule and is not listed as active until `check_arrival` finds a fifth of its raiders within 12000 units of the manor (or after 12 game days). The start day becomes the arrival day.
- Config: `invasion.border` (`rule`, `margin`, `inset`, `min_spawn_distance`, `march_lead_days`, `arrival_radius`, `arrival_share`, `max_march_days`, `north_axis`). The key `arrival_days` of the first draft is gone: the game has no such call.
- Fallback: when the edge actor is not found, the log says so and the army starts at `start_dy` from the player pawn as before.
- The relief army and the test spawns of `HarnessBattle` are unchanged.

## Spikes and open questions

| Question | Spike |
|---|---|
| Does arrival days greater than 0 bring the army from off the map? | A |
| Map bounds, playable area, border points on walkable land | B |
| March order after a border spawn (fallback only) | C |
| Which border and how many days? | answered by A and B, then play tests |

Findings go in `notes/` of this change. Engine facts that stay true move to the wiki before the archive.
