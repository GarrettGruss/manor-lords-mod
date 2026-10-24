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

The config holds the list `rebellion_weapon_ids`. Known ids: 133 (spear), 271 (large shield), 163 and 273 (other gear of `spearMilitia`, `docs/wiki/concepts/unit-templates.md`). Homes may hold other weapon and armor goods. Spike task 2.1 reads the inventory of homes in real fixtures and completes the list. Until then the default list is `{133, 271, 163, 273}`.

## Loot override state

- Where: a module in `features/raid_behavior` (generic: it knows units and goods, not rebellions). API: `set(unit_key, goods)`, `get(unit_key)`, `take(unit_key)` (get and clear), `clear_all()`.
- Key: `unit:GetAddress()`. A body in `Region.corpses` is the same SMUnit object as the live unit (spike-corpse-pit-loot, `body-owner.md`), so the key stays valid when the unit dies. `ItemsLooted` stays on the body.
- Read: the corpse pit pay-out path. When the pit receives a body whose key has an override, the mod adds the override goods to the pit (`addToInventory`) and clears the entry (`take`). Without an override the existing rules apply (Hussite share, or nothing for native raids). The pit storage-limit rules stay.
- Other body loot paths: the mod has none besides the pit pay-out. The game's own plunder (`ItemsLooted`, carried goods) is not changed, so live plunder loot still works.
- Lifetime: an entry is cleared at pay-out. When the squad leaves the map the units vanish and their goods are lost. The mod clears entries of units that no longer exist at the next poll. The weapons are not returned to homes.
- Save and load: the map is not saved in this change (addresses change at load). After a load the map is empty and the brigands give the normal loot. Open question for the owner.
- A brigand may carry plundered goods (`ItemsLooted`) and have an override. Both stay: the game handles the plundered goods, the mod pays the override.

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

- Reuse `homeless_rebel` (proven). No new engine call for the spawn.
- Keep `spawnBanditCamp` only to create the pawn.
- Config keys stay in the `bandits` table of `Scripts/config.lua`.
