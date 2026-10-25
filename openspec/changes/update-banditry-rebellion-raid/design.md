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
3. `just_die` the 18 camp Brigands and hide their bodies (`SetActorHiddenInGame(true)`, `Region.corpses:Empty()` if needed). Both are safe in the spike.
4. Demolish the camp: `SMBuildingMaster:demolish(true)` on the camp (encampment, bType 100). `demolish()` without the argument is refused, and `canBeDemolished()` is false. Spike result: parts went 17 to 0, the master was gone in about 10 game s, the pawn survived, and the game did not respawn the camp in 28 game days.
5. Log each step. Fail loudly if a step fails.

It is called (a) at game start and after each load, (b) as a guard before each rebellion. Not verified: pawn survival over save and load (task 2.10), a second `spawnBanditCamp` after a removal, and later bandit raid behavior with a pawn that has no camp.

## Weapon item ids

The config holds the list `rebellion_weapon_ids`. Default: all known ids from the extracted `DT_Items` table: 133 spears, 178 polearms, 177 sidearms, 205 warbows, 206 crossbows, 271 large shields, 270 small shields, 163 gambesons, 164 mail armor, 273 militia helmets, 288 and 289 mercenary helmets. Only 133 and 271 were seen stocked in homes. Spike task 2.1 reads the home inventories in real fixtures and checks the list.

## Loot override state

- Where: a module in `features/raid_behavior` (generic: it knows units and goods, not rebellions). API: `set(unit, goods)`, `get(unit)`, `take(unit)` (get and clear), `clear_all()`, `relink()` (after a load).
- Session key: `unit:GetAddress()`. A body in `Region.corpses` is the same SMUnit object as the live unit (spike-corpse-pit-loot), so the key stays valid when the unit dies. `GetAddress` changes after a load, so it is only the in-memory index.
- Read: the corpse pit pay-out path. When the pit receives a body whose key has an override, the mod adds the override goods to the pit (`addToInventory`) and clears the entry (`take`). Without an override the existing rules apply. The pit storage-limit rules stay.
- The game's own plunder (`ItemsLooted`, carried goods) is not changed.
- An override on a body ends when the body is paid out or disappears (about 30 game days). Owner accepted.

### Save with ModState

- ModState has no removal and needs registered keys (`mod/shared/ModState/ModState.lua`), so the map uses fixed slots. The feature registers `loot_slot_1` to `loot_slot_<N>` (kind `string`, default empty, N from config `loot_override_slots`, default 200). ModState limit facts (`docs/wiki/concepts/mod-commands-and-state.md`): an entry is under 1024 characters, 1000 entries were tested. A slot value uses only A-Z a-z 0-9 `_` `.` `-`. A slot holds one unit: `<unit key>_<good id>-<good id>...`. A cleared slot is set to the empty string. `set` takes the first empty slot. If all slots are full, `set` logs an error and drops the new entry (the unit then gives the config loot). The mod never writes the Tags array with the bridge.
- `set`, `take` and every drop write the slot at once.

### Stable unit key (spike task 2.8)

After a load the game builds new SMUnit objects. The entry needs a key that is the same before and after. Candidates, in order of preference ("Not checked yet"):

1. Squad id plus unit index in the squad.
2. A unit name or id property that the game saves.
3. Re-match by squad: save the squad key and the goods per squad. After a load, give the goods to the living units of that squad in squad order. This is the fallback.

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
