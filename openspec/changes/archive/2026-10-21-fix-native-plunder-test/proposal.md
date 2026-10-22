## Why

Issue #373 (from #337): the test scenario `raid-behavior-native-plunder` fails on `main`.

- The 18 Brigands now lose their fight with the village defenders. The raid ends `destroyed`, so the native leave line never appears, and the spec scenario asks for it within 20 game days.
- The tracker counts dead raiders as living for some days. The census shows 0 bandits while the tracker shows 1 to 4. This breaks the rule that the living count equals the game unit count.

Owner decisions (2026-10-21):

- The 20 day limit can be omitted. The test checks that the mod tracks a native raid correctly and leaves it alone, whatever the end of the fight.
- The purpose of `mod/raid_behavior` is to steer the larger Hussite raids, because the game has no native way to raid a player region with units other than Brigands. Requirements that test the game itself, or that serve only native bandit raids, are dropped:
  - the spec scenario "Native plunder" (loot, burned buildings and population of a native raid);
  - the requirement "Bandit squads leave only in a quiet spot";
  - the requirement "The loot of a dead raider goes to the nearest store".

## What Changes

- **Tracking:** the requirement "Every spawned raid is tracked" is replaced by "Every spawned raid is tracked by the game census" (the tool cannot drop a scenario in a MODIFIED block). Its spec scenario "A one-squad native raid" becomes "A Hussite raid": a Hussite raid runs under the baron AI, not the native plunder AI (owner, 2026-10-21). It has no day limit and may end `left` or `destroyed`. The native leave line is no longer checked. The test scenario `carry_caps.py` checks it; `native_plunder.py` is removed. The tracker counts a raider as living only while the game unit census counts it.
- **Native raids:** the mod still does not steer, rout or remove a native raid. The spec scenario "Native plunder" is removed, because it measures the game's AI, not the mod.
- **BREAKING** Bandit squad raids (no lord) are no longer sent home by the mod: no peace, no removal in a quiet spot.
- **BREAKING** The loot of a dead raider is no longer added to the nearest store. It stays with the body (the game's own behavior). The corpse pit change (`spike-corpse-pit-loot`, #360) will give it back through the corpse pit.
- **Purpose:** the Purpose of `mod/raid_behavior` gets this text (a delta spec cannot change a Purpose, so task 4.1 writes it into the living spec before the archive):
  > The raid_behavior feature steers the larger Hussite raids into the player's region, because the game has no native way to raid a player region with units other than Brigands. A Hussite raid runs under the baron AI, not the native plunder AI, so that a raid can bring a mix of units (archers, spearmen, retinue) that a native raid cannot. It also tracks each raid that the invasion feature spawns, keeps the loot of Hussite raids under a cap, lets role raids leave, and guards the player's region.

## Capabilities

### Modified Capabilities

- `mod/raid_behavior`: the Purpose; REMOVED "Every spawned raid is tracked" (ADDED again as "Every spawned raid is tracked by the game census"), "A native raid is left alone" (its rule is ADDED again as "The mod never steers or removes a native raid", without the spec scenario "Native plunder"), "Bandit squads leave only in a quiet spot" and "The loot of a dead raider goes to the nearest store".

## Impact

- `mod/InvasionMod/Scripts/features/raid_behavior/`: tracker (`world.lua`, `rules.lua`), the bandit leave code and the loot return code (`return_loot`) are removed.
- Test scenarios: `carry_caps.py` gets the tracking checks; `native_plunder.py` and `loot_return.py` are removed.
- `harness/tests/test_fakegame_raid_behavior.py`.
- Follow-up: the delta spec of `spike-corpse-pit-loot` modifies "The loot of a dead raider goes to the nearest store". It must become an ADDED corpse pit requirement before that change is archived.
