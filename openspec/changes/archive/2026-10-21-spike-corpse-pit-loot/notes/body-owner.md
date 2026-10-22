# Body to raider (task 1.2)

Question: can the mod tell which raider a body belongs to, so it can spawn that raider's loot?

## Method
Runs `corpse-3` and `corpse-4`: `spawn_raiders`, `set_unit_loot` (6 on 3 or 4 raiders), `kill_units with_loot=1` (`SMUnit:just_die`), then read the `corpses` array of every region for `ItemsLooted`.

## Result: yes
- The body in `Region.corpses` is the SAME `SMUnit` object as the live raider (names such as `VAMP_DefaultUnit_C_2147452098`; `realPos` equal to the victim place that `kill_units` reported).
- `ItemsLooted` stays on the body after death (6 stayed 6 on 4 bodies in `corpse-3` and on 3 bodies in `corpse-4`). The game does not zero it. (The `raid-loot` test scenario says the loot goes to 0 after death: that is the census of LIVE units. Do not rely on it for bodies.)
- The raid tracker (`raid_behavior/world.lua`) keys units by `unit:GetAddress()` and reads `loot` while the unit lives. A body has the same address. The mod can keep `key -> loot` for a dead raider and look it up at pick-up or delivery.
- Not proven: address equality across two separate eval chunks. My test used a global table that did not survive between evals, so it showed 0 matches. That is a test artifact, not a game fact. Inside the mod (one Lua state) the existing key already works.

## What the mod can and cannot link
- Pick-up: a body key leaves `Region.corpses` and a pit worker `Inventory` goes 0 -> 1 (the worker nearest to the body place). The pair (worker, body key) can be stored.
- Delivery: that worker `Inventory` goes 1 -> 0 near the pit. Then the mod knows the body key and its loot.
- Simpler and enough: keep a FIFO queue of the loot of picked-up bodies. Each increase of the pit `Type 233` `amt` pays one entry. The order can differ per worker, so one body may get the loot of another body. The raid total stays right. If exactness matters, use the (worker, body) pair.
- Bodies of raiders that die in a region without a pit with workers are never picked up (see `fallback.md`).
- Villager and animal bodies are in the same list. The mod must pay loot only for keys it tracks as raiders.
