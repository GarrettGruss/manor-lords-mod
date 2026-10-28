# One-off buildings: feasibility

Issue: #521. Facts and evidence: `engine-facts.md` (called "facts" below). Effort: S = under a day of work, M = a few days, L = a week or more, with models and several game runs.

Common cost for every new placeable building (called **B** below): a pak row, a model (Meshy or a vanilla class), a name text row, a way to start placement (card, or a mod menu button that calls `activateBuildingMode`), and effect code in Lua. B is proven except the card (facts, section 1). Build B once, as the first spike.

## Verdicts

| Concept | Verdict | Effort | Main blocker or evidence |
|---|---|---|---|
| Dockyard | Needs a spike | L | Water placement rule and fishing without a node. Row 59 and `BM_SG_FishermansHut` may help. |
| Boatwright | Needs a spike | L | New goods plus "a building makes them from planks" (job link). Trade speed is native. |
| Rathaus | Feasible with pak work | M | B plus Lua effects (silver, influence, happiness). A second Manor function is not possible; use a normal function. |
| Astronomical clock | Feasible with pak work | S | B plus a "needs Rathaus" rule. Depends on Rathaus. |
| Apothecary | Needs a spike | M | Recipe link for a new item (herbs to medicine). Happiness effect is mod-owned. |
| Inn | Needs a spike | M | Merchant visit rate is native. A tavern clone is easy. |
| Cobblestone roads | Not feasible without native code | not rated | Roads are native. Substitute possible (see below). |
| Bath-houses | Feasible with pak work | M | B plus a mod-owned happiness effect. Needs the approval spike. |
| Tournament grounds | Feasible now (menu version) | S, M with a building | Silver spend, approval write, experience write all proven. |

## Dockyard

Needs from the engine: a large building (like the Construction Yard, row 119: 5 worker slots, `bSize` 1), a water placement rule, a water trade post (trade function), and fish gathering without a resource node.

- Large building: a new row with a bigger `Bounds`; the model comes from Meshy. Feasible (B).
- Unlock at town: `settlementLevel` column (facts, section 1). Unknown whether a new id is checked.
- On rivers or lakes: no data column. Native placement check. **Unknown.** Two routes: (a) clone vanilla row 59, which may already carry the rule through its native job 66, and test where the ghost turns white; (b) place the building anywhere and let a mod rule remove it when no water is near. Route (b) needs a water query. No reflected water query was found in the repo notes. `demolish` on a player building is not tested.
- Fishing without a node: row 59 lists fish production (items 30, 32) and the game has no fish deposit asset in use (only `Resource_Fish`). The fish recipe names item rows 319 and 315, which do not exist in the extract. **Unknown** whether the hut works in the shipped game. If it does, the dockyard is a bigger clone of it.
- Water trade post: a trade post is the function `Trader` (row 6, job 48). Water trade needs a new trade route type. Not found in data. Cheapest version: the dockyard gives a mod-owned trade income (`changeSilver` per day, scaled by fish stock or by workers). Lost: real imports and exports by boat.
- Effort L. Spike question: "Can row 59 be placed next to water, and does it make fish with no deposit?" One game run with a pak that sets `bVisibleInUi`, then a place and a 10 game day soak.

## Boatwright

- Needs: a building that turns planks (item 17, from the sawpit) into boats, a new good "boat" and a trade speed effect for the dockyard.
- New item row: proven. Category must be an existing one (for example Construction).
- Recipe link: **Unknown** (facts, section 2). Spike question: "Does a new building row with an existing job id, plus a new item row with `craftingTool` set, produce the item?" The same question blocks the apothecary and guild crafts. Answer it once.
- Effect "speeds trades like horses at trade posts": the horse effect is the upgrade `order_horse` (`DT_Upgrades` 19) on rows 6, 30 and 97. Its effect is native. A mod cannot call it for a boat. **Unknown**: read `TradeSettings` and `Tradepoint` fields for a speed value (spike T below). Cheapest version: the boats are goods that the dockyard "uses up"; the mod adds a daily silver bonus per boat in stock. Lost: real trade speed.
- Dependency: dockyard.
- Effort L.

## Rathaus

- Needs: a large building for a large town (`settlementLevel`, `maxInRegion` 1), a "second manor" that gives income, influence and happiness.
- A second building with the `Manor` function is not wise: `Region.manor` is one object, and the Keep, Palace and gate modules belong to it. Use function `Default` (the Tax Collector row 58 is a manor module with function `Default`).
- Income and influence: `changeSilver` and `changeInfluence` once per game day by the mod, scaled by population. Proven calls (facts, section 3).
- Happiness: a mod-owned write (see bath-houses). Spike A.
- Model: Meshy, or the unfinished Lv3 palace assets as a base (rows 81 to 83 exist; not placeable as is).
- Effort M to L (the model is the largest part).
- Lost against a native building: no native tooltip lines for its effect. A mod tooltip row or a letter can show it.

