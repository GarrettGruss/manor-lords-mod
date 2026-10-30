## Context

The current feature offers 3 contracts, the player picks one, and a missed deadline costs influence. Code: `mod/InvasionMod/Scripts/features/liege_contracts/` (`init.lua`, `rules.lua`, `world.lua`, `loader.lua`, `view.lua`). Goods are counted with `region:getStockOfGood` and taken from the stores of the player region (`world.take_goods`: tier 1 stores 6 and 72 first, then the tier 2 stores). Silver is paid with `playerRef.silver = before + amount` (`liege_influence.add_silver`). Goods are added to the first storehouse. A tech point is `tech_picks_earned` in ModState.

## Decisions

1. Three tiers: Small, Medium, Large. Each spring the mod draws 3 different requests from each tier (9 in all). A request and a reward are drawn together into one contract, with the request amount from the formula below.
2. The limit per tier per year is `liege_contracts.tier_limits = { small = 1, medium = 1, large = 1 }`. The fulfilled counts reset at each spring.
3. Contracts expire at the start of winter. The offer is cleared then. No penalty. The window then shows the time to the next spring.
4. Delivery source: the same as today (any store of the player region). The stock shown on a card is `getStockOfGood`, which is the same source. Decided by the owner (2026-10-30).
5. The Fulfil button is enabled when stock >= amount and the tier count < limit. The mod checks both again when the click arrives, and refuses with a reason if not.
6. The data file holds the two pools per tier (below). No good id, amount or text is in Lua code. The base, weight and difficulty values are in config.

## Goods tiers (owner decision 2026-10-30)

The owner gave these three lists of goods. They are decided, not proposed.

- Tier 1 goods: planks, berries, mushrooms, small game, hides, rubble stone, clay, carrots, beets, cabbage, salt, bows, carp.
- Tier 2 goods: cut stone, fruit (apples, quinces, pears), tools, metal bars, wooden parts, eel.
- Tier 3 goods: swords, shields, polearms, spears, large shield, helmets, gambeson, mail armor, plate armor, crossbows, smoked fish, sausages.

