# AdaptiveOrigins 1.1 (inspection note)

Date: 2026-10-11. Source: `C:\Users\garre\Downloads\AdaptiveOrigins 1.1 368 1.1 2026-09-13T16-11Z KHNI4i06G`. Nothing was run.
Files: `enabled.txt`, `README.txt`, `scripts/config.lua` (11 KB), `scripts/main.lua` (10 KB). Comments are in Russian. Group C by assignment; it is an economy mod, not military. Read for technique.

## What it does for the player
The Origin the player picked (Food, Trade, Mining, Military, Metropolis paths) grows with the settlement level 1..6. Bonuses scale from x0.75 to x1.25 (economy x1.10 at most). Some perks switch on at higher levels. Drawbacks deepen from -5% to -30%. The flat import fee falls from 7 to 3. (README.txt)

## How it works
- It edits global settings objects (class default objects) with `:Add(key, value)` on their map properties (main.lua:15-24, 118-123):
  - `/Script/ManorLords.Default__YieldModifierSettings` field `YieldModifierValues` (float map),
  - `/Script/ManorLords.Default__ProductivitySettings` field `ProductivityModifierPercentValues` (int map, rounded),
  - `/Script/ManorLords.Default__PerkSettings` field `PerkEffectBonuses` (float map),
  - `/Script/ManorLords.Default__TradeSettings` field `importFee` (set directly, main.lua:170-175).
  Keys are effect ids (yield 1..10, prod 1/3/4/5, perk 17, 38, 56, 59, 60, 65, 66, 68, 70, 78, 81, 82, 83, 86). The id map is in config.lua comments.
- The level comes from `Region:getNumFamiliesOfLv` per settled region, a ladder table and an average (main.lua:31-97), same code as AdaptiveEnemies.
- Timing: first apply 6 s after load (`ExecuteWithDelay(6000)`), again after `PawnCPP:playCinematicSequence`, then `LoopAsync(applyIntervalMs 15000)` (main.lua:187-206). A test hotkey Ctrl+Shift+F12 forces a level (off by default).
- It does not change which effects an Origin has. It only changes numbers in shared maps. The author says effect values are read live by the game.

## Game version and signs it is stale
Target 0.8.104. Against the 0.8.111 jmap, all names exist: the four CDOs, `YieldModifierValues`, `ProductivityModifierPercentValues`, `PerkEffectBonuses` (all MapProperty), `TradeSettings.importFee` (UInt32), `Region:getNumFamiliesOfLv`. No stale name found. Effect ids were not checked (they are data, not names).
Side find: `Region.settlementLevel` (Int) and `Region.isSettled` (Bool) exist in 0.8.111 and are not used.

## Risk review
Pure Lua, no file or network access. It changes shared global tables for all pawns, including the AI lords. If another mod writes the same keys, the two fight. License: none given ("100% original standalone code").

## Lessons for us
- Raids and enemy scaling: none directly.
- Technique that matters: a mod can change game rules at run time by writing map entries of a `*Settings` CDO (`obj.MapField:Add(key, value)`). This works without a pak and without `FindRow`. Our own check list should look for `Default__*Settings` classes that hold raid or combat numbers. `Default__RaidSettings` has only `defaultRaidIDs` and `eliteRaidIDs` (spike S1). The jmap has other settings classes that were not searched in this note.
- Unit stats: `PerkSettings.PerkEffectBonuses` key 60 is "forest combat" and key 78 is a castle cost discount (config comments). The perk map may hold other combat bonuses. A spike could list which perk ids touch battle.
- Level scaling: if we scale invasions by realm size, read `Region.settlementLevel` (jmap) instead of the family ladder. Verify it in the game first.

## Test idea for the harness
Scenario `settings-map-write`: read `Default__PerkSettings.PerkEffectBonuses` key 60 through `HarnessDataTable`-like read, write 0.25 with `:Add`, read back, check the effect shows in a battle in the forest (range assert), restore. It shows if perk maps are a safe route for combat balance in A/B tests.
