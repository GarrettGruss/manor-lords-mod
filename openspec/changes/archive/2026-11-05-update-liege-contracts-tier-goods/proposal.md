## Why

<!-- Issue: #569 -->

The three tiers of the liege contracts ask for goods that do not match their meaning. Small contracts ask for farm crops and clay. Large contracts ask for weapons and armor that the player rarely has. The owner decided on 2026-11-04 to rework the tiers: Small is for renewable goods, Medium is for processed goods, and Large is for costs that hurt (units, families, tribute, animals) with strong rewards (laws, King's Favour, arms, a relief army). Issue: #569.

## What Changes

- **Tier I (Small).** Requests are renewable goods (berries, mushrooms, fish, small game, timber, charcoal, firewood, hides, eggs, rubble stone, planks). Rewards are vassal goods (salt, iron ore, clay, flax, stone). The goods and item ids are in `design.md` (table 1).
- **Tier II (Medium).** Requests are processed goods (sausage, smoked fish, metal bars, bread, wooden parts, leather, linen, yarn). Rewards are tools, drinks (ale, cider, mead) and clothes. Candles do not exist in the game and are dropped.
- **Tier III (Large).** A request is a cost, not a delivery of goods: loan one squad for 60 days, send 3 families away for good, or give the vassal tribute of one season (owner amounts of 2026-11-05; the herd cost and the peasant loan are dropped, see `design.md`, decisions 9 and 10). Rewards: a random law, King's Favour, weapons, armor, an extra law slot, or a promise of a larger relief army in the next great raid. King's Favour replaces the old 1000 influence reward.
- The reward kinds `regional_wealth`, `silver`, `tech_point` and `influence` leave the reward pools.
- New reward kinds: `law`, `kings_favour`, `law_slot`, `relief_promise`. New cost kinds: `loan_units`, `send_families`, `tribute_season`.
- Owner decisions (2026-11-04): a law won from a contract works whatever the tech path of the player. Law slots start at 1 and are at most 5 in total. A `law_slot` reward past the cap pays King's Favour instead (owner decision 2026-11-05). Large costs scale with the difficulty like the other tiers (owner decision 2026-11-05).
- Unchanged: nine contracts each spring, one fulfilled contract per tier and year, the built manor rule, the winter expiry with no penalty, the window layout (the Large cards show a cost line in place of a goods line).

## Design pillars

Serves `design/mod/invasion-mod.md` pillar 2 (rule through others: the liege asks for duty) and pillar 3 (scarcity: vassal goods are the rewards of Tier I). It does not break pillar 6: a contract law is a free pick and the tech path stays a choice (owner decision, `design.md`, decision 3).

## Dependencies

- `add-laws-menu` (#563, spec merged in PR #566): the hooks `laws_unlock(id, source)` and `laws_add_slot()`. Its gate 2 must apply the owner decisions of 2026-11-04 (1 base slot, cap of 5 slots, a contract law ignores the path rule). See `design.md`, decision 4.
- The spike `spike-loan-units` (merged, PR #574): a squad is loaned with `PawnCPP:addRemoveSquadRequest` and returned with `spawnArmy`. Peasants cannot be loaned; the owner dropped the peasant loan (2026-11-05).
- Spike tasks of this change (tasks 1.x): King's Favour write (works), family removal (works), herd removal (fails, cost dropped), the tribute pause (built in the tribute feature), the timber good (a stored good).

## Non-goals

- No new laws and no change of law effects.
- No change of the window style, the 2-click rule, the tier limit, the spring refresh or the winter expiry.
- No new items and no pak data change. A good that is not in `DT_Items` is dropped.
- No change of the great raid, except one saved bonus for the relief army size.

## Impact

- Modified spec: `mod/liege_contracts`.
- Data: `mod/InvasionMod/data/liege_contracts/contracts.json` (version 3).
- Code (gate 2): `Scripts/features/liege_contracts/` (`loader.lua`, `rules.lua`, `world.lua`, `init.lua`, `view.lua`), a small read of the bonus in `features/invasion/` (where `relief.lua` is called) and `Scripts/config.lua`.