## Astronomical clock

- Needs: an add-on of the Rathaus, with happiness, influence and silver upkeep.
- Add-on: the game builds manor modules with `isModule`, `moduleCategory`, `placedWithin`, `snapPoints`. That is native and tied to the manor. The cheap version is a separate small building that the mod accepts only when a Rathaus stands (hide the card until then, or remove the building and refund).
- Upkeep: a negative `changeSilver` per day. Proven calls.
- Effort S after the Rathaus.

## Apothecary

- Needs: herbs as input, medicine as output, happiness now, health later.
- Herbs exist as an item (the Forager gathers items 171, 279 and 18; there is a herbs garden asset and the upgrade `herbs_garden`). The id of Herbs is not mapped yet.
- Medicine: a new `DT_Items` row (proven) with `Resources` herbs.
- Recipe link: Unknown (spike R above). Fallback: a host building with an existing job, plus the recipe set by Lua (as for the burgage tailor slot).
- Happiness from medicine: the game has no medicine need. The mod reads the stock of medicine in the region and applies a happiness value from it, and uses up a little each week (`consumeGoodNoCheck`, proven on homes). Spike A for the happiness write.
- Effort M.

## Inn

- Needs: more visits of foreign merchants.
- The building: clone the Tavern rows 37 and 116 (function `Tavern`, job 53). Easy (B). A cloned `Tavern` function may count as an amenity (factor `SatisfiedAmenities` +6 in a live village). Unknown whether a clone counts.
- Merchant visit rate: **Unknown** and probably native. Spike T: read `RTSMultiEngineCPP.tradepoints`, `ForeignMarketSupply` and `TradeSettings`; look for an interval or chance field; find the Lua-reachable spawn for merchant squads. If only native code spawns them, the inn cannot change the rate.
- Cheapest version: the inn gives a mod-owned "visit" event: every N days it adds silver and a few goods, with a letter text. Lost: real merchant units.
- Effort M.

## Cobblestone roads

- Roads are native: the road tool and `RTSMultiEngineCPP.roads`. No data column or enum for a surface. No cobble asset exists in the files.
- A new road type with its own surface and cost: not feasible without native code.
- Substitutes, each Unknown and none a road:
  1. A placeable "paved plaza" building (`isPlaza` column exists) with a cobble model, cost and the Rathaus plus Mason guild rule. It gives a look and a mod effect (happiness or health) but no road.
  2. At run time, swap the road material for a cobble material when the rules are met (a global change of all roads, not per road). Not tried. The repo can change a mesh at run time (`SetStaticMesh`, engine-limits). Material change on the road landscape is not known.
- Dependencies: Rathaus, Mason guild (`guildhalls.md`).
- Effort: not rated; ask the owner whether a plaza substitute is acceptable.

## Bath-houses

- Needs: happiness. Policy 7 "Bathhouse pleasures" exists as `[not implemented]` text and enum `BathhousePleasure` (legacy-16 `policies.md`). So the game plans a native one, but there is no effect or building.
- The building: B, a clone of the Tavern or Church row, or of a well.
- Happiness: a mod-owned approval or public order value (Spike A). Public order is proven; approval is not.
- Health: counts toward the Health metric (`health-metric.md`).
- Effort M.

## Tournament grounds

- Needs: spend personal wealth, a big short happiness boost, a small experience gain for militia and retinue.
- "Personal wealth": the lord treasury (`silver`) or influence. Ask the owner which one. Regional wealth is the town's, not personal.
- Spend: `changeSilver(-n)`. Proven.
- Boost: write approval or public order for N days. Public order proven; approval Spike A.
- Experience: `SMUnit.combatExperience` write for militia and retinue units (proven in test scenario `veterancy`). Strength effect is not measured; ask the owner for a number.
- Menu version (feasible now): a button in the mod menu, enabled when a building of a chosen existing type stands (for example the Archery range, row 40, or the Training camp, row 45) or with no building at all. Pictures: a banner or letter.
- Building version: B, a large open-air model. Effort M.
- Effort: S (menu version), M (building).

## Dependencies

- Dockyard before Boatwright.
- Rathaus before Astronomical clock.
- Rathaus and Mason guild before cobblestone.
- B (new building pipeline) before all except the tournament menu version.
- Spike A (happiness write) before Rathaus, bath-house, tournament and apothecary effects.
- Spike R (recipe link) before Boatwright, Apothecary and guild crafts.
- Spike T (trade fields) before Inn and Boatwright effects.
