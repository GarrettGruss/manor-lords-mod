## Why

Issue: #360

Owner request (chat, 2026-10-21): "For the loot mechanic. Launch a spike to see if the corpse pit could be used as an alternative to teleporting the loot into a storehouse. I would like loot to spawn at the corpse pit as bodies are brought to it."

Today the loot of a dead raider is added straight into a store. The goods appear in the store with no visible carrier. The owner wants the goods to appear at the corpse pit when the body arrives there.

## How loot returns today

- A raid tick calls `rules.update` and calls `return_loot` for each death (`mod/InvasionMod/Scripts/features/raid_behavior/init.lua:182`).
- `return_loot` (`init.lua:64`) picks the nearest store and the good it holds most of. It calls `world.deposit(store, good, death.loot)` (`init.lua:73`, `world.lua:210`). The goods are added to the store at once.
- With no store, the loot is counted as lost (`init.lua:69-70`).
- The carry cap is written back to the game by `world.write_loot` (`world.lua:60`, called at `init.lua:89`).
- Living spec: `openspec/specs/mod/raid_behavior/spec.md`, requirement "The loot of a dead raider goes to the nearest store".

## What Changes

- A spike answers if the corpse pit can replace the direct store add. No code in this change.
- If the spike says yes, the owner decides, and a later gated task changes `return_loot`.
- The delta spec adds scenarios for the new behavior. They stay "Not checked yet" until the spike ends.

## Impact

- Affected capability: `mod/raid_behavior`.
- Affected code later: `features/raid_behavior/init.lua`, `world.lua`.
