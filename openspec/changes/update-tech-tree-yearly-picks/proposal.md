## Why

Issue: #499. Owner decisions 2026-10-27 (first set) and 2026-10-27 (answers to the open questions). Today the player gets one tech node for each settlement level (`slots_per_level`). The owner wants a slower, steadier pace: one pick for each game year, earned at the start of spring, saved when unused. The owner also wants techs that serve both paths, and laws that give the player real tools against unrest and rebellion. This change adds three common techs and three common laws.

## What Changes

- Picks (replaces the node slots). The player gets `initial_picks` (default 1) pick at the start and `picks_per_year` (default 1) pick at each start of spring. Unused picks are banked. Every unlock (path node or common tech) costs one pick. The settlement level no longer matters. `slots_per_level` is removed. The pick state is saved with ModState.
- The tech year starts in spring. A pick is earned when the season counter shows a new spring, not after any four season changes. A game that starts in another season gets its first yearly pick at the first spring after the start. A game that starts in spring gets no extra pick for that spring (the start grant is `initial_picks`).
- Paths do not change. The player picks Oppression or Prosperity, the choice is final, path nodes unlock in order. The existing 8 nodes, 6 laws and 2 vassal policy gates do not change.
- Common techs (new, no path, any order, both paths): Corpse Robbing, Armory Census, Night Watch. A pick can go to the next node of the chosen path or to any common tech. A common tech can be picked before a path is chosen (common techs only).
- Common laws (new, free, repealable, they count toward `max_active_laws`, default 2):
  - Strip the Dead (Corpse Robbing): the body of a dead bandit or soldier gives loot at the corpse pit, from the existing loot rules; -1 Public Order for each corpse looted.
  - Disarm the Peasantry (Armory Census): each tick, weapon and armor items in homes go back to the storehouse; no family is a valid rebel, so no rebellion; -3 approval.
  - Curfew (Night Watch): the order loss of banditry (`homeless_term`) is halved; -4 approval.
- Behavior change: corpse loot at the pit is ALWAYS ON today (Hussite raiders only). After this change it happens only while Strip the Dead is in force (and then also for bandit and soldier bodies). Without the law, no body pays loot.
- Out of scope: Bounties (no safe write of regional wealth is proven); the in-game window `mod/tech_tree_widget` (a separate follow-up change; until then the player uses the named commands).

## Decisions (owner, 2026-10-27)

- One pick for each game year, earned at the start of spring, banked. No settlement level rule.
- Common techs can be picked in any order, by both paths, also before a path is chosen (common techs only).
- `initial_picks` is 1.
- The common laws are free, repealable and count toward `max_active_laws`.
- Strip the Dead takes its loot from the existing loot rules (the config loot paid at the corpse pit today) or, when the body has one, from the rebellion loot override (change `update-banditry-rebellion-raid`).
- Curfew halves `homeless_term`.
- Mass Graves (law), Burial Rites (tech), Woodsmen (tech) and Clear the Woods (action) are removed from this change.
- The tech window is a separate follow-up change.
- Bounties is not in this change.

## Open questions (with defaults)

1. The spring value of the game season enum. Default: config `tech_tree.spring_season`; gate 2 reads the value in the real game (task 1.3) and does not guess it.
2. Loot of a bandit or soldier body. No such loot entry exists today (see `design.md`). Default: a config table `raid_behavior.body_loot`, filled by the owner before the balance run; until then Strip the Dead pays nothing for those bodies.

## Impact

- Specs: `mod/tech_tree` (RENAMED and MODIFIED: data file, node slots become picks, laws, commands; ADDED: common techs, three common laws), `mod/raid_behavior` (MODIFIED: pit loot only under Strip the Dead).
- Code (gate 2): `Scripts/features/tech_tree/` (rules, init, world), `data/tech_tree/tree.json`, `config.lua` (`tech_tree`, `raid_behavior`), the effect hooks in `bandits` and `raid_behavior`, a new home tick in `tech_tree/world.lua`, tests, test scenarios, wiki, CHANGELOG.
- Overlap with `update-banditry-rebellion-raid` (#480, in gate 2): Disarm the Peasantry uses the rebellion rule "only armed families can rebel" and its `rebellion_weapon_ids`; Strip the Dead uses its loot override. See `design.md`. Merge that change first, or rebase on it.
- Risk: homes may not return goods the way the spike showed for every item id; the spring tick source is the season counter of `invasion`.
