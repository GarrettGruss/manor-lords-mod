# Health metric: feasibility

Issue: #521. Facts: `engine-facts.md`.

## Verdict

Feasible now as a mod-owned metric. Effort M for the metric, its display and one effect. Each source building (fountain, sewer, apothecary, bath-house) has the cost of its own building (`buildings.md`).

## What the engine offers

- No Health metric exists. Nothing in the engine to reuse or to write.
- A mod stores its own number in the save with `ModState` (proven; feature `mod_state`).
- Inputs the mod can read: population (`Region:getNumTotalPopulation`), burgage plots (`getNumBurgagePlots`), settlement level, building counts by id (`getBuildingCount`), stock of goods (`getStockOfGood`). All reflected and used by the harness.
- Display: a row in the approval and public order tooltip (feature `order_tooltip`, custom rows work), a line in the mod menu, or a banner (`HarnessUi`). A new bar in the top bar of the game is not a known technique. The HUD is native UMG, and a pak widget needs a UE cook.
- Effects the mod can apply when Health is low:
  - A happiness or public order penalty (public order write proven; approval write is spike A).
  - A disease event: a letter and `SMUnit:just_die` on some villagers. `just_die` makes bodies and the corpse pit takes them (proven, #360, rebel-without-corpses). Do not call `K2_DestroyActor` on a unit.
  - Slower growth: `Region:GetMonthlyPopGrowthModifiersWithValues` is read-only. No known write. Unknown. Immigration refills about every 3 game days.

## The rules from the owner's list

| Rule | Feasible | How |
|---|---|---|
| Starts at 100 percent | Yes | Default value in ModState. |
| Falls as the city grows | Yes | A formula on population and building counts. Needs a design number. |
| Fountains raise it | With pak work | A new building (B), or the existing wells (rows 21, 114, function `WaterSource`) as a stand-in. No fountain asset exists. |
| Sewers raise it, in very large towns with cobblestone roads | With pak work, partly blocked | The building is B. "Cobblestone roads" cannot be a real road (`buildings.md`). Replace the rule with the plaza substitute, or with the Rathaus and Mason guild. |
| Apothecaries raise it | With pak work | Needs spike R for medicine. |
| Bath-houses raise it | With pak work | B. |
| Large churches raise it | Yes | The large stone church exists (row 120). Count it with `getBuildingCount(120, true)`. |

## Order of work

1. Metric, formula, display and a penalty. No new building. Feasible now. Start here.
2. Wells as stand-in fountains, large churches.
3. New buildings as they arrive.

## Risks

- A design is needed for the numbers (decline rate, source weights, penalties). The owner owns design. Do not write it into `design/mod/`.
- The happiness penalty depends on spike A.
- The game rebuilds tooltip rows each game day. The mod appends them again (as `order_tooltip` does).
