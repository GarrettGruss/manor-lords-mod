# Design: store tiers and raid stealing

## Context

Legacy source: `openspec/changes/archive/2026-10-16-legacy-m03-raid-behavior/README.md`. The loss per store and the fire to ruins were spiked in `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-S6.md` and `spike-R8.md`.

Manor storage finding: `openspec/changes/archive/2026-10-15-legacy-12-manor-exploration/implementation-notes/worker-slots.md` (2026-10-11, run `workers-spike-1`). A worker slot with the storehouse role (job 45) can be created on the Keep from Lua by writing the row "57" of the DataTable `buildingStats` (`isWork`, `job`, `workerTypes.Y`, `buildingFunction`, `storageLimitGeneric`). A family can be assigned and carries goods into the Keep. Related: `openspec/changes/archive/2026-10-15-legacy-12-manor-exploration/implementation-notes/storage-m1.md` (the Keep has an `Inventory` and a generic limit of 50). Both are from earlier spikes, with a Keep finished by a shortcut.

## Answered questions (owner, 2026-10-19)

1. Which store is guarded? The manor itself. Tier 2 is the manor storage. The finding above shows that the manor can get storage and hauling jobs.
2. Loss share per store tier? Removed. Replaced by the rules below.
3. Ruin rebuild discount? Dropped. The game manages ruin rebuild.
4. Where does the loss act? The mod cannot steer raiders, so it depends on the raid mode (see Decisions).

## Decisions

- Tiers: tier 1 = storehouse and granary. Tier 2 = manor storage. Raiders can steal from tier 1, never from tier 2. The tier list is in the feature config.
- Game raid (the game steers raiders to pillage and steal): the mod does not compute stolen goods. The game manages it.
- Baron AI raid (baron units cannot pillage or steal): the mod steals in Lua.
  - For each baron unit, measure its distance to the battle marker.
  - If the distance is above a configurable threshold (300 m for now), the unit is "stealing".
  - A stealing unit takes a configurable amount (10 goods per in-game day for now) from tier 1 stores only.
  - The raid has a configurable total steal goal, scaled by game difficulty (for now 100 for a small raid and 300 for a large raid). Stealing stops at the goal.
- Stretch goal (separate requirement): a tech "Manor" in a third, common branch of the tech tree. One tech for now. It unlocks storage under the manor with the capacity and job slots of a level 1 storehouse (generic limit 250, 3 worker slots, see the worker-slots finding).

## Open questions

1. How does game difficulty scale the steal goal? Only the values for a small raid (100) and a large raid (300) are known. Answer: the owner, then a spike on how to read the difficulty.
2. Which goods are taken first, and are they taken in turn from several tier 1 stores or from the nearest one? Answer: the owner.
3. Where is the battle marker read from, and in which unit is the distance (the 300 m threshold)? Answer: a spike (task 1.1).
4. What counts as a small raid and a large raid? Answer: the owner.
5. Does a game raid reach the manor store? The mod does not steer it. Answer: a spike (task 1.2).
6. Stretch tech: where is the third, common branch in the tech data, and what are the cost and the research time? Answer: the owner and a spike (task 1.3).
7. Do the goods stolen in a baron raid vanish, or can the player recover them? Answer: the owner.
