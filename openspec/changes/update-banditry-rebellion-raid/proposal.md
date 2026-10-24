## Why

Issue: #480. Owner decisions 2026-10-24 (first round in gate 1 PR #481, second round in this follow-up). The camp outcome of `update-banditry-bandit-camp` (18 families leave, one camp of 18 Brigands far away) does not hurt the village. The spike `rebel-noai` (`notes/rebel-noai-findings.md`) showed that squads of the bandit pawn "Outlaws", spawned at the homes of removed families, raid the village at once in fixture `playtest-noai`, burn buildings, log "enough looted" and leave the map. That is the rebellion the owner wants. The spike `spike-militia-weapon-rebellion` showed that militia weapons sit in homes and that `consumeGoodNoCheck` removes them. The owner now wants the rebels to be armed with the weapons of the village, and the village to pay for it.

## What Changes

- The banditry outcome becomes a rebellion. `rebellion_families` (default 6) families leave, and `rebellion_squads` (default 1) Brigands squad (18 units) of the pawn "Outlaws" spawns at the home of the first removed family (`HarnessBandits.homeless_rebel`, mode `home`, `spawnArmy`). The native Outlaws AI raids the village, logs "enough looted" and leaves the map.
- Weapons (new). A rebellion needs weapons. Before it starts, the mod counts the weapons in villager homes. It needs `rebellion_weapons` (default 18). If the homes hold fewer, NO rebellion happens: no family leaves, no squad spawns, the timer stays expired and the mod retries on the next tick, and a telemetry event is logged. If the homes hold enough, the mod removes 18 weapons at random from the homes (`consumeGoodNoCheck`) and then does the rebellion. The mod removes nothing when the rebellion will not happen.
- Militia (new). Rallied militia carries weapons that left the homes. The mod also counts the weapons of rallied militia units of the rebelling region, so rallying does not stop a rebellion. Engine facts are unknown. A spike task finds them. The fallback is in `design.md` (proposed, owner to confirm).
- Loot override (new, generic, in `raid_behavior`). A per-unit map (unit key = a stable key that survives a load, see `design.md`; `GetAddress` is used only inside one session) to a list of goods. The mod records the removed weapons and spreads them over the spawned brigands (one item per unit). When the body of such a unit is paid out at the corpse pit, the pit gets the override goods instead of the config loot. Units without an override keep the existing behavior. Live plunder loot still works next to it.
- Corpses (new task). The running spike `spike-rebel-without-corpses` checks if killed families leave bodies and if a removal without a body is possible. The implementation uses its result (no waiting).
- The mod no longer calls `spawnBanditCamp` for each leave event. It calls it only when the Outlaws pawn is missing, to create the pawn, and then calls `addPawnRelations`. Side effect, accepted: that call also makes one camp of 18 Brigands.
- Config values in the `bandits` table of `mod/InvasionMod/Scripts/config.lua`: `threshold` 25, `timer_days` 60 (was 90), `order_gain` 25, `tick_days` 30 (unchanged), `leavers` renamed `rebellion_families` with default 6 (was 18), new `rebellion_squads` 1, new `rebellion_weapons` 18, new `rebellion_weapon_ids` (list of item ids).
- The other order rules stay: manor term +10 plus tech bonus, homeless term -5 per homeless family.

## Open questions (with defaults)

1. Militia fallback when equipped weapons cannot be read or removed. Proposed default: count the equipped weapons of rallied units toward the 18 and take the rest from homes. If even reading is impossible, block the rebellion while militia is rallied. Proposed, owner to confirm.
2. Save and load of the loot override map: DECIDED (see Decisions), saved with ModState. Still open: whether bodies are also saved (proposed: yes, until pay-out or body expiry, owner to confirm), and the stable unit key (spike task 2.8).
3. The full list of weapon and armor item ids that homes hold. Known ids are in `design.md` (Weapon item ids). Only 133 and 271 were seen stocked in homes. A spike task finds the rest.
4. Weapons already removed when a later step fails. Proposed default: not put back, logged as an error. Owner to confirm.
5. The camp side effect when the pawn is missing. Default: accepted (one camp of 18 Brigands, once). Pending the spike `spike-militia-corpses-and-camp-removal`.

## Decisions (owner, 2026-10-24)

- The loot override map MUST be saved in the save file while the unit is alive on the map. It uses ModState (Tags on the player pawn). This replaces the earlier proposal "not saved". The unit key must be stable across a load, and the design re-links the saved entries to the units after a load. When the unit dies, the entry moves to its body until pay-out (proposed: bodies are saved too, until pay-out or body expiry, owner to confirm). When the unit leaves the map, the entry is dropped.
- The militia fallback question is being answered by the running spike `spike-militia-corpses-and-camp-removal`. The camp side effect (can the camp and its bandits be deleted) waits for the same spike.
- Weapon id facts from `DT_Items` (extracted table, may be older than the game): 133 spears, 271 shields_large, 270 shields_small, 177 weapons_sidearms, 178 weapons_polearms, 205 warbows, 206 crossbows, 163 gambesons (armor), 164 mail_armor, 273 militia_helmets_resource, 288 and 289 mercenary helmets. `spearMilitia` gear is 163, 133, 271, 273 (gambeson, spear, large shield, helmet). Only 133 and 271 were seen stocked in homes. The default weapon id list does not change yet.

## Impact

- Specs: `mod/bandits` (RENAMED and MODIFIED: the conversion requirement; MODIFIED: the timer requirement; ADDED: weapons and militia), `mod/raid_behavior` (ADDED: loot override).
- Code (gate 2): `mod/InvasionMod/Scripts/features/bandits/world.lua` (`M.leave`), `init.lua`, `rules.lua`, `features/raid_behavior` (override map, ModState save, re-link on load, pit pay-out), `mod/InvasionMod/Scripts/config.lua`, tests, test scenarios.
- Risk: the raid may be slow when a neighbour AI army exists. Squad removal at the map edge is unverified. Militia weapon removal is unverified.
- Overlap: the change `update-spawn-from-map-border` touches the same conversion requirement. Check it on rebase.
