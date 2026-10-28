## Context

The feature `tech_tree` has one path choice, 8 nodes, 6 laws and 2 policy gates (`data/tech_tree/tree.json`). It limits nodes by `slots_for_level(level, slots_per_level)`. State is in ModState keys `tech_path`, `tech_nodes`, `tech_laws`. The corpse pit pays loot to bodies of Hussite raids all the time (`raid_behavior`, change `add-corpse-pit-loot`). The change `update-banditry-rebellion-raid` (#480) is in gate 2. It adds the rebellion rule (only armed families can rebel, `rebellion_weapon_ids`) and the loot override map.

## Data model (tree.json)

- Keep `paths`, `nodes`, `laws`, `vassal_policies`. Set `version` 2.
- New top-level list `common_nodes`: `{ id, name, effect, layout }` with no `path` and no `requires`. Ids: `corpse_robbing`, `armory_census`, `burial_rites`, `night_watch`, `woodsmen`.
- `laws` entries may have `"path": "common"` and `requires: [<common node id>]`. Ids: `strip_the_dead`, `disarm_the_peasantry`, `mass_graves`, `curfew`. A new field `excludes: [<law id>]` (Mass Graves excludes Strip the Dead; the check is symmetric).
- New effect kinds (an unknown kind stops the load, as today): `law_corpse_loot`, `law_disarm_homes`, `law_clear_bodies`, `law_banditry_gain` (value 0.5). The existing kinds `public_order` and `approval` carry +5 (Mass Graves), -3 (Disarm) and -4 (Curfew). The per-corpse order loss is a config value.
- `woodsmen` has `"action": "clear_the_woods"` and no standing effect.

## Picks

- Config (`tech_tree`): `picks_per_year` 1, `initial_picks` 1. `slots_per_level` is removed.
- State: `tech_picks_earned` (integer, picks given so far) and `tech_year_seen` (integer, last game year that gave picks). `tech_nodes` is unchanged and now also holds common tech ids (dot list; no id contains a dot). Free picks = `tech_picks_earned` minus the number of unlocked ids.
- Unlock check order: unknown id, already unlocked, no free pick ("no free pick"), then for a path node: path chosen, same path, required nodes. A common tech skips the path and order checks (open question 1: today every node is refused with "no path is chosen" before a path exists; that stays for path nodes).

## Yearly tick source

The mod has no calendar call for the year. `invasion` counts season changes (`yearly_season_no`, 4 a year; year 1 is the first 4 seasons after the mod started; pure rule `plan.season_year`). The tech tree reads that counter through a small getter in `features/invasion` (no new hook) in its existing `poll_ms` loop. When the year is above `tech_year_seen`, it adds `picks_per_year` for each new year, sets `tech_year_seen`, and saves both before it logs. A load does not give a pick twice because the year is saved first. If the getter is not ready, no pick is given and the next poll retries.

## Laws and effects

The effect totals (`rules.totals`) already feed `bandits`, `unit_balance`, `manor_stronghold` and `tribute`. New values in the totals: `corpse_loot` (Strip the Dead), `disarm_homes` (Disarm), `clear_bodies` (Mass Graves) and `banditry_gain_multiplier` (Curfew, product, default 1). A new enact refusal: a law named in `excludes` of an enacted law ("law X excludes law Y"). Common laws need no path.

- Strip the Dead: `raid_behavior` pays loot only while `corpse_loot` is on. Without it the pit poll still counts corpses but pays nothing (behavior change from always on). With it, a body of a bandit or a soldier of any raid (including native raids) pays its goods: a Hussite body pays the share of its record, other bodies pay `strip_the_dead.body_goods`. For each corpse looted the mod lowers the mod order by `strip_the_dead.order_loss` (default 1) through `bandits`, in one clamped write at the end of each pit poll.
- Disarm the Peasantry: a new tick in `tech_tree/world.lua` every `disarm.tick_days` game days (default 1). For each home that holds an id of `bandits.rebellion_weapon_ids`, it reads the stock, calls `consumeGoodNoCheck`, and then `addToInventory` on the storehouse for the same amount (both proven in the rebellion spike). No family then has a valid weapon, so the rebellion rule "needs `rebellion_families` valid families" blocks the rebellion (telemetry `rebellion_blocked`). The militia must re-arm when called. `approval -3` is a normal effect.
- Mass Graves: each game day, bodies of the day before are hidden (`SetActorHiddenInGame(true)`) and `Region.corpses:Empty()` is called (proven safe for about 30 game days). The mod never calls `K2_DestroyActor`. +5 Public Order is a normal effect. Rebellion overrides: the rebellion spec deletes an override at body expiry, so a cleared body would lose the rebel goods. This change pays the goods of the entry to the storehouse (`addToInventory`) at the clear step and then clears the entry (open question 5).
- Curfew: `bandits.set_modifiers` gets `banditry_gain_multiplier`; the order tick uses `homeless_term * multiplier`, rounded half up. `approval -4` is a normal effect.

## Clear the Woods

Command `InvasionMod.tech_tree_clear_woods`. It needs Woodsmen unlocked. Steps, as proven in the spike `spike-militia-corpses-and-camp-removal`: find the camp master (`bType` 100), call `just_die` on its Brigands, hide the bodies, then `SMBuildingMaster:demolish(true)`. It never calls `K2_DestroyActor` on an `SMUnit`. It is a one-time use (`tech_woods_used`, integer). It is refused when no camp exists or it was used. It does not remove the Outlaws pawn.

## Interaction with update-banditry-rebellion-raid

- Disarm uses `bandits.rebellion_weapon_ids`. If that change is not merged, gate 2 uses the list `{133, 271}` in `tech_tree` config as a fallback.
- Mass Graves uses the loot override map of `raid_behavior`. If the map does not exist yet, the clear step only hides bodies.
- Both changes edit `config.lua` and the bandits tick. Rebase on `main` before the archive.

## Risks

- A home may hold goods that the tick cannot find by id; they stay and a rebellion is possible. Logged as `disarm_homes_missed`.
- Clearing bodies while a pit worker carries one may break a task; the mod skips such bodies if the game shows it, else it logs.
- Strip the Dead on native raid bodies is new. Loot values are TBD and need a balance run.
- An old save has no `tech_picks_earned`: the first poll gives `initial_picks` and the picks of the years seen so far.

## Not in scope

Bounties; changes to the F9 menu (open question 6).
