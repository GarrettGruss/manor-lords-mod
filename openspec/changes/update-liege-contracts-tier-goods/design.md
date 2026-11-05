## Context

The loader, rules and world code of `liege_contracts` handle one request kind (a good and an amount) and six reward kinds. Tier III needs costs that are not goods. This design lists the items, the new kinds, the defaults and the open questions.

## Table 1: Item ids

Checked in `modtools/work/DT_Items.vanilla.json` (213 rows, 2026-11-04). Names are the internal row names.

### Tier I requests (renewable goods)

| Good | Id | Row name | Note |
|---|---|---|---|
| Berries | 171 | Berries | kept |
| Mushrooms | 279 | mushrooms | kept |
| Carp | 30 | Carp | kept |
| Eel | 32 | Eel | moves here from Tier II |
| Small game | 330 | SmallGame | kept |
| Timber | 16 | Wood | category Construction/Woodworks, `Value` 0. It may not be a stored good. Spike task 1.5 checks it. If it is not stored in the player region, drop it. |
| Charcoal | 13 | Charcoal | new |
| Firewood | 216 | Firewood | new |
| Hides | 3 | Hides | kept |
| Eggs | 220 | Eggs | new |
| Rubble stone | 15 | Rubble | kept |
| Wooden planks | 17 | planks | kept |

### Tier I rewards (vassal goods)

| Good | Id | Row name |
|---|---|---|
| Salt | 145 | Salt |
| Iron ore | 14 | Iron Ore |
| Clay | 146 | Clay |
| Flax | 11 | Flax (a farm crop, kept because vassals pay it) |
| Stone | 27 | RoughStone |

### Tier II requests (processed goods)

| Good | Id | Row name | Note |
|---|---|---|---|
| Smoked meat | 320 | sausage | The table has no smoked meat row. Recipes 355 and 356 are sausage recipes. The owner guess is right: one request, "sausages". |
| Smoked fish | 323 | smokedFish | kept |
| Metal bars | 35 | Iron ingot / slab | kept |
| Bread | 172 | Bread | new |
| Rye bread | 170 | Rye Bread | new, a second bread row |
| Wooden parts | 7 | Wooden Parts | kept |
| Leather | 4 | Leather | new |
| Linen | 12 | Cloth_Linen | new |
| Yarn | 148 | Yarn | new |

### Tier II rewards

| Good | Id | Row name |
|---|---|---|
| Iron tools | 6 | Iron tools |
| Ale | 28 | Ale |
| Cider | 327 | Cider |
| Mead | 325 | Mead |
| Clothes | 149 | Clothes (the only clothing row; shoes are row 10 and are not used) |

### Tier III reward goods

| List | Ids |
|---|---|
| `weapons` | 177 swords, 178 polearms, 133 spears, 270 small shields, 271 large shields, 205 bows, 206 crossbows |
| `armor` | 163 gambesons, 164 mail armor, 273 helmets, 293 plate armor |

### Herd animals (Tier III cost)

| Animal | Id | Row name |
|---|---|---|
| Sheep | 72 | Sheep |
| Goat | 222 | goat_body |
| Pig | 321 | pig_body |
| Cow | 347 | Cow |
| Ox | 234 | oxBody |
| Horse | 98 | Horse |

Whether the mod can count and remove animals from pens is open (spike task 1.4).

### Dropped goods

| Wanted or old | Why dropped |
|---|---|
| Candles | no item row |
| Salted fish | no item row (only smoked fish 323) |
| Smoked meat (apart from sausage) | no row; sausage 320 is used |
| A specific clothing item (coat, dress) | one row only: Clothes 149 |
| Carrots 337, beets 339, cabbage 338, bows 205 (as a Tier I request) | leave the Tier I request pool (crops and arms are not renewable wild goods) |
| Cut stone 283, apples 296, quinces 46, pears 45 | leave the Tier II request pool (not on the owner list) |
| Silver, regional wealth, tech point, influence rewards | owner decision: the new reward lists replace them |

## Table 2: Pools and defaults

Amounts scale like the current tiers. Tier I uses `base` 50 and Tier II uses `base` 30, both with the existing weight and difficulty formula. Tier III has fixed amounts, scaled by the difficulty value and rounded half up (open question Q2).

### Weights (proposed)

- Tier I: berries 1.4, mushrooms 1.2, carp 1.0, eel 1.0, small game 1.0, timber 1.0 (if kept), charcoal 0.8, firewood 1.2, hides 0.8, eggs 1.2, rubble 1.6, planks 1.0.
- Tier II: sausage 1.0, smoked fish 1.0, metal bars 0.8, bread 1.2, rye bread 1.2, wooden parts 0.8, leather 0.8, linen 0.8, yarn 1.0.
- Reward amounts: Tier I vassal goods 20 to 40. Tier II tools 10 to 20, drinks 15 to 30, clothes 10 to 20.

### Tier III costs (defaults, open question Q1)

