# Rich deposits per region (spike #546)

Runs (slot auto, fixture base, map Jagged_Cliffs, read only, no save call, paused game): `rr-names`, `rr-deep`, `rr-decal`, `rr-hover`, `rr-sweep`, `rr-table`. Probe: `harness/scenarios/probe_region_resources.py`. The save folder was backed up first.

## Answer: yes, for ore and stone deposits and for game. Not for berries, fish and farmland.

### Where deposits are stored
- Each deposit zone is a `ResourceNode` actor (35 on the map). The array `RTSGameManager.deposits` is empty and `DepositDecal` has no objects (earlier spike #342).
- The node component `ResourceZoneDecal` (a `DecalComponent`) tells the kind and the richness. Call `GetDecalMaterial()` on it and `DecalSize` is a property.
- Kind by material name:
  - `depositMaterial` = iron ore
  - `depositMaterial_Clay` = clay
  - `depositMaterial_Salt` = salt
  - `depositMaterial_Stone` = stone
  - `deerDecal_Mat` = game (wild animals)
- A node with `resourceClumps` (class `Resource_Berries_C`, `Resource_Fish_C`, `Resource_Mushrooms_C`, `Resource_Eel_C`, `Resource_Stone_C`) is a gatherable patch. Its decal has no material (`<invalid>`) and size 128.

### Rich or poor
- `ResourceZoneDecal.DecalSize.X` is 5000 for a RICH deposit and 4000 for a POOR ore deposit (game decals are 4500).
- Proof (tooltip on the real mouse hover, `WhiteTooltipRT.Text`):
  - Iron 5000 at (-28920, 74753): "Iron (Surface Deposit: 1192) / Rich Resource / Endless Underground Reserves".
  - Clay 5000 at (61696, 28910): "Clay (Surface Deposit: 1178) / Rich Resource / Endless Underground Reserves".
  - Stone 5000 at (-16233, 23213): "Stone / Rich Resource / Endless Underground Reserves".
  - Clay 4000: "Clay (118)", "(117)", "(115)", "(116)". Iron 4000: "Iron (119)", "(116)". No rich line.
- Not hovered, but the same size rule: salt 5000 at (-30233, 16213) (the pit tooltip hid it) and (-33227, -65259), clay 5000 at (69328, -1837). The salt in Nusslohe was shown as rich in the earlier spike.
- The decal size is a rule found on this map (all 22 deposit nodes fit it). It is not a documented flag. Check it again on another map.
- No reflected field holds the deposit amount, the rich flag or "endless". The tooltip is the only place for the amount.

### Deposit to region
- `RTSGameManager:getRegionByPos(Vector, true)` returns the region object. Pass the decal world position (`K2_GetComponentLocation`) as `{X=, Y=, Z=}`. It worked for all 35 nodes (run `rr-table`).
- Region name: `region:getRegionName()` (for example "Obere Wiese"). The object name (`hofstetten`) is the level actor name.

### Good ids (DT_Items, vanilla)
| Deposit | Good id | Name |
|---|---|---|
| iron | 14 | Iron Ore |
| clay | 146 | Clay |
| salt | 145 | Salt |
| stone | 27 | RoughStone (the quarry output). Id 15 is Rubble (the fieldstone patches). |
| flax (farm second) | 11 | Flax |
| game | 147 meat, 331 Venison, 2 Stag Carcass, 330 SmallGame | check which good the hunter yields before use |
| berries | 171 | Berries |
| fish | 30 Carp, 32 Eel | |

### Table (test map Jagged_Cliffs, 7 regions)
Rich = decal size 5000. Poor ore deposits are listed in brackets.
| Region (name, actor) | Rich ore and stone | Game | Poor ore (not counted) | Rich count |
|---|---|---|---|---|
| Wilde Wand (Eichenhau) | iron | no | clay | 1 |
| Hochweg (Goldhof) | none | yes | iron, clay | 0 |
| Obere Wiese (hofstetten) | clay | no | iron | 1 |
| Krumme Leite (immenreuth) | stone, salt | yes | clay | 2 |
| Riesenbuckel (Nusslohe) | salt | yes | none | 1 |
| Kleine Nolle (selbitz) | clay | no | iron | 1 |
| Rangbachau (waldbrand) | stone (clump node with a 5000 decal) | yes | iron, clay | 1 |

Notes:
- "Rich" for stone in Rangbachau: the node at (6618, 3004) holds 8 `Resource_Stone_C` and a 5000 decal. It was not hovered (the sweep stopped before it). The earlier stone node in Krumme Leite was hovered and is rich.
- Game (deer decal, size 4500) has no rich flag. All tooltips say "Wild Animals (n/m), Teeming". Treat game as a normal deposit, or leave it out of the rich rule.
- Berries, fish, eels and mushrooms are clump patches (`Resource.amt`, `capacity`). They have no rich flag.
- Fertile farmland: `Region:hasWeakFertility()` is true in all 7 regions, so it does not separate them. `Region:GetEnviromentProportions()` returns 6 unnamed ratios per region (a biome mix). `getPredictedHarvestForGoodType(good)` is 0 (no farms). No rich-farmland flag was found.

### Cases for the owner rule
- Regions with 2 rich deposits: 1 (Krumme Leite). With 1: 5. With 0: 1 (Hochweg).
- A region with 0 rich deposits needs a rule (for example two farmland goods, or no tribute). That is an owner decision.

## Fallback (config table)
Not needed for ore and stone: read it live. A config override is still useful for a map that breaks the size rule or for regions with 0 rich deposits:
`rich_deposits = { ["Obere Wiese"] = { "clay" }, ... }` keyed by `getRegionName()`. To fill it: run `probe-region-resources` with `HARNESS_PROBE=table` and `HARNESS_PROBE=sweep`, read the decal sizes, and confirm one or two by hover.

## Recommendation
- Read live at the first tribute tick, and cache per region: `FindAllOf("ResourceNode")`, then `ResourceZoneDecal` -> `GetDecalMaterial():GetName()` and `DecalSize.X`, then `getRegionByPos`. Rich when `DecalSize.X >= 5000` on a node whose material name starts with `depositMaterial`.
- Use a config table to override the live result.
- Decide the rule for regions with fewer than 2 rich deposits, and for farmland richness (no flag exists: use a config list of regions or a threshold on `GetEnviromentProportions`).

## Not verified
- Decal size 5000 = rich for salt and for the Rangbachau stone node (no tooltip read).
- The size rule on other maps and in a new game.
- How tooltip `Surface Deposit` changes for 5000 nodes with no mine (it dropped 1 per day with a mine, #342).
- Which good a hunter yields for the game deposit.
- The calls were made while paused; a running game was not needed.
- The real mouse was used for the hover (lock `os_input_lock` held; slot auto).
