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
| Timber | 16 | Wood | category Construction/Woodworks, `Value` 0. Spike 1.5 (run 20261106-001410-ca20): the stock read finds 23 units, so it is a stored good and stays. |
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

Dropped: spike 1.4 found no safe way to remove animals (decision 9), so the `herd` cost is not in the table. This table is kept as history.

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

Amounts scale like the current tiers. Tier I uses `base` 50 and Tier II uses `base` 30, both with the existing weight and difficulty formula. Tier III amounts are the owner amounts of 2026-11-05, scaled by the difficulty value (easy 0.75, medium 1.0, hard 1.25) and rounded half up (decision 11).

### Weights (proposed)

- Tier I: berries 1.4, mushrooms 1.2, carp 1.0, eel 1.0, small game 1.0, timber 1.0 (if kept), charcoal 0.8, firewood 1.2, hides 0.8, eggs 1.2, rubble 1.6, planks 1.0.
- Tier II: sausage 1.0, smoked fish 1.0, metal bars 0.8, bread 1.2, rye bread 1.2, wooden parts 0.8, leather 0.8, linen 0.8, yarn 1.0.
- Reward amounts: Tier I vassal goods 20 to 40. Tier II tools 10 to 20, drinks 15 to 30, clothes 10 to 20.

### Tier III costs (owner amounts, 2026-11-05)

| Cost kind | Default at difficulty 1.0 | Form |
|---|---|---|
| `loan_units` | 1 squad of the player for 60 game days | decision 12 (spike `spike-loan-units`) |
| `send_families` | 3 families, for good | spike 1.2 works (`notes/send-families.md`) |
| `tribute_season` | the vassal tribute of one season (3 months) goes to the liege | decision 13; the amount is in months |
| ~~`loan_peasants`~~ | dropped by the owner (2026-11-05) | decision 10 |
| ~~`herd`~~ | was 10 small or 4 large animals; dropped, no safe removal | decision 9 |

### Tier III rewards (defaults)

| Reward kind | Default | Note |
|---|---|---|
| `law` | one random law that is not unlocked yet | calls `laws_unlock(id, "Contract: <name>")`; works whatever the tech path |
| `kings_favour` | +10 King's Favour | spike 1.1 works: `changeKingsFavour(10)` raised `kingsFavour` from 0 to 10 (`notes/kings-favour.md`) |
| `weapons` | 20 to 40 of one good of list `weapons` | |
| `armor` | 15 to 30 of one good of list `armor` | |
| `law_slot` | +1 law slot | calls `laws_add_slot()`; capped (decision 2) |
| `relief_promise` | +5 squads in the relief army of the next great raid | saved bonus, used once (owner amount) |

The `law` reward is drawn only when at least one law is still locked.

## Decisions

