# Guildhalls, advanced crafts and guild recruits: feasibility

Issue: #521. Facts: `engine-facts.md`. Building pipeline B: `buildings.md`.

## Verdicts

| Part | Verdict | Effort | Main blocker or evidence |
|---|---|---|---|
| Guildhall building (one per artisan type) | Feasible with pak work | M for the first, S for each next | B. One row per guild, one model each (or one model with a color change). |
| Requirement "3 of an artisan type" | Feasible with pak work | S | Count with `getBuildingCount(bType, true)`. The refusal is the open part (see below). |
| Income from related artisans | Feasible now | S | Mod-owned `changeSilver` per day, scaled by `getGoodsProducedOver`. |
| Advanced crafts (plate, swords, better clothes and boots, fancier cheese) | Needs a spike | M | Recipe link (spike R) and which items already exist. |
| Mason guild unlocks cobblestone | Not feasible as a road | see `buildings.md` | Roads are native. |
| Guild recruits (plate militia, between militia and retinue) | Feasible with pak work | M | New `DT_UnitTemplates` row. Recruit call with a new template name is Unknown. |

## Guildhall and the requirement

- A guildhall is a normal new building (B), probably with function `Default` and a mod effect.
- Count: the harness already counts buildings by id. The artisan types map to existing rows: blacksmith = Smithy (25), weaver (33), tanner (28), communal oven (26), mason = Stonemasons Station (117), dyer (473), brewery (105), and so on. The row ids come from the extract of `buildingStats`.
- Enforcing "3 of a type": the engine has no hook to refuse a placement (`engine-limits.md`). Options, cheapest first:
  1. Hide the card until the count is 3. Needs a run-time write of `bVisibleInUi` (numbers of the row are written by `HarnessHousing`; the bool write and the card refresh were not tested). Spike C (card).
  2. Let the player place it and remove it with `demolish(true)` plus a refund if the count is below 3. `demolish` on a player building is not tested.
  3. Use `requiredPerks` or `requiredTech` columns with a tech granted by the mod. Data only; Unknown.
- Lost with options 2 and 3: the ghost does not show the rule.

## Income from related artisans

The game has no guild income. The mod pays it: once a day, `changeSilver(k * value of goods produced by the related buildings)`. `ProductionTrackerComponent:getGoodsProducedOver(days)` is reflected (jmap-findings). Item prices are in `DT_Items.Value`. Proven call: `changeSilver`. Not tested here: reading the production tracker through the mod. A small spike inside the first guild change.

## Advanced crafts

- Recipes are data rows in `DT_Items` (`engine-facts.md`, section 2). The columns `upgradesRequiredToCraft` and `techsRequiredToCraft` look like the game's own gate for a recipe. A guild could be an upgrade row in `DT_Upgrades` (`requiresBuilding` column exists) that unlocks the recipes. Unknown.
- Audit first: which advanced items already exist. Plate armor exists in the retinue tier 3 template. Item 293 (armor, needs 6 of item 35) has no craft tool. Swords 177 and 178 exist with tool 264. Check the identity of these rows in the item texts, then decide what is new.
- New goods (fancier cheese, higher-tier clothes and boots): new item rows (proven) with an existing category.
- Which building crafts them: the recipe link (spike R). Cheapest: the guildhall itself is the host, or the matching artisan building gets the recipe row through its `craftingTool`.
- Effort M, mostly the audit and the recipe link.

## Mason guild and cobblestone

The mason guild can unlock a mod rule, but the road type is native. See `buildings.md`, "Cobblestone roads". If the owner accepts a plaza substitute, the mason guild is the requirement for it.

## Guild recruits

- Needs: a militia variant that can wear plate, stronger than militia, weaker than retinue.
- Unit type: a new `DT_UnitTemplates` row, cloned from `spearMilitia` or `retinue_tier1` with plate gear and a `maxSize` (spec 29 proved new rows; wiki `unit-templates.md`). Plate meshes exist (retinue tier 3).
- Gear: a template sets the look and the stats. Stock for militia gear sits in the homes and comes from the storehouse (proven, #482). A mod can put plate into the storehouse with `addToInventory` (proven). `equip` is cosmetic for villagers, so do not use it as the source of gear.
- Recruit call: `PawnCPP:addMilitiaSquad(region, FName)` with a new row name. Unknown. Spike U: add the row, call it, read the squad size and unit roles. Do not read the `Squad` struct. Use the `commandedSquads` count and `SMUnit.assignedSquadID`.
- Native militia limit per region is about 1 squad per 36 people (`native-modding.md`, not checked). Guild squads would count against it, or need their own count.
- Strength between militia and retinue: stats come from the template and gear. Tune with `harness-ab-testing`.
- Experience: `combatExperience` write (proven).
- Effort M.

## Dependencies

- Guild system (the first guildhall) before advanced crafts, recruits and the mason rule.
- Spike R before advanced crafts.
- Spike U before recruits.
- Rathaus before cobblestone (owner list).
