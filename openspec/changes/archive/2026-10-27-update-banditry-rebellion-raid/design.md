## Flow

1. The banditry timer expires (`timer_days` after the order fell below `threshold`).
2. `ensure_outlaw_pawn()` (see Outlaws init). If it fails, stop and retry on the next tick.
3. Find valid families. A family is valid when its home (`building.Inventory`, bType 3) holds at least one item with an id in `rebellion_weapon_ids`. If fewer than `rebellion_families` (6) valid families exist: stop. The timer stays expired, the mod retries on the next tick (`tick_days`), and logs `rebellion_blocked` (fields: valid families found, families needed). Nothing was removed.
4. Pick `rebellion_families` valid families at random. The village keeps `min_families_left`.
5. Take all weapon and armor goods (ids in `rebellion_weapon_ids`) from the homes of the chosen families: one `building:consumeGoodNoCheck(good)` per item (as `world.plunder` does). Record the goods list and the home of each good.
6. Kill the chosen families (`core.remove_families`, `just_die`) and hide each body (`SetActorHiddenInGame(true)`). Handle `Region.corpses` as the spike found safe (`Empty()` is safe). NEVER call `K2_DestroyActor` on an SMUnit (crash). Do not keep unit references across game time.
7. `homeless_rebel` mode `home` spawns `rebellion_squads` (1) Brigands squad (`spawnArmy`, owner = Outlaws) at the first removed home. If the spawn fails: put the goods back into the homes they came from (`addToInventory`), log an error, and the timer stays expired.
8. Record loot overrides: spread the goods over the units of the squad (18 units). With more goods than units, units get several goods (round robin). With fewer goods, some units get none. Store the map in the loot override state.
9. The native AI raids, logs "enough looted. Leaving map." and walks to the map edge.
10. The mod raises the order by `order_gain` and restarts the timer if the order is still below `threshold`.

The order is check first, remove after (owner accepted). A failure after the removal is only possible at the spawn, and step 7 repairs it. Families killed before a failed spawn are not brought back; only the goods return.

The brigands' visible gear does not match the pantry goods (owner accepted). The loot override is the way the player recovers the goods. The mod does not re-apply gear: `SMUnit:equip` exists but is cosmetic and reverts in about 1 game day (spike `militia-corpses-and-camp-removal`).

## Outlaws init

A separate module `features/bandits/outlaws.lua` with an idempotent `ensure_outlaw_pawn()`:

1. If the Outlaws pawn exists, do nothing and return true.
2. Else call `spawnBanditCamp()` (no arguments). The game picks the place: the mod cannot choose the region. Then `addPawnRelations(pawn)`.
3. The pawn exists now, so `ensure_outlaw_pawn()` returns true at once and a rebellion may go on. The camp cleanup runs on the next polls (`finish_camp_removal`, game time needed). Real-game fact (runs `rb-init-4` and `rb-init-5`, bridge spike): a camp is built by its 18 Brigands. If they die in the same tick, the camp stays unbuilt (`IsConstructed` false) and `demolish(true)` does nothing for good. So the cleanup waits until every new camp is built (`IsConstructed` true, one poll in run `rb-init-6`; after 120 polls it goes on anyway), then `just_die` the 18 camp Brigands (found by the addresses that were new after `spawnBanditCamp`, so rebels are never touched) and hides their bodies (`SetActorHiddenInGame(true)`). Both are safe in the spike.
4. Then demolish the camp: `SMBuildingMaster:demolish(true)` on the camp (encampment, bType 100), called on each poll until the camp is gone (up to 120 polls, then an error is logged). `demolish()` without the argument is refused, and `canBeDemolished()` is false. Real result (run `rb-init-6`): the camp was gone about 80 game s after the pawn was made. Do not read a property of a camp master after the demolish (a bridge read of the destroyed master crashed the game in the spike).
5. Log each step. Fail loudly if a step fails.

It is called (a) at game start and after each load, (b) as a guard before each rebellion. Pawn survival over save and load is verified (run `rb-rt-r1`: the pawn existed after the load and the init did nothing). Not verified: a second `spawnBanditCamp` after a removal, and later bandit raid behavior with a pawn that has no camp.

## Weapon item ids

The config holds the list `rebellion_weapon_ids`. Default: all known ids from the extracted `DT_Items` table: 133 spears, 178 polearms, 177 sidearms, 205 warbows, 206 crossbows, 271 large shields, 270 small shields, 163 gambesons, 164 mail armor, 273 militia helmets, 288 and 289 mercenary helmets. Only 133 and 271 were seen stocked in homes. Spike task 2.1 reads the home inventories in real fixtures and checks the list.

## Loot override state