1. **Cost kinds replace the request.** A Tier III contract holds a `cost` (kind and amount) in place of `good` and `amount`. Tier I and II contracts keep `good` and `amount`. The card shows "Cost: <text>" for Tier III and "Deliver <n> <GOODS>" for the other tiers.
2. **Law slots (owner decision 2026-11-04).** Law slots start at 1. The total is at most 5 (1 base and up to 4 extra). `laws_add_slot()` does nothing past the cap. A `law_slot` reward is not drawn when the cap is reached. If a `law_slot` contract was dealt earlier and the cap is reached before it is fulfilled, the reward pays King's Favour (owner decision 2026-11-05: when the player already has 5 slots, `max_total_laws`, King's Favour is paid; the amount is the default of `kings_favour`, 10).
3. **Contract laws ignore the tech path (owner decision 2026-11-04).** A law won from a contract can be enacted whatever path the player took. The path rule that keeps other-path laws refused does not apply to a contract law.
4. **Required change in `add-laws-menu`.** The merged spec of `add-laws-menu` (PR #566) still says 2 base slots, no cap, and that other-path laws stay refused. Its gate 2 must apply decisions 2 and 3: `max_active_laws` of 1, a total cap of 5 in `laws_add_slot`, and an Enact check that accepts a contract-unlocked law of the other path. This change calls `laws_unlock` and `laws_add_slot` and declares that dependency. It does not edit the specs of `add-laws-menu`.
5. **King's Favour.** The player pawn has `kingsFavour` (Int) and `getKingsFavour_daysLeft()` (legacy spec 02, `jmap-findings.md`). Spike 1.1 (run 20261106-000620-91e6): `changeKingsFavour(10)` on the player pawn raised `kingsFavour` from 0 to 10, and the value held for one game day. The days-left function counted down (249, 248, 247), so the game may use it for a timed effect; what the value does in the game is not known. The mod calls `changeKingsFavour` and reads the value back, as `add_regional_wealth` did.
6. **Relief promise.** `relief_promise` adds squads to the relief army of the great raid (`features/invasion/relief.lua`; the base is 15, 8 or 0 squads by difficulty). The bonus is kept in mod state (`relief_bonus_squads`, integer, default 0), added when the relief army spawns, and reset to 0 after that. At difficulty 3 the base is 0 and the bonus still applies. The squads appear at `relief_offset` as today.
7. **Loan switch.** `loan_units` is drawn only when the config value `liege_contracts.loan_enabled` is true. It is true: the spike `spike-loan-units` showed that a squad can be removed and respawned (decision 12). If the value is false, the cost is dropped from the draw.
8. **State.** The saved offer text form carries the cost kind and amount and the new reward kinds. A saved offer with an old good or reward that the table no longer has is dropped without penalty (existing rule). The table version is 3.

9. **The herd cost is dropped (spike 1.4).** Animals are not goods in a building inventory: an ox shed (type 97) holds the animals as actors in its `animals` array. `getStockOfGood(234)` counts them (2 oxen), but `consumeGoodNoCheck` takes nothing (0 taken), and `just_die` on a `VAMP_Ox_C` runs without an error and changes nothing (`dead` stays false, the count stays). `K2_DestroyActor` is on the crash list. There is no safe way to remove an animal, so `herd` is not in the table (task 2.2). Details: `notes/herd.md`.
10. **The peasant loan is dropped (owner decision 2026-11-05).** The cost kind `loan_peasants` and its config are removed. The spike showed that peasants cannot be taken out of the simulation anyway.
11. **Large costs scale with the difficulty (owner decision 2026-11-05).** The amount of a Large cost is `max(1, round(amount * difficulty))` with the factors of the other tiers (easy 0.75, medium 1.0, hard 1.25). The loan length (60 days) does not scale. Rewards do not scale.
12. **How a squad loan works.** The contract takes the player squad with the most men. The mod writes down the template, the number of men and the mean experience, removes the squad with `PawnCPP:addRemoveSquadRequest({Value = id})` (no bodies, no crash in the spike), and spawns a squad of the same template with `spawnArmy` after 60 game days, also after a load (the record is in mod state, `loans`). The returned squad is equal, not the same men (names, gear and the squad id are not kept). The template of a squad is not readable from the units (`unitTemp` reads None), so the mod takes it from the registry of `HarnessBattle` (squads that the harness or the mod spawned) or from the config table `liege_contracts.loan_templates` by the number of men (32 men: `spearMilitia`, 36 men: `retinue_tier1`, the two sizes measured in the spike). A squad of another size cannot be loaned: the contract is refused with the reason "the squad type is not known". Open for the owner: more templates.
13. **The tribute pause.** `tribute_season` sets the saved value `tribute_skip_months` of the feature `tribute` to the cost amount in months (3 months is one season at difficulty 1.0). Each monthly tick that finds a value above 0 pays nothing and lowers it by 1. The contract is refused when no vassal is handed over.

## Open questions for the owner

- **Q4 Loan failure.** If a loaned unit dies while away, is the contract still paid? Proposed: yes. The reward is paid when the cost is taken, as for all contracts. (A removed squad cannot die while away.)
- **Q6 Squad types.** Only the two measured squad sizes can be loaned (decision 12). Which other squad types should the table know?
- **Q7 Weapon and armor amounts** (20 to 40 and 15 to 30) were not part of the 2026-11-05 answer and stay as proposed.

Answered by the owner on 2026-11-04 and not open: laws from contracts ignore the tech path; law slots start at 1 and cap at 5. Answered on 2026-11-05 and not open: the Tier III amounts (1 squad for 60 days, 3 families, King's Favour +10, relief +5 squads), the cost scaling with the difficulty (Q2), King's Favour for a law slot at the cap (Q3), no peasant loan, and Wood (16) stays (Q5, spike 1.5).

## Risks

- Removing families, animals and units from Lua may crash the game (`DANGEROUS_ACTIONS.md`: `family_add` with `building_assign_worker` crashed; `K2_DestroyActor` on units crashed). Each cost needs a spike before it is built. A cost with no safe method is left out of the table and is listed as dropped in the implementation pull request (done for `herd`, decision 9).
