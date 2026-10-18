# Part B: war wagon

Date: 2026-10-18. Issue #178. No game-owned actor was destroyed. The probe destroyed only its own actors.

## Search (class dump `jmap` and pak names)
- Native classes: `SMSiegeUnit` (subclass of `SMUnit`, no own properties, no instance in the world), `Obstacle` (Actor, no properties, none in the world), struct `Obstacle2D` (no reflected fields).
- Path blocking data: `SpatialComponent.Obstacles` (array of `Obstacle2D`) on the game manager. Only building commits add entries (spec 14).
- `SMUnit` functions: `equipTradeWagon`, `isWagonEquipped`, `getEquippedWagon`, `cartLoadingEquipGood`. Item 254 `tradingWagon` has slot Shield and no `VAMP_Variations`.
- Blueprint classes: `Resource_BigCart_C` and `Resource_TimberCart_C` (meshes `work_handcart_static` and `SM_MERGED_BP_tradingWagon_staticResource`), `Resource_Handcart_C`, `Resource_Ladder_C`. Building classes `BM_FoodCart`, `BM_FirewoodCart`, `BM_SiegeCamp` are not loaded in the test save. Meshes: `FantasyVillage/Meshes/SM_Wagon01` to `03`, `horse_harness_wagon`. No ballista, catapult, cannon or battering ram assets exist.

## Stand-in tests (order of the spec)
1. Spawned cart actor that blocks movement.
   - Scenario `probe-cart-actors` (run `20261018-113333-29cc`): `Resource_BigCart_C`, `Resource_TimberCart_C`, `Resource_Handcart_C`, `Resource_Ladder_C` and `Obstacle` spawn and destroy without a crash. The `BM_*` classes are not loaded.
   - Scenario `probe-cart-block` (runs `20261018-113456-fea0`, `20261018-114807-9ebb`, `20261018-114938-e95b`, `20261018-115120-42e5`): the path obstacle list (`path_state`) is 620 before and 620 after 5 props. Pathfinding does not know the carts. No unit blocking was shown. The movement track was inconclusive: the squads moved little in 14 wall seconds, also in the control run.
   - Verdict: a spawned cart is a mesh only, like the free wall of spec 14. BLOCKED as a blocker.
2. Placeable obstacle or palisade. Not tested again. Spec 14: the planner wall blocks, the free wall does not, and no Lua call adds obstacle entries. `Obstacle` actors spawn but add no entry (620 stays). A real blocker needs a built wall, which is fixed, not mobile.
3. Squad with a wagon role. PROVEN to spawn and fight.
   - Pak `warwagon`, row `warWagon` (6 units, item 360 with def 60 and block 60, Speed 0.4). Spawn: run `20261018-115406-6f39` (mean def 53.3, block 50).
   - Fight: 6 units against 18 Brigands, run `20261018-115541-0937`: 1 casualty, all 18 bandits died. One run, not a statistic. The run is marked failed only because the scenario rule needs 10 start units.
   - `equipTradeWagon` on a unit of a spawned squad (scenario `probe-wagon`, run `20261018-113236-e531`): the call returned without error. The answers of the functions cannot be read through the command (out value). No wagon was visible in the screenshot (squad far away, game paused). Inconclusive.

## What moves with an army, blocks pathing, crashes
- Moves with an army: only a normal squad. A wagon-role squad moves, holds and fights like one. No movable vehicle actor was found.
- Blocks pathing: no spawned actor. Only native building obstacles.
- Crashes: none in these runs. Known crash from spec 14: emptying `SpatialComponent.Obstacles`. Not repeated.
- Visual: item 254 has no mesh. A wagon look needs a Blueprint or mesh pak (spec 21).

## Verdict
War wagon as a vehicle: BLOCKED. Best stand-in: a small squad with high def and block and a slow item (`warWagon`). It spawns and fights. It does not shelter archers and does not block movement.

## Spike code (generic, no mod name)
- `HarnessBattle` commands `unit_probe` (allow-listed no-parameter calls), `prop_spawn`, `prop_clear` and `squad_positions`. HarnessActions version 56.
- Hidden scenarios: `probe-custom-unit`, `probe-wagon`, `probe-cart-actors`, `probe-cart-block`.
- `squad_positions` reads `SMUnit.realPos`. `K2_GetActorLocation` of a unit stays at the spawn point.
