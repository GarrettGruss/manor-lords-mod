## 1. Spike (game agent; follow harness-game-spike; no save calls)

Write findings to `notes/<topic>.md`, one file per topic.

- [x] 1.1 Find the corpse pit: class, building id in `DT_Buildings`, how villagers carry bodies to it (the job, the corpse or body actor), and the events or UFunctions for body delivery or burial. Can Lua hook the moment a body arrives? (`notes/corpse-pit.md`)
- [x] 1.2 Can the mod tell which raider a body belongs to (raider unit or squad of a mod raid), so it can spawn the loot of that raider? (`notes/body-owner.md`)
- [x] 1.3 Can goods be spawned on the ground or in a pile at the pit (a dropped goods or resource pile actor)? Do villagers haul them to storage by themselves? Compare with the direct store add (`world.deposit`). (`notes/goods-pile.md`)
- [x] 1.4 What happens when no corpse pit exists, or bodies are not collected? Define the fallback to today's direct store add. (`notes/fallback.md`)
- [x] 1.5 Picture evidence of goods at the pit (`ctx.screenshot`), in `evidence/` with `evidence/README.md`.

## 2. Owner decisions

- [x] 2.1 Decided: the pit replaces the direct store add.
- [x] 2.2 Decided: the Hussite plunder record gives the loot; no fixed good. Decision: the Hussite plunder record, no fixed good.
- [x] 2.3 Decided: bodies left on the ground need no mod fallback. Decision: bodies left on the ground need no mod fallback.

## 3. Implementation (gated: only after the owner decisions and a new spec pull request)

- [x] 3.1 Moved to change `add-corpse-pit-loot`.
- [x] 3.2 Moot: the pit replaces the direct store add, so no fallback.
- [x] 3.3 Moved to change `add-corpse-pit-loot`.
- [x] 3.4 Wiki and CHANGELOG done here; skills are for the follow-up change.
