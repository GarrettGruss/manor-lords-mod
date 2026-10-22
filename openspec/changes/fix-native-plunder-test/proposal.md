## Why

Issue #373 (from #337): the test scenario `raid-behavior-native-plunder` fails on `main`.

- The 18 Brigands now lose their fight with the village defenders. The raid ends `destroyed`, so the native leave line never appears, and the spec scenario asks for it within 20 game days.
- The tracker counts dead raiders as living for some days. The census shows 0 bandits while the tracker shows 1 to 4. This breaks the rule that the living count equals the game unit count.

Owner decision (2026-10-21): the 20 day limit can be omitted. The goal of the test is that the mod tracks a native raid correctly and leaves it alone, whatever the end of the fight.

## What Changes

- The spec scenario "A one-squad native raid" no longer has a day limit. The raid may end `left` or `destroyed`. The native leave line is required only when the raid ends `left`.
- The tracker counts a raider as living only while the game unit census still counts it. A unit that is still in the `SMUnit` list but not in the census is gone.
- The test scenario `native_plunder.py` follows the new spec scenario. It keeps a safety cap on game days so that a run ends.

## Capabilities

### Modified Capabilities

- `mod/raid_behavior`: the requirement "Every spawned raid is tracked".

## Impact

- `mod/InvasionMod/Scripts/features/raid_behavior/` (tracker: `world.lua`, `rules.lua`).
- `mod/InvasionMod/scenarios/raid_behavior/native_plunder.py`.
- `harness/tests/test_fakegame_raid_behavior.py`.
