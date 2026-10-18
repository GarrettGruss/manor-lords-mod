# M04 iteration 03: coin-buy-back

Branch: `feat/M04-bandits-03-coin-buy-back`. Issue: #167.

## Goal
The player pays silver and the bandits go back to the village as families (M00: "fight them or pay coin to bring them back").
The mod sets the price and checks it, because the game does not (`homeless-rebellion.md`, `bandit-settlement.md` Q1).

## Price rule (TBD, tuned in playtests)
- `price = ceil(families_returned x silver_per_family x price_multiplier)`.
- Config `bandits.buy_back`: `silver_per_family = 10`, `price_multiplier = 1.0`.
- The two tech nodes of M00 decision 29 change only `price_multiplier`: Iron Hand 1.25 (+25%), Amnesty 0.5 (-50%). Both multiply. The tech tree is M12; this iteration only reads the multiplier from the config (`rules.buy_back_price`).
- Scaled values round up (M00 decision 30). With the start values, 2 families cost 20 silver, the amount that the proven letter used.

## How the player triggers it (this iteration)
- Named command `InvasionMod.bandits_buy_back`. A UI comes later (a diplomacy panel entry or a button; open question 6 of the README).
- The command uses the native negotiation letter underneath: the relation tag `attacking`, then the paragraph `raider_suggestSettle+<price>` sent to the bandit lord. This is the proven route.
- The game does not check the price and the letter removes every bandit unit. So the mod checks the rules before it sends the letter.
- The native letter in the diplomacy screen still works for the player and is not priced by the mod. The mod cannot intercept it safely (a hook on `sendLetter` is not tried). This is a known gap until the UI iteration.

## Rules
- The mod counts `bandits_outstanding_families` (ModState): families that turned to bandits and have not come back. A conversion adds to it.
- Families returned = min(outstanding, free home slots). Free home slots = `getAvailableLivingSpace().constructed`.
- Refused, with a reason and no change, when: no outstanding families; no bandit units; no free home slot; silver is below the price.
- On success: price is charged, bandit units go down, families return, outstanding goes down by the families returned.

## Open question (spike S1, first task of the implementation)
Spec 15 found that the letter returns families for raid squads (`spawnRaiders`: 5 of 5 tries) but not for `spawnArmy` squads, which `homeless_rebel` mode `home` makes (0 of 3 tries). The conversion of iteration 01 uses mode `home`.
S1 measures this again with the conversion squads. If it still gives no family, the mod returns the families by another proven route and the note records which one. The route must not use `Region:AddNewFamily` (crash). Candidates: a decoy raid before the letter; `settle_region`. A route that overfills the free slots is capped by the mod or refused.

## Acceptance criteria
- C1: with outstanding families F, free slots S, silver P0: after the buy-back, silver = P0 - price (exact, silver read while paused), and price = ceil(min(F, S) x 10 x multiplier).
- C2: families return: families after - families before is between 1 and min(F, S) (range, because the game may fill fewer or the village may grow).
- C3: bandit units after < bandit units before, and 0 within 120 game seconds.
- C4: outstanding families go down by the families returned.
- C5: refused when silver is below the price: silver, families and bandit units do not change; the answer has a reason.
- C6: refused when no free home slot: no change; the answer has a reason.
- C7: refused when there is nothing to buy back (no outstanding families or no bandit units): no change.
- C8: price multiplier 1.25 and 0.5 give prices 13 and 5 for 1 family and 25 and 10 for 2 families (pure rule, fake game test).
- C9: the game runs 5 game days after the buy-back with no crash.
- Fake game tests cover C1, C4 to C8.

## Scenarios
- `scenarios/bandits/buy_back.py` (`bandits-buy-back`): C1 to C7 and C9 in the real game.

## Result
Not run yet.