| Cost kind | Default at difficulty 1.0 | Form |
|---|---|---|
| `loan_units` | 10 squads of the player for 60 game days | depends on `spike-loan-units`. Owner fallback: if loaning is impossible, the units are lost for good. |
| `loan_peasants` | 10 peasants for 30 game days | same spike. Fallback: the peasants are lost. |
| `send_families` | 3 families, for good | spike task 1.2 |
| `tribute_season` | the vassal tribute of one season goes to the liege | spike task 1.3 |
| `herd` | 10 sheep, goats or pigs, or 4 cows, oxen or horses | spike task 1.4 |

### Tier III rewards (defaults)

| Reward kind | Default | Note |
|---|---|---|
| `law` | one random law that is not unlocked yet | calls `laws_unlock(id, "Contract: <name>")`; works whatever the tech path |
| `kings_favour` | +10 King's Favour | the scale of the value is unknown (spike task 1.1) |
| `weapons` | 20 to 40 of one good of list `weapons` | |
| `armor` | 15 to 30 of one good of list `armor` | |
| `law_slot` | +1 law slot | calls `laws_add_slot()`; capped (decision 2) |
| `relief_promise` | +5 squads in the relief army of the next great raid | saved bonus, used once |

The `law` reward is drawn only when at least one law is still locked.

## Decisions

1. **Cost kinds replace the request.** A Tier III contract holds a `cost` (kind and amount) in place of `good` and `amount`. Tier I and II contracts keep `good` and `amount`. The card shows "Cost: <text>" for Tier III and "Deliver <n> <GOODS>" for the other tiers.
2. **Law slots (owner decision 2026-11-04).** Law slots start at 1. The total is at most 5 (1 base and up to 4 extra). `laws_add_slot()` does nothing past the cap. A `law_slot` reward is not drawn when the cap is reached. If a `law_slot` contract was dealt earlier and the cap is reached before it is fulfilled, the reward pays King's Favour (the same amount as `kings_favour`). This fallback is a lead proposal. The owner can change it (Q3).
3. **Contract laws ignore the tech path (owner decision 2026-11-04).** A law won from a contract can be enacted whatever path the player took. The path rule that keeps other-path laws refused does not apply to a contract law.
4. **Required change in `add-laws-menu`.** The merged spec of `add-laws-menu` (PR #566) still says 2 base slots, no cap, and that other-path laws stay refused. Its gate 2 must apply decisions 2 and 3: `max_active_laws` of 1, a total cap of 5 in `laws_add_slot`, and an Enact check that accepts a contract-unlocked law of the other path. This change calls `laws_unlock` and `laws_add_slot` and declares that dependency. It does not edit the specs of `add-laws-menu`.
5. **King's Favour.** The player pawn has `kingsFavour` (Int) and `getKingsFavour_daysLeft()` (legacy spec 02, `jmap-findings.md`). The harness action `add_kings_favour` calls `changeKingsFavour(amount)` on the player pawn (`harness/runlib/actions.py`), and `harness/scenarios/probe_actions.py` probes it. No recorded result proves it. So a mod reward is not proven. Spike task 1.1 checks that `changeKingsFavour` changes `kingsFavour` and what the value does in the game (a days-left function suggests a timed effect). If the call does not work, set the field in Lua (as `set_influence` does) or drop the reward.
6. **Relief promise.** `relief_promise` adds squads to the relief army of the great raid (`features/invasion/relief.lua`; the base is 15, 8 or 0 squads by difficulty). The bonus is kept in mod state (`relief_bonus_squads`, integer, default 0), added when the relief army spawns, and reset to 0 after that. At difficulty 3 the base is 0 and the bonus still applies. The squads appear at `relief_offset` as today.
7. **Loan forms depend on a spike.** `loan_units` and `loan_peasants` are in the data table but are drawn only when the config value `liege_contracts.loan_enabled` is true. Gate 2 sets it from the result of `spike-loan-units`. If loaning is impossible, the cost becomes "the units are lost" (the owner fallback), and the card text says so.
8. **State.** The saved offer text form carries the cost kind and amount and the new reward kinds. A saved offer with an old good or reward that the table no longer has is dropped without penalty (existing rule). The table version is 3.

## Open questions for the owner

- **Q1 Amounts and durations.** The defaults in table 2 are proposals: loan length (60 days units, 30 days peasants), squads and peasants count, families (3), herd size, King's Favour amount (10), relief bonus (+5 squads), weapon and armor amounts.
- **Q2 Difficulty scaling of Tier III costs.** Scaled by the raid level like the goods (proposed), or fixed?
- **Q3 Capped slot reward.** King's Favour (lead proposal), or no `law_slot` card once the cap is reached?
- **Q4 Loan failure.** If a loaned unit dies while away, is the contract still paid? Proposed: yes. The reward is paid when the cost is taken, as for all contracts.
- **Q5 Timber.** Keep "Wood" (16) only if spike 1.5 shows it in the stores.

Answered by the owner on 2026-11-04 and not open: laws from contracts ignore the tech path; law slots start at 1 and cap at 5.

## Risks

- Removing families, animals and units from Lua may crash the game (`DANGEROUS_ACTIONS.md`: `family_add` with `building_assign_worker` crashed; `K2_DestroyActor` on units crashed). Each cost needs a spike before it is built. A cost with no safe method is left out of the table and is listed as dropped in the implementation pull request.
