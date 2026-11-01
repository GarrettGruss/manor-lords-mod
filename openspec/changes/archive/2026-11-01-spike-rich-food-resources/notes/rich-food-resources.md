# Rich game, berries, fish and mushrooms (spike #548)

Runs (slot 1, fixture base, map Jagged_Cliffs, read only, no save call): `rf-food2` (node table), `rf-hover`, `rf-hover2`, `rf-hover3` (tooltips by real mouse), `rf-values`, `rf-names`, `rf-table`, `rf-deep` (region data), `rf-animals`, `rf-animals2` (game node). Probe: `harness/scenarios/probe_region_resources.py` (steps `food`, `foodhover`, `animals`; env `HARNESS_LOCS` limits the hover). Run `rf-hover` hit the 300 s limit after 11 nodes; hover2 and hover3 finished the rest. Saves were backed up first (`backups/saves-20261101-rich-food`).

## Answer

| Resource | Rich detectable in Lua? | How |
|---|---|---|
| Berries | yes | Sum of `capacity` over `resourceClumps` of the `ResourceNode` >= 130 |
| Fish and eels | yes | Same, sum >= 385 |
| Mushrooms | yes | Same, sum >= 122 |
| Game | no | Only the tooltip max (28) shows it. Config table. |
| Rich soil | no | No flag found. Owner rule: assume flax as the second rich resource. |

## Where they are stored
- Berries, fish, eels and mushrooms are `ResourceNode` actors with `resourceClumps` (`Resource_Berries_C` 8 clumps, `Resource_Fish_C` 11 or 6, `Resource_Eel_C` 6, `Resource_Mushrooms_C` 16). The node decal has no material (size 128).
- The tooltip on the node is `Name (amt/capacity)`, and `capacity` is the sum over clumps (checked: 130, 134, 165, 385, 390, 122 match the node sums of run `rf-food2`).
- A rich node adds the line `<img id="RichDeposit"/> Rich Resource`. Rich and poor differ only in the capacity: rich nodes have about 2.5x the capacity of poor ones.
- Game: `ResourceNode` with decal material `deerDecal_Mat`, size 4500, scale 1, no clumps. No animal actor class was found (11 class names tried, 0 objects). The node and engine have no count or max property. The tooltip shows `Wild Animals (n/max)`.
- Region: `getRegionByPos` on the decal position (as for ore).

## Tooltip evidence (rich lines)
- Berries (-56920, 71253) Wilde Wand: "(5/130) Rich Resource". Berries (6618, -7496) Rangbachau: "(6/134) Rich Resource".
- Fish (58196, 56910) Obere Wiese: "(269/385) Rich Resource". Eel node (64315, -25914) Kleine Nolle: "Shoal of Fish (390/390) Rich Resource".
- Fish (-32420, 53753) Wilde Wand: "(165/165)" no rich line.
- Mushrooms (58120, -72286) Hochweg: "(0/122) Rich Resource". Mushrooms 54, 62, 45: no rich line.
- Game Riesenbuckel (-33227, -40759): "Wild Animals (17/28) Rich Resource". Game Hochweg 12/16, Krumme Leite 14/18, Rangbachau 17/17: no rich line.
- Not hovered (tooltip text empty twice): berries Riesenbuckel (-78727, -75759), capacity 53. It is poor by the capacity rule.

## Rich soil
Hochweg is rich in soil according to the owner. Region data of all 7 regions: properties identical, `hasWeakFertility` true, `getCropTypes` [1,3,2,7,15] in all, `getPredictedHarvestForGoodType` 0, `GetEnviromentProportions` gives 6 ratios with unreadable keys (Kleine Nolle: empty), `GetAffinitiesConnectedWithEnvironment` fails through the bridge. No flag separates Hochweg. Time-boxed: not detectable.

## Region table (test map)
Rich = ore decal 5000, or capacity rule, or tooltip "Rich Resource".

| Region | Ore, stone, salt | Game | Berries | Fish | Mushrooms | Soil | Rich count |
|---|---|---|---|---|---|---|---|
| Wilde Wand | iron | no (no node) | rich (130) | poor (165) | no node | unknown | 2 |
| Hochweg | none | no (12/16) | no node | no node | rich (122) | rich (owner) | 1 + soil = 2 |
| Obere Wiese | clay | no node | no node | rich (385) | poor (54) | unknown | 2 |
| Krumme Leite | stone, salt | no (14/18) | no node | no node | poor (62) | unknown | 2 |
| Riesenbuckel | salt | rich (17/28) | poor (53, inferred) | no node | no node | unknown | 2 |
| Kleine Nolle | clay | no node | no node | rich (390, eel) | poor (45) | unknown | 2 |
| Rangbachau | stone | no (17/17) | rich (134) | no node | no node | unknown | 2 |

Hochweg is the known positive check: rich mushrooms confirmed, the owner's rich soil is not readable.

## Item ids (DT_Items, vanilla)
- Berries 171. Mushrooms 279. Carp 30, Eel 32. Flax 11 (rich soil).
- Game: the hunting camp (`buildingStats` row 14) lists 330 SmallGame (100) and 9 in `averageProduction`. Ids 147 meat, 331 Venison and 2 Stag Carcass also exist. The good a hunter really delivers was not run in a game. Use 330 as the default.
- Fish: the Fisherman's Hut (row 59) lists 30 and 32.

## Recommendation
- Ore, stone and salt: decal size (earlier spike).
- Berries, fish and mushrooms: at the first tribute tick, per node sum `capacity` of `resourceClumps` and compare with the thresholds (berries 130, fish 385, mushrooms 122). Then `getRegionByPos`. Keep the thresholds in a feature config.
- Game: config table `rich_game = { ["Riesenbuckel"] = true }` keyed by `getRegionName()`.
- Rich soil (owner rule): not detectable, so a region with only 1 detected rich resource assumes the second is rich soil and pays flax (id 11). Hochweg is such a region (1 mushrooms + soil). With the data above only Hochweg has 1; all others have 2 without soil.
- Add a config override for Hochweg-like exceptions.

## Not verified
- Thresholds on other maps and new games. The sample has 2 or 3 values per kind.
- Riesenbuckel berries tooltip. Berries and mushrooms capacity change with the season ("Seasonal (Shrinking)"): the capacity read may differ in another season. Read once and cache.
- Which good a hunter camp really yields.
- Whether game and rich soil can be read in another way (animal spawn data in the map, farm plot tooltip).
