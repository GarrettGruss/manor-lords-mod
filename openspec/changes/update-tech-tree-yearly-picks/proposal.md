## Why

Issue: #499. Owner decisions 2026-10-27. Today the player gets one tech node for each settlement level (`slots_per_level`). The owner wants a slower, steadier pace: one pick for each game year, saved when unused. The owner also wants techs that serve both paths, and laws that give the player real tools against unrest, rebellion and bodies. This change adds five common techs, four common laws and one one-time action.

## What Changes

- Picks (replaces the node slots). The player gets `picks_per_year` (default 1) tech pick at the start of each game year. Unused picks are banked. Every unlock (path node or common tech) costs one pick. The settlement level no longer matters. `slots_per_level` is removed. The pick count is saved with ModState.
- Paths do not change. The player picks Oppression or Prosperity, the choice is final, path nodes unlock in order. The existing 8 nodes, 6 laws and 2 vassal policy gates do not change.
- Common techs (new, no path, any order, both paths): Corpse Robbing, Armory Census, Burial Rites, Night Watch, Woodsmen. A pick can go to the next node of the chosen path or to any common tech.
- Common laws (new, free, repealable, they count toward `max_active_laws`, default 2):
  - Strip the Dead (Corpse Robbing): dead bandits and soldiers give loot at the corpse pit; -1 Public Order for each corpse looted.
  - Disarm the Peasantry (Armory Census): each tick, weapon and armor items in homes go back to the storehouse; no family is a valid rebel, so no rebellion; -3 approval.
  - Mass Graves (Burial Rites): bodies are cleared the next day; +5 Public Order; cannot be in force together with Strip the Dead.
  - Curfew (Night Watch): banditry rises half as fast; -4 approval.
- Clear the Woods (Woodsmen): a one-time action that destroys a bandit camp (kill its Brigands, hide the bodies, `demolish(true)`).
- Behavior change: corpse loot at the pit is ALWAYS ON today (Hussite raiders only). After this change it happens only while Strip the Dead is in force (and then also for bandit and soldier bodies). Without the law, no body pays loot.
- Out of scope: Bounties (no safe write of regional wealth is proven).

## Decisions (owner, 2026-10-27)

- One pick for each game year, banked. No settlement level rule.
- Common techs can be picked in any order, by both paths.
- The common laws are free, repealable and count toward `max_active_laws`.
- Mass Graves and Strip the Dead exclude each other.
- Bounties is not in this change.

## Open questions (with defaults)

1. Can a common tech be picked before a path is chosen? Default: yes. A common tech belongs to no path, so the "no path is chosen" refusal applies only to path nodes.
2. How many picks at the start? Default: `initial_picks` 1 (the pick of game year 1 is available at once), then `picks_per_year` at each new year.
3. Loot of a dead bandit or soldier body under Strip the Dead. Default: `strip_the_dead.body_goods` in config (TBD value, placeholder one spear, id 133). A Hussite body keeps the share of its raid record.
4. What "Curfew halves banditry gain" means. Default: it halves the order loss of each tick (`homeless_term`, the loss for each homeless family), because that is how banditry rises. It does not change the timer.
5. Overrides of the rebellion on a cleared body (Mass Graves). Default: the goods of the entry go to the storehouse (`addToInventory`) when the body is cleared, and the entry is cleared. Without this the goods would be lost.
6. The tech menu (F9) shows no common techs and no pick count after this change. Default: a separate follow-up change updates `mod/tech_tree_widget`; until then the player uses the named commands.
7. The Clear the Woods target. Default: the nearest bandit camp to the manor. The action is refused when no camp exists.

## Impact

- Specs: `mod/tech_tree` (RENAMED and MODIFIED: data file, node slots become picks, laws, commands; ADDED: common techs, four common laws, Clear the Woods), `mod/raid_behavior` (MODIFIED: pit loot only under Strip the Dead).
- Code (gate 2): `Scripts/features/tech_tree/` (rules, init, world), `data/tech_tree/tree.json`, `config.lua` (`tech_tree`), the effect hooks in `bandits` and `raid_behavior`, a new home tick in `tech_tree/world.lua`, tests, test scenarios, wiki, CHANGELOG.
- Overlap with `update-banditry-rebellion-raid` (#480, in gate 2): Disarm the Peasantry uses the rebellion rule "only armed families can rebel" and its `rebellion_weapon_ids`; Mass Graves meets its loot override. See `design.md`. Merge that change first, or rebase on it.
- Risk: homes may not return goods the way the spike showed for every item id; the yearly tick source is the season counter of `invasion`.