ASSUMPTION (the lead's default; the owner may change it): a Small contract asks for tier 1 goods, a Medium contract asks for tier 2 goods, and a Large contract asks for tier 3 goods. Each request is one good. The rewards stay as decided before (Table 2). A reward good is never the request good of the same contract. A "weapon" reward is one of the tier 3 weapons (swords, shields, polearms, spears, large shield, crossbows). Bows are tier 1, so they are not a weapon reward.

All numbers are PROPOSED DEFAULTS that the owner tunes in config. Higher tiers ask for fewer units of more valuable goods. Item ids are the row names of `DT_Items` (extracted vanilla table, 213 rows). The column "Id status" says "confirmed (source)" or "unknown". An unknown id has a candidate from the table row name; task 1.2 confirms it. No id is a silent guess.

## Request amount formula (owner decision 2026-10-30)

`amount = max(1, round(base(tier) * weight(good) * difficulty))`

- `base(tier)`: one config value per contract tier. Proposed: Small 50, Medium 30, Large 15 (`liege_contracts.base`).
- `weight(good)`: one config value per good of Table 1 (`liege_contracts.weight`, by item id). Cheap and plentiful goods have a high weight. Valuable goods have a low weight. Proposed values are in Table 1.
- `difficulty`: a multiplier (`liege_contracts.difficulty`). ASSUMPTION (lead's default, an open question for the owner): it comes from the yearly raid level that the player chose in the scenario settings: level 1 (easy) 0.75, level 2 (medium) 1.0, level 3 (hard) 1.25, level 0 (off) 1.0.
- `round` rounds half up to a whole number.

Worked example: Large, plate armor, hard: `15 * 0.35 * 1.25 = 6.56`, so the request is 7 plate armor. At medium it is `15 * 0.35 * 1.0 = 5.25`, so 5.

## Table 1: requests by tier

The column "Amount at difficulty 1.0" is `round(base * weight)`.

| Tier | Good | Item id | Id status | Base | Weight | Amount at difficulty 1.0 |
|---|---|---|---|---|---|---|
| Small | Planks | 17 | confirmed (archived notes of m06; DT_Items `planks`) | 50 | 1.0 | 50 |
| Small | Berries | 171 | confirmed (DT_Items `Berries`) | 50 | 1.4 | 70 |
| Small | Mushrooms | 279 | confirmed (archived note `deposit-decal.md`: Resource_Mushrooms type 279) | 50 | 1.2 | 60 |
| Small | Small game | 330 | confirmed (DT_Items `SmallGame`) | 50 | 1.0 | 50 |
| Small | Hides | 3 | confirmed (DT_Items `Hides`; 139 is `Hide Washed`) | 50 | 0.8 | 40 |
| Small | Rubble stone | 15 | confirmed (DT_Items `Rubble`; named in the earlier draft) | 50 | 1.6 | 80 |
| Small | Clay | 146 | confirmed (DT_Items `Clay`; config comments) | 50 | 1.4 | 70 |
| Small | Carrots | 337 | confirmed (DT_Items `Carrots`) | 50 | 1.2 | 60 |
| Small | Beets | 339 | confirmed (DT_Items `Beetroots`) | 50 | 1.2 | 60 |
| Small | Cabbage | 338 | confirmed (DT_Items `Cabbages`) | 50 | 1.2 | 60 |
| Small | Salt | 145 | confirmed (archived notes; DT_Items `Salt`) | 50 | 0.6 | 30 |
| Small | Bows | 205 | unknown: task 1.2 confirms. Candidate 205 `warbows` (the config lists it as the bow good); 21 is `huntingBow` | 50 | 0.4 | 20 |
| Small | Carp | 30 | confirmed (archived notes; DT_Items `Carp`) | 50 | 1.0 | 50 |
| Medium | Cut stone | 283 | unknown: task 1.2 confirms. Candidate 283 `DressedStone` (name match only); 27 is `RoughStone` | 30 | 1.0 | 30 |
| Medium | Apples | 296 | confirmed (DT_Items `apples`) | 30 | 1.2 | 36 |
| Medium | Quinces | 46 | confirmed (DT_Items `Quinces`) | 30 | 1.0 | 30 |
| Medium | Pears | 45 | confirmed (DT_Items `Pears`) | 30 | 1.2 | 36 |
| Medium | Tools | 6 | unknown: task 1.2 confirms. Candidate 6 `Iron tools`; other tool rows exist (saw, mallet, knife, sickle) | 30 | 0.5 | 15 |
| Medium | Metal bars | 35 | confirmed (archived notes: iron ingot; DT_Items `Iron ingot / slab`) | 30 | 0.8 | 24 |
| Medium | Wooden parts | 7 | confirmed (DT_Items `Wooden Parts`) | 30 | 0.8 | 24 |
| Medium | Eel | 32 | confirmed (DT_Items `Eel`) | 30 | 1.0 | 30 |
| Large | Swords | 177 | confirmed (archived note `loot-ids.md`: sword = sidearm good) | 15 | 1.0 | 15 |
| Large | Shields | 270 | confirmed (archived note `loot-ids.md`: small shield) | 15 | 1.0 | 15 |
| Large | Polearms | 178 | confirmed (config `rebellion_weapon_ids`) | 15 | 1.0 | 15 |
| Large | Spears | 133 | confirmed (archived note `item-ids.md`) | 15 | 1.2 | 18 |
| Large | Large shield | 271 | confirmed (archived note `item-ids.md`) | 15 | 1.0 | 15 |
| Large | Helmets | 273 | unknown: task 1.2 confirms which helmet. Candidate 273 `militia_helmets_resource` (confirmed as the basic militia helmet); 276, 285, 288, 289, 294 are other helmet rows | 15 | 0.6 | 9 |
| Large | Gambeson | 163 | confirmed (config `rebellion_weapon_ids`; `loot-ids.md`) | 15 | 0.6 | 9 |
| Large | Mail armor | 164 | confirmed (config `rebellion_weapon_ids`) | 15 | 0.4 | 6 |
| Large | Plate armor | 293 | confirmed (archived note `engine-facts.md` of assess-endgame-buildings: item 293, retinue tier 3 armor) | 15 | 0.35 | 5 |
| Large | Crossbows | 206 | confirmed (config `rebellion_weapon_ids`) | 15 | 0.8 | 12 |
| Large | Smoked fish | 323 | confirmed (DT_Items `smokedFish`) | 15 | 1.2 | 18 |
| Large | Sausages | 320 | confirmed (DT_Items `sausage`) | 15 | 1.2 | 18 |

Fruit is three rows (apples, quinces, pears). The pool of a tier is the rows of its tier in this table. Tier 1 has 13 rows, tier 2 has 8 rows and tier 3 has 12 rows, so every pool has more than the 3 requests that the spring draw needs.

## Table 2: rewards by tier

One reward for each contract, drawn from the pool of its tier. The tiers of the rewards stay as decided before the goods tiers. All amounts are PROPOSED DEFAULTS.

| Tier | Reward kind | Good id | Amount |
|---|---|---|---|
| Small | Tier 1 goods | any good of the tier 1 rows of Table 1 (not the request good) | 20 to 40 |
| Small | Regional wealth | none | 40 to 80 |
| Medium | Weapons | one of 177 swords, 270 shields, 178 polearms, 133 spears, 271 large shield, 206 crossbows (not the request good) | 10 to 20 |
| Medium | Tier 2 goods | any good of the tier 2 rows of Table 1 (not the request good) | 15 to 30 |
| Medium | Treasury silver | none | 150 to 300 |
| Large | Tech point | none | 1 |
| Large | Influence | none | 1000 |

A reward good is never the same as the request good of its contract. Rewards are paid as today: goods go to the first storehouse, silver to `playerRef.silver`, a tech point to `tech_picks_earned`, influence to the mod influence. The Large tech point reward is allowed only when `update-tech-tree-yearly-picks` is built (as today).

## Risks

- Regional wealth has no proven write path for OUR mod. A third-party mod writes `Region.regionalWealth` directly (`openspec/changes/archive/2026-10-15-legacy-13-mod-inspection/implementation-notes/battlefield-loot.md`), and the harness action that sets region values reads it back (`harness/scenarios/winter_region.py`). Whether the game keeps the value, and how the HUD shows it, is not checked for the mod. The old spec says "no safe read is proven" for regional wealth. Spike task 1.1 answers this. If the spike fails, the Small reward pool drops the regional wealth row.
- The pak widget may not have enough controls for 9 cards plus 3 tier boxes. Task 1.3 checks it. A pak change would be needed.
- The arms shipment button moves to the manor (owner decision 2026-10-30). The exact manor UI hook (the manor menu or panel, and whether the pak has a control for it) is not checked. Task 3.4 checks it. The change has a delta spec for `mod/liege_influence`.

## Open questions

Same list as the proposal (regional wealth, difficulty source, request tiers). Spikes: regional wealth (task 1.1), item ids (task 1.2), pak controls (task 1.3).

## Save state

Kept as today: the spring counter, the offer and the done count. New: the fulfilled count of each tier. Dropped: the active contract keys. An old save loads with defaults; its old offer is dropped and the first new offer comes at the next spring.
