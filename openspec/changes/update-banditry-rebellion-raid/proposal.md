## Why

Issue: #480. Owner decisions 2026-10-24 (rounds in gate 1 PRs #481, #485, #488, and this follow-up). The camp outcome of `update-banditry-bandit-camp` (18 families leave, one camp of 18 Brigands far away) does not hurt the village. The spike `rebel-noai` (`notes/rebel-noai-findings.md`) showed that squads of the bandit pawn "Outlaws", spawned at the homes of removed families, raid the village at once in fixture `playtest-noai`, burn buildings, log "enough looted" and leave the map. That is the rebellion the owner wants. The village pays for it: the rebels take the weapons and armor of the families that rebel, and the player can win these goods back by killing the brigands.

## What Changes

- The banditry outcome becomes a rebellion. `rebellion_families` (default 6) families leave, and `rebellion_squads` (default 1) Brigands squad (18 units) of the pawn "Outlaws" spawns at the home of the first removed family (`HarnessBandits.homeless_rebel`, mode `home`, `spawnArmy`). The native Outlaws AI raids the village, logs "enough looted" and leaves the map.
- Family selection (new). A valid family is a family whose home holds at least one weapon or armor item (an id in `rebellion_weapon_ids`). The mod picks `rebellion_families` valid families AT RANDOM (not the best armed). If fewer than `rebellion_families` valid families exist, NO rebellion happens: an unarmed village never rebels. The timer stays expired, the mod retries on the next tick and logs the telemetry event `rebellion_blocked`.
- Goods (new). The mod takes ALL weapon and armor goods from the homes of the chosen families (`consumeGoodNoCheck`). These goods become the loot overrides of the spawned brigands, spread over the 18 units. The brigands' visible gear does not match these goods (owner accepted). The loot override is how the player recovers the goods.
- Order of steps. Ensure the Outlaws pawn, find the valid families, pick, take the goods, kill the families (`just_die`) and hide their bodies, spawn the squad at the first home, record the loot overrides. If the spawn fails after the removal, the mod returns the goods to the homes and logs the error.
- Outlaws init (new module). A separate module with an idempotent `ensure_outlaw_pawn()`. If the Outlaws pawn exists, it does nothing. Otherwise it calls `spawnBanditCamp()`, `addPawnRelations`, kills the 18 camp Brigands, hides their bodies and demolishes the camp (`SMBuildingMaster:demolish(true)`). It runs at game start, after each load, and as a guard before each rebellion. This replaces the accepted camp side effect.
- Loot override (new, generic, in `raid_behavior`). A per-unit map to a list of goods, saved with ModState (`loot_override_slots`, default 200). When the body of a unit is paid out at the corpse pit, the pit gets the override goods instead of the config loot. An override on a body ends when the body is paid out or disappears (about 30 game days, owner accepted).
- Militia. Rally and disband cannot be driven from Lua (spike). Killing registered militia returns their home weapons to the storehouse. The requirement "rallied militia weapons still count" stays. Its check is a manual playtest by the owner.
- Config values in the `bandits` table of `mod/InvasionMod/Scripts/config.lua`: `threshold` 25, `timer_days` 60 (was 90), `order_gain` 25, `tick_days` 30 (unchanged), `leavers` renamed `rebellion_families` with default 6 (was 18), new `rebellion_squads` 1, new `rebellion_weapon_ids`, new `loot_override_slots` 200.
- The other order rules stay: manor term +10 plus tech bonus, homeless term -5 per homeless family.

## Open questions (with defaults)

1. Pawn survival over save and load is unverified (task 2.10). Default: `ensure_outlaw_pawn()` after each load repairs a missing pawn.
2. The stable unit key across a load (spike task 2.8). Default: the fallback by squad in `design.md`.
3. Which weapon and armor ids homes stock beyond 133 and 271 (task 2.1). The default list holds all known ids.

## Decisions (owner, 2026-10-24)

- Selection: random valid families (a home with at least one id of `rebellion_weapon_ids`), default 6. Fewer valid families means no rebellion. The mod takes all weapon and armor goods of the chosen homes.
- Default `rebellion_weapon_ids`: 133 spears, 178 polearms, 177 sidearms, 205 warbows, 206 crossbows, 271 large shields, 270 small shields, 163 gambesons, 164 mail armor, 273 militia helmets, 288 and 289 mercenary helmets (from `DT_Items`, extracted table, may be older than the game). Only 133 and 271 were seen stocked in homes so far.
- The brigands' visible gear does not match the goods. The loot override is the recovery. No re-apply of gear with `SMUnit:equip` (it is cosmetic and reverts in about 1 game day).
- Check-first order: the mod finds the valid families before it removes anything.
- Outlaws init is a separate idempotent module, called at game start, after each load and before each rebellion. The mod cannot choose the camp region: the game picks the place.
- `loot_override_slots` default 200 (ModState facts: entry under 1024 characters, 1000 entries tested).
- The loot override map is saved with ModState while the unit is alive. An override on a body ends at pay-out or when the body disappears.
- Militia: the check is a manual owner playtest.

## Impact

- Specs: `mod/bandits` (RENAMED and MODIFIED: the conversion requirement; MODIFIED: the timer requirement; ADDED: family selection, goods, Outlaws init, militia), `mod/raid_behavior` (ADDED: loot override).
- Code (gate 2): a new Outlaws init module in `mod/InvasionMod/Scripts/features/bandits/`, `world.lua` (`M.leave`), `init.lua`, `rules.lua`, `features/raid_behavior` (override map, ModState save, re-link on load, pit pay-out), `mod/InvasionMod/Scripts/config.lua`, tests, test scenarios.
- Risk: the raid may be slow when a neighbour AI army exists. Squad removal at the map edge is unverified. Camp demolition after a load is unverified.
- Overlap: the change `update-spawn-from-map-border` touches the same conversion requirement. Check it on rebase.
