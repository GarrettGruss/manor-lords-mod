## Flow

1. The banditry timer expires (`timer_days` after the order fell below `threshold`).
2. Weapon check. Count weapons in homes (items in `rebellion_weapon_ids`, held in `building.Inventory` of homes, bType 3), plus weapons of rallied militia (see Militia). If the count is below `rebellion_weapons` (18): stop. The timer stays expired, the mod retries on the next tick (`tick_days`), the families stay, and the mod logs the telemetry event `rebellion_blocked` (fields: weapons found, weapons needed, militia counted). Nothing was removed.
3. Pick 18 weapons at random from the counted items and remove them: one `building:consumeGoodNoCheck(good)` per item on the home that holds it (as `world.plunder` does). Record the list of removed goods.
4. `rebellion_families` (6) families leave (`core.remove_families`). The village keeps `min_families_left`.
5. If no Outlaws pawn exists, `spawnBanditCamp()` makes it (one camp of 18 Brigands as a side effect), then `addPawnRelations(pawn)`.
6. `homeless_rebel` mode `home` spawns `rebellion_squads` Brigands squads (`spawnArmy`, owner = Outlaws) at the first removed home.
7. The mod reads the unit keys (`GetAddress`) of the new squad and gives each unit one item of the removed list (18 items over 18 units, in the order of the random pick). With other counts: round robin. It stores the map in the loot override state.
8. The native AI raids, logs "enough looted. Leaving map." and walks to the map edge.
9. The mod raises the order by `order_gain` and restarts the timer if the order is still below `threshold`.

Order of steps 2 to 4: check first, remove after. If a step after the removal fails (for example the spawn), the mod logs an error. It does not put the weapons back (proposed, owner to confirm).

## Weapon item ids

The config holds the list `rebellion_weapon_ids`. Known ids from the extracted `DT_Items` table (it may be older than the game): 133 spears, 271 shields_large, 270 shields_small, 177 weapons_sidearms, 178 weapons_polearms, 205 warbows, 206 crossbows, 163 gambesons (armor), 164 mail_armor, 273 militia_helmets_resource, 288 and 289 mercenary helmets. `spearMilitia` gear is 163, 133, 271, 273 (gambeson, spear, large shield, helmet; `docs/wiki/concepts/unit-templates.md`). Only 133 and 271 were seen stocked in homes. Spike task 2.1 reads the inventory of homes in real fixtures and completes the list. Until then the default list does not change: `{133, 271, 163, 273}`.

## Loot override state

- Where: a module in `features/raid_behavior` (generic: it knows units and goods, not rebellions). API: `set(unit, goods)`, `get(unit)`, `take(unit)` (get and clear), `clear_all()`, `relink()` (after a load).
- Session key: `unit:GetAddress()`. A body in `Region.corpses` is the same SMUnit object as the live unit (spike-corpse-pit-loot, `body-owner.md`), so the key stays valid when the unit dies. `ItemsLooted` stays on the body. `GetAddress` changes after a load, so it is only the in-memory index.
- Read: the corpse pit pay-out path. When the pit receives a body whose key has an override, the mod adds the override goods to the pit (`addToInventory`) and clears the entry (`take`). Without an override the existing rules apply (Hussite share, or nothing for native raids). The pit storage-limit rules stay.
- Other body loot paths: the mod has none besides the pit pay-out. The game's own plunder (`ItemsLooted`, carried goods) is not changed, so live plunder loot still works.
- A brigand may carry plundered goods (`ItemsLooted`) and have an override. Both stay: the game handles the plundered goods, the mod pays the override.

### Save with ModState

Owner decision 2026-10-24: the map is saved while the unit is alive.

- ModState has no removal and needs registered keys (`mod/shared/ModState/ModState.lua`), so the map uses a fixed set of slots. The feature registers `loot_slot_1` to `loot_slot_<N>` (kind `string`, default empty, N from config `loot_override_slots`, proposed 40: 18 per rebellion squad, room for two rebellions). A slot value uses only the characters A-Z a-z 0-9 `_` `.` `-`. A slot holds one unit: `<unit key>_<good id>-<good id>...` (the stable unit key is below). One Tag name is far below the 1023 character limit. A cleared slot is set to the empty string (overwritten in place, no Tag removed). `set` takes the first empty slot. If all slots are full, `set` logs an error and drops the new entry (the unit then gives the config loot). The mod never writes the Tags array with the bridge.
- `set`, `take` and every drop write the slot at once (`state:set` flushes).
- The limits of spec 24 are respected: the slot Tags are created once, in place, and their count is fixed by N.

