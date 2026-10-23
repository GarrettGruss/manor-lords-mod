## Context

The spike (#360) found that a body delivery has no hook. It shows only as the pit inventory `Type 233` `amt` rising by 1. `pit:addToInventory` counts in the region stock at once and villagers haul it to a store in 3 to 5 game days.

## Decisions

- **Share math:** share of good g = `floor(record[g] / start_raiders)`. `start_raiders` is the raider count at the start of the raid, the same count that the carry cap uses. A share is the same for every body, so the order of bodies does not matter. Rounding down means a small record can give 0; the remainder stays in the stores as lost plunder. This is accepted.
- **Whose body:** a body is mapped to a raid by the raider key that the tracker already has (`GetAddress`). A dead raider stays in `Region.corpses` until a worker picks it up. The mod pays each key once.
- **Polling rate:** once each game second on the game thread, only while a Hussite raid with a record exists or has dead raiders. It reads one pit entry, so the cost is small.
- **Several bodies per poll:** the number of new bodies is the rise of `amt`; the mod pays that many shares, for the dead keys of Hussite raids that are not paid yet.
- **Several pits:** the mod uses the pit that has the rise.
- **Worker assignment:** the game does not assign workers to the pit. The player assigns a family. Tests call `building_assign_worker type=113` after the fixture loads (the fixture `base-corpse-pit` holds the built pit only).
- **No fallback:** no pit means no give-back. Bodies left on the ground are punished by the game's own approval mechanic (owner decision).
- **Saves:** the mod never calls a save function. The record is a ModState key.

## Risks

- Reading `unit.currAnim`, `unit.dropsTo` or `unit.Speed` crashed the game in the spike. The poll reads only the pit inventory.
- The pit inventory could also rise from non-raider bodies (villagers, native raiders). The mod pays only for dead keys it knows; extra rises are ignored.