- Where: a module in `features/raid_behavior` (generic: it knows units and goods, not rebellions). API: `set(unit, goods)`, `get(unit)`, `take(unit)` (get and clear), `clear_all()`, `relink()` (after a load).
- Session key: `unit:GetAddress()`. A body in `Region.corpses` is the same SMUnit object as the live unit (spike-corpse-pit-loot), so the key stays valid when the unit dies. `GetAddress` changes after a load, so it is only the in-memory index.
- Read: the corpse pit pay-out path. When the pit receives a body whose key has an override, the mod adds the override goods to the pit (`addToInventory`) and clears the entry (`take`). Without an override the existing rules apply. The pit storage-limit rules stay. The tech tree law "Strip the Dead" (pit pay-out on or off for the Hussite share) does not gate the override: the override is how the player recovers the goods that the rebels took.
- The game's own plunder (`ItemsLooted`, carried goods) is not changed.
- An override on a body ends when the body is paid out or disappears (about 30 game days). Owner accepted.

### Save with ModState

- ModState has no removal and needs registered keys (`mod/shared/ModState/ModState.lua`), so the map uses fixed slots. The feature registers `loot_slot_1` to `loot_slot_<N>` (kind `string`, default empty, N from config `loot_override_slots`, default 200). ModState limit facts (`docs/wiki/concepts/mod-commands-and-state.md`): an entry is under 1024 characters, 1000 entries were tested. A slot value uses only A-Z a-z 0-9 `_` `.` `-`. A slot holds one unit: `<unit key>_<good id>-<good id>...`. A cleared slot is set to the empty string. `set` takes the first empty slot. If all slots are full, `set` logs an error and drops the new entry (the unit then gives the config loot). The mod never writes the Tags array with the bridge.
- `set`, `take` and every drop write the slot at once.

### Stable unit key (spike task 2.8)

After a load the game builds new SMUnit objects. The entry needs a key that is the same before and after. Decision (verified, run `rb-rt-r1`): the saved key is the squad id plus the index of the unit in its squad at the spawn, and the relink gives the entries of a squad, ordered by index, to the units of that squad in the order of the game (the fallback 3 of the old list). The squad ids stayed the same over the harness save and load (squad 20 before and after), and 15 of 15 entries were linked to units again. The units of a squad are equal, so the match by position is enough. A unit name or id property that the game saves was not needed.

The unit key in memory is the address. A dead unit has `assignedSquadID` 0, so a body is found only by its address, and an entry of a dead unit is kept (marked with the death day) until the pit pays it or 30 game days passed. The pit cannot tell whose body arrived (its count only rises), so a rise of the corpse count by N pays the N dead entries with the oldest death (one body, one entry). A body of a villager can therefore pay the entry of a killed brigand. This is an implementation limit (the game gives no hook on a delivered body). It is listed under "Spec changes" of the pull request for owner review.

### Re-link on load

- After a load the mod waits until the player pawn exists and until the Outlaws squads exist again, then runs `relink()`: it reads all slots, finds the unit of each key, sets the session index, and logs the count of linked and lost entries.
- An entry whose unit is not found at the end of a poll window (10 game seconds, config) is dropped and logged. Its slot is cleared.
- Bodies: when a unit with an entry dies, the entry stays in its slot and belongs to the body until pay-out or body expiry. Bodies are found after a load in `Region.corpses`. Not checked yet: that a body keeps the key after a load.
- Unit leaves the map: the entry is dropped at the next poll. The goods are not returned to homes.

## Militia

Spike facts (`spike-militia-corpses-and-camp-removal`):

- Rally and disband cannot be driven from Lua. A real rally needs the real mouse. `RequestDisbandSquad` and `disbandSquad` do nothing.
- Homes hold one spear and one shield per registered militia man. Killing militia returns their home weapons to the storehouse (not lost). Equip is cosmetic and changes no stock.

The exploit case stays a requirement: rallied militia weapons must still count, so rallying cannot dodge the rebellion. The check is "Manual: owner playtest". The fallback stays as written: only goods that sit in the homes of the chosen families count and are taken. A family whose weapons are on a rallied man still has them in its home (the spike saw no stock change), so the family stays valid. The spike did not test items on the body of a really rallied man.

## Known facts (`notes/rebel-noai-findings.md`)

- Fixture `playtest-noai`: the squads raid at once. The first building burns after 37 to 108 game s, "enough looted" shows after 108 to 202 s, the squads reach the map edge after 268 to 312 s. 3 to 5 buildings burn.
- Fixture `base`: the squads waited about 500 s at an AI waypoint. Likely cause: a neighbour AI lord army. Not proven.
- Killed families leave bodies. Hide is safe, destroy crashes (spike `rebel-without-corpses`).
- Loot of goods comes only from `raid_behavior` plunder. Not verified for Outlaws squads.
- Squad removal at the map edge is not verified.

## Decisions

- The loot override map is saved with ModState (owner, 2026-10-24).
- Reuse `homeless_rebel` (proven). No new engine call for the spawn.
- The pawn is created by the separate Outlaws init module and the camp is removed.
- Config keys stay in the `bandits` table of `Scripts/config.lua`.
