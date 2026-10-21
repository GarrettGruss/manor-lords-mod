## 1. Spike (game agent; follow harness-game-spike; no save calls)

Write findings to `notes/<topic>.md`, one file per topic.

- [x] 1.1 Find the corpse pit: class, building id in `DT_Buildings`, how villagers carry bodies to it (the job, the corpse or body actor), and the events or UFunctions for body delivery or burial. Can Lua hook the moment a body arrives? (`notes/corpse-pit.md`)
- [x] 1.2 Can the mod tell which raider a body belongs to (raider unit or squad of a mod raid), so it can spawn the loot of that raider? (`notes/body-owner.md`)
- [x] 1.3 Can goods be spawned on the ground or in a pile at the pit (a dropped goods or resource pile actor)? Do villagers haul them to storage by themselves? Compare with the direct store add (`world.deposit`). (`notes/goods-pile.md`)
- [x] 1.4 What happens when no corpse pit exists, or bodies are not collected? Define the fallback to today's direct store add. (`notes/fallback.md`)
- [x] 1.5 Picture evidence of goods at the pit (`ctx.screenshot`), in `evidence/` with `evidence/README.md`.

## 2. Owner decisions

- [ ] 2.1 Owner decides: replace the direct store add, or keep it as fallback only.
- [ ] 2.2 Owner decides: loot amount per body, and which good spawns.
- [ ] 2.3 Owner decides: what happens to loot that nobody hauls.

## 3. Implementation (gated: only after the owner decisions and a new spec pull request)

- [ ] 3.1 Hook body arrival at the pit and spawn the loot there.
- [ ] 3.2 Keep the direct store add as fallback.
- [ ] 3.3 Add tests and a test scenario; update the spec "Checked by" lines.
- [ ] 3.4 Update the wiki, skills and `CHANGELOG.md`.
