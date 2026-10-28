## Context

The feature `tech_tree` has one path choice, 8 nodes, 6 laws and 2 policy gates (`data/tech_tree/tree.json`). It limits nodes by `slots_for_level(level, slots_per_level)`. State is in ModState keys `tech_path`, `tech_nodes`, `tech_laws`. The corpse pit pays loot to bodies of Hussite raids all the time (`raid_behavior`, change `add-corpse-pit-loot`). The change `update-banditry-rebellion-raid` (#480) is in gate 2. It adds the rebellion rule (only armed families can rebel, `rebellion_weapon_ids`) and the loot override map.

## Data model (tree.json)

- Keep `paths`, `nodes`, `laws`, `vassal_policies`. Set `version` 2.
- New top-level list `common_nodes`: `{ id, name, effect, layout }` with no `path` and no `requires`. Ids: `corpse_robbing`, `armory_census`, `night_watch`.
- `laws` entries may have `"path": "common"` and `requires: [<common node id>]`. Ids: `strip_the_dead`, `disarm_the_peasantry`, `curfew`. No law excludes another law, so there is no `excludes` field.
- New effect kinds (an unknown kind stops the load, as today): `law_corpse_loot`, `law_disarm_homes`, `law_banditry_gain` (value 0.5). The existing kind `approval` carries -3 (Disarm) and -4 (Curfew). The per-corpse order loss is a config value.

## Picks

- Config (`tech_tree`): `picks_per_year` 1, `initial_picks` 1, `spring_season` (the value of the spring season in the calendar enum; read in the real game in task 1.3, not guessed). `slots_per_level` is removed.
- State: `tech_picks_earned` (integer, default -1: not started) and `tech_spring_no` (integer, default -1: the season counter of the last spring that gave a pick or that was seen at the start). `tech_nodes` is unchanged and now also holds common tech ids (dot list; no id contains a dot). Free picks = `tech_picks_earned` minus the number of unlocked ids.
- Unlock check order: unknown id, already unlocked, no free pick ("no free pick"), then for a path node: path chosen, same path, required nodes. A common tech skips the path and order checks. A path node is still refused with "no path is chosen" before a path exists.

## Spring rule (tick source)

The mod has no calendar call for the year. `invasion` counts season changes in `yearly_season_no` and reads the season value (`current_season()` in `features/invasion`). The tech tree reads both through a small getter in `features/invasion` (no new hook) in its existing `poll_ms` loop.

- First poll with `tech_picks_earned` = -1 (new game, or an old save): set `tech_picks_earned` to `initial_picks` and `tech_spring_no` to the current season counter, then save both. The spring of the start (if the game starts in spring) gives no extra pick.
- Later polls: when the current season equals `spring_season` and the season counter is above `tech_spring_no`, add `picks_per_year`, set `tech_spring_no` to the counter, and save both before it logs. A game that starts in summer, autumn or winter gets the first yearly pick at the next spring. A load does not give a pick twice because the counter is saved first.
- If the getter is not ready (no season seen yet), no pick is given and the next poll retries.

## Laws and effects

The effect totals (`rules.totals`) already feed `bandits`, `unit_balance`, `manor_stronghold` and `tribute`. New values in the totals: `corpse_loot` (Strip the Dead), `disarm_homes` (Disarm) and `banditry_gain_multiplier` (Curfew, product, default 1). Common laws need no path.

- Strip the Dead: `raid_behavior` pays loot only while `corpse_loot` is on. Without it the pit poll still counts corpses but pays nothing (behavior change from always on). With it, a body of a bandit or a soldier of any raid (including native raids) pays loot. For each corpse looted the mod lowers the mod order by `strip_the_dead.order_loss` (default 1) through `bandits`, in one clamped write at the end of each pit poll. Loot source, in this order:
  1. the loot override of the body, when it has one (change `update-banditry-rebellion-raid`, map in `raid_behavior`; used by rebel bodies);
  2. a Hussite body: its share of the raid record (`rules.body_share`, fed by the plunder goods of `raid_behavior.plunder`; this is the existing pit loot);
  3. any other tracked body: the table `raid_behavior.body_loot`, one list of loot variants for each body kind (`bandit`, `soldier`). Each variant is `{ weight = 1, goods = { [good id] = amount } }` (weight optional, default 1). The mod draws one variant for each body, at random by weight.
  Owner values (2026-10-28), kind `bandit` (Brigands): variant 1 is 1 sword (good 177, `weapons_sidearms`) and 1 small shield (270, `shields_small`); variant 2 is the same plus 1 helmet (273, `militia_helmets_resource`). The ids were checked in `DT_Items` (`modtools/work/DT_Items.vanilla.json`), see `notes/loot-ids.md`. The kind `soldier` is empty: the owner gave no values. An empty list pays nothing.
  Gate 2 finding: a body at the pit has no identity (the pit only shows a corpse count). The mod can attribute a body only to a dead raider that `raid_behavior` tracked. A Hussite raider pays its raid share (rule 2). A dead Brigand of a native or bandit raid (counted in `raid.unpaid_other`) pays a `bandit` variant (rule 3). Other bodies (villagers, militia, soldiers of the player) are not attributed: they pay nothing and cost no order. Each looted (attributed) body lowers the order by `order_loss`, also when its loot list is empty. Bodies that arrive while the law is off are consumed with no pay-out, so enacting the law never pays old bodies.
- Disarm the Peasantry: a new tick in `tech_tree/world.lua` every `disarm.tick_days` game days (default 1). For each home that holds an id of `bandits.rebellion_weapon_ids`, it reads the stock, calls `consumeGoodNoCheck`, and then `addToInventory` on the storehouse for the same amount (both proven in the rebellion spike). No family then has a valid weapon, so the rebellion rule "needs `rebellion_families` valid families" blocks the rebellion (telemetry `rebellion_blocked`). The militia must re-arm when called. `approval -3` is a normal effect.
- Curfew: `bandits.set_modifiers` gets `banditry_gain_multiplier` (0.5); the order tick uses `homeless_term * multiplier`, rounded half up. `approval -4` is a normal effect. The timer, threshold and order gain stay.

## Interaction with update-banditry-rebellion-raid

- Disarm uses `bandits.rebellion_weapon_ids`. If that change is not merged, gate 2 uses the list `{133, 271}` in `tech_tree` config as a fallback.
- Strip the Dead uses the loot override map of `raid_behavior`. If the map does not exist yet, rule 1 is skipped.
- Both changes edit `config.lua` and the bandits tick. Rebase on `main` before the archive.

## Risks

- A home may hold goods that the tick cannot find by id; they stay and a rebellion is possible. Logged as `disarm_homes_missed`.
- Strip the Dead on native raid bodies is new. Loot values are not set and need a balance run.
- An old save has no `tech_picks_earned`: the first poll gives `initial_picks` only (no back pay for past years).

## Not in scope

Bounties; the in-game tech window `mod/tech_tree_widget` (separate follow-up change).