### Stable unit key (engine fact, spike task 2.8)

After a load the game builds new SMUnit objects. The entry needs a key that is the same before and after the save. Candidates, in order of preference. None is checked yet ("Not checked yet"):

1. Squad id plus unit index in the squad. Needs: a squad has a stable id or index across a load and the unit order in the squad is kept.
2. A unit name or id property that the game saves.
3. Re-match by squad: save the squad key (for example squad owner pawn, spawn location or squad index) and the list of goods per squad. After a load, give the goods to the living units of that squad in squad order. Units that died meanwhile lose the goods at the end of the list. This is the fallback if 1 and 2 do not exist. It keeps the number of goods per squad, not who carries which one. That is acceptable: every brigand has one item and the pit gets goods per body.

The spike reads these facts in a save and a load of a real run (saved by `save_game`) and writes `notes/`. The design then fixes the key. Until then the slot value format above is provisional.

### Re-link on load

- After a load the mod waits until the player pawn exists (as ModState does) and until the Outlaws squads exist again, then runs `relink()`: it reads all slots, finds the unit of each key (rule above), sets the session index `GetAddress` to the goods, and logs the count of linked and lost entries.
- An entry whose unit is not found at the end of a poll window (proposed: 10 game seconds, config) is dropped and logged. Its slot is cleared.
- Bodies (proposed, owner to confirm): when a unit with an entry dies, the entry stays in its slot and now belongs to the body. Bodies last about 30 game days (archive `2026-10-24-spike-rebel-without-corpses`). The slot stays until the pit pays out the body or the body expires. So a save with a body on the ground keeps the override. The body is found after a load by the same re-link (bodies are in `Region.corpses`). Not checked yet: that a body keeps the stable key after a load.
- Unit leaves the map: the units vanish and the entry is dropped at the next poll (slot cleared). The weapons are not returned to homes.

## Militia

When the player rallies militia, the weapons move from homes onto the soldiers. The 18-weapon check must not be dodgeable this way. Unknown engine facts (spike task 2.2): can the mod read the equipped weapons of a rallied militia unit (`SMUnit:GetEquippedID` slots), and remove them (unequip or consume calls)? Do the weapons go back to homes when the militia is dismissed?

Fallback if removal from equipped units is impossible (proposed, owner to confirm): count the equipped weapons of rallied militia units of the rebelling region toward the 18, and remove only as many as needed from homes. If homes plus equipped weapons are below 18, the rebellion is blocked as in step 2. If even reading equipped weapons is impossible, the rebellion is blocked while militia is rallied in the region, and a telemetry event says so.
If removal is possible: remove from equipped units first (proposed), then from homes.

## Corpses

The spike `spike-rebel-without-corpses` (running) checks if killed families leave bodies and if there is a removal without a body. Task 1.6 uses its result, for example: remove the families in the way that leaves no body, if it exists. The implementation does not wait for the spike.

## Known facts (`notes/rebel-noai-findings.md`)

- Fixture `playtest-noai` (no AI opponents): the squads raid at once. The first building burns after 37 to 108 game s, "enough looted" shows after 108 to 202 s, the squads reach the map edge after 268 to 312 s. 3 to 5 buildings burn.
- Fixture `base`: the squads waited about 500 s at an AI waypoint near (-31000,-22500). The likely cause is a neighbour AI lord army. Not proven.
- Loot of goods comes only from `raid_behavior` plunder. Not verified for Outlaws squads.
- Squad removal at the map edge is not verified.
- Militia (`spike-militia-weapon-rebellion`): `addMilitiaSquad` registers villagers. Homes stock one spear (133) and one large shield (271) per militia man. `consumeGoodNoCheck` on homes removes them. `turnToBandit` does not change the side.

## Decisions

- The loot override map is saved with ModState (owner, 2026-10-24).
- The militia fallback and the camp removal wait for the spike `spike-militia-corpses-and-camp-removal`.
- Reuse `homeless_rebel` (proven). No new engine call for the spawn.
- Keep `spawnBanditCamp` only to create the pawn.
- Config keys stay in the `bandits` table of `Scripts/config.lua`.
