## Context

The current feature offers 3 contracts, the player picks one, and a missed deadline costs influence. Code: `mod/InvasionMod/Scripts/features/liege_contracts/` (`init.lua`, `rules.lua`, `world.lua`, `loader.lua`, `view.lua`). Goods are counted with `region:getStockOfGood` and taken from the stores of the player region (`world.take_goods`: tier 1 stores 6 and 72 first, then the tier 2 stores). Silver is paid with `playerRef.silver = before + amount` (`liege_influence.add_silver`). Goods are added to the first storehouse. A tech point is `tech_picks_earned` in ModState.

## Decisions

1. Three tiers: Small, Medium, Large. Each spring the mod draws 3 different requests from each tier (9 in all). A request and a reward are drawn together into one contract, with the amounts drawn in the table range.
2. The limit per tier per year is `liege_contracts.tier_limits = { small = 1, medium = 1, large = 1 }`. The fulfilled counts reset at each spring.
3. Contracts expire at the start of winter. The offer is cleared then. No penalty. The window then shows the time to the next spring.
4. Delivery source: the same as today (any store of the player region). The stock shown on a card is `getStockOfGood`, which is the same source. Open question 3 in the proposal.
5. The Fulfil button is enabled when stock >= amount and the tier count < limit. The mod checks both again when the click arrives, and refuses with a reason if not.
6. The data file holds the two pools per tier (below). No good id, amount or text is in Lua code.

## Table 1: requests by tier

All amounts are PROPOSED DEFAULTS. The owner tunes them in the data file or config. Item ids are from `DT_Items` (`openspec/changes/archive/2026-10-23-add-scenario-start-kit/notes/item-ids.md`, and the archived notes of m06 and m10). The column "Class" says raw or produced.

Tier 1 and tier 2 goods (open question 2): "tier 1 goods" = raw goods that the land gives with one building (wood, stone, clay, grain, fish, iron ore, salt). "Tier 2 goods" = produced goods that need an input (planks, bread, ale, meat, iron ingot). Why: the same split is already used for stores (tier 1 and tier 2 stores) and it is easy to explain to the player. Iron ore and salt are raw but finite in this mod (`finite_resources`), so they are used as Medium requests, not as free rewards.

| Tier | Good | Item id | Class | Amount range |
|---|---|---|---|---|
| Small | Wood | 16 | raw | 40 to 80 |
| Small | Stone | 27 | raw | 30 to 60 |
| Small | Clay | 146 | raw | 30 to 60 |
| Small | Carp | 30 | raw | 40 to 80 |
| Medium | Planks | 17 | produced | 40 to 80 |
| Medium | Bread | 172 | produced | 40 to 80 |
| Medium | Ale | 28 | produced | 30 to 60 |
| Medium | Iron ore | 14 | raw | 30 to 60 |
| Medium | Salt | 145 | raw | 30 to 60 |
| Large | Planks | 17 | produced | 100 to 160 |
| Large | Bread | 172 | produced | 100 to 160 |
| Large | Iron ingot | 35 | produced | 40 to 80 |
| Large | Spears | 133 | produced | 40 to 80 |

Larger tiers ask for more units of produced goods. The ids 27 (stone), 28 (ale), 35 (iron ingot) and 146 (clay) come from archived notes and config comments. Confirm them in `DT_Items` (task 1.2). Rubble (15) is not a request good.

## Table 2: rewards by tier

One reward for each contract, drawn from the pool of its tier. All amounts are PROPOSED DEFAULTS.

| Tier | Reward kind | Good id | Amount |
|---|---|---|---|
| Small | Tier 1 goods: Wood | 16 | 30 to 60 |
| Small | Tier 1 goods: Stone | 27 | 20 to 40 |
| Small | Tier 1 goods: Clay | 146 | 20 to 40 |
| Small | Regional wealth | none | 40 to 80 |
| Medium | Weapons: Spears | 133 | 15 to 30 |
| Medium | Weapons: Large shields | 271 | 15 to 30 |
| Medium | Tier 2 goods: Planks | 17 | 30 to 60 |
| Medium | Tier 2 goods: Bread | 172 | 30 to 60 |
| Medium | Treasury silver | none | 150 to 300 |
| Large | Tech point | none | 1 |
| Large | Influence | none | 1000 |

A reward good is never the same as the request good of its contract. Rewards are paid as today: goods go to the first storehouse, silver to `playerRef.silver`, a tech point to `tech_picks_earned`, influence to the mod influence. The Large tech point reward is allowed only when `update-tech-tree-yearly-picks` is built (as today).

## Risks

- Regional wealth has no proven write path for OUR mod. A third-party mod writes `Region.regionalWealth` directly (`openspec/changes/archive/2026-10-15-legacy-13-mod-inspection/implementation-notes/battlefield-loot.md`), and the harness action that sets region values reads it back (`harness/scenarios/winter_region.py`). Whether the game keeps the value, and how the HUD shows it, is not checked for the mod. The old spec says "no safe read is proven" for regional wealth. Spike task 1.1 answers this. If the spike fails, the Small reward pool drops the regional wealth row.
- The influence amount (1000) is large against the old rewards (10 to 40) and the old penalty (500). The owner decided it. Check the influence scale at gate 2.
- The pak widget may not have enough controls for 9 cards plus 3 tier boxes. Task 1.3 checks it. A pak change would be needed.
- The arms shipment button has no place in the new window (open question 1 of the proposal).

## Open questions

Same list as the proposal. Spikes: regional wealth (task 1.1), item ids (task 1.2), pak controls (task 1.3).

## Save state

Kept as today: the spring counter, the offer and the done count. New: the fulfilled count of each tier. Dropped: the active contract keys. An old save loads with defaults; its old offer is dropped and the first new offer comes at the next spring.
