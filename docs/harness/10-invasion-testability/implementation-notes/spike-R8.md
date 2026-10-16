# Spike R8: rebuild cost of a burned building (criterion R8)

Date: 2026-10-10. Game: real game, base fixture. Tools: bridge eval (experiments only), then the commands of `HarnessActions` version 11 (`mod/shared/HarnessBuild`) and the hidden scenario `rebuild-cost`.
Verdict: **the test method works.** The base game has no repair or rebuild price. A rebuild is "demolish the ruin, place the same building again". The new construction site lists the goods it needs, and the harness reads them. The mod can lower them, and the builders then use the lower amount.

## Question
Spike S6 showed that a burned building becomes Rubble (type 75) and that no function or table gives a building cost. Can the cost of a rebuild be read and checked in another way?

## What was found
- A construction site is an `SMBuildingMaster` with `IsConstructed() == false`. Its property `constructionGoods` is an array of entries `{Type, amt}` with the goods that it still needs.
  A finished building has an empty list. Reading `Type` and `amt` of these entries is safe (no crash).
- Dunghill (type 121) site: `constructionGoods` = `[{Type 17 (Planks), amt 4}]`. The build preview in the game says "Construction Cost: 4" and "Not enough goods!" when the stock has no planks.
  With no planks the click placed nothing (3 probe runs). The cost is Planks, not Timber (Timber 78 did not help).
- The goods leave the stock when the builders build, not at the click: planks 40 -> 36 after the site was built (about 3 game days at 8x, 120 game seconds).
- Rebuild: `collapseBuilding()` or `StartFire()` make the Dunghill Rubble (type 75, `typeBeforeChange` 121). A new Dunghill at the same place is refused while the ruin stands.
  After `demolish(true)` on the ruin (also while it still burns) the same spot accepts a new site. The new site needs **Planks 4 again**: the base game charges the full cost for a rebuild.
- Lower cost: writing `amt = 2` on the entry of the site read back as 2. After the build the planks fell by **2** (36 -> 34). So a mod can set a partial rebuild cost by writing the site entries. The mod must do it for each new site (for example when a site appears on the place of a ruin).
- Placing a site needs the real OS mouse (`place_building`, spec 07).
- Other building types were not tried for the cost. Only 121 (Dunghill, 4 planks) and 30 (HitchingPost, free: `constructionGoods` empty).

## Method in the harness
- `HarnessBuild` commands: `building_sites` (buildings with `built`, `rubble`, `burning`, `needs`; counts `built`, `sites`, `rubble` for a type), `ruin_building` (fire or collapse the first built building of a type),
  `demolish_ruins`, `set_site_cost` (lower only, 0 allowed). Actions with the same names in `ctx.actions`.
- Scenario `rebuild-cost` (COVERS R8, hidden, takes the real mouse and focus, about 85 s):
  give 60 planks, place a Dunghill, read the cost (4 planks, only Planks), build it (planks used = cost), burn it (fire), wait until the fire is out, check Rubble (type 75) and no Dunghill,
  demolish the ruin, place again, check that the base rebuild cost equals the full cost, lower the site to half (2), build, check the planks used (2).

## Results
Scenario `rebuild-cost`, real game, 3 of 3 passed: `rebuild-cost-1`, `rebuild-cost-2`, `rebuild-cost-3`. 12 asserts each: full cost 4, planks used 4, rubble type 75, rebuild cost 4, lowered cost 2, planks used 2.

## Not verified
- The "partial" cost itself is a rule of the mod. The scenario proves that a cost can be read, that a rebuild happens, and that a lower cost is charged. It does not test a discount rule, because none exists yet.
- Costs of other buildings, goods of several kinds, and a site that the player places by hand during a raid.
- That the real mod applies the discount at the right moment (when the site appears). The mod has to do this. Then the same scenario can be changed to check the discount.
- The scenario needs the real mouse, so it cannot run in a suite or while a person uses the computer.
