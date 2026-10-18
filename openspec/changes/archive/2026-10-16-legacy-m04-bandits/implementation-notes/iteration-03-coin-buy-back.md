# M04 iteration 03: notes

## Design
- Command `InvasionMod.bandits_buy_back`. No arguments. The mod reads the facts, checks the rules (`rules.buy_back_refusal`), then sends the native letter: tag `attacking`, paragraph `raider_suggestSettle+<price>`.
- The game does not check the price and removes all bandit units on the map. The mod checks silver, free home slots, outstanding families and bandit units first.
- ModState keys: `bandits_outstanding_families` (added at each conversion), `bandits_returned_families`.
- A sent buy-back is "pending". The scheduler poll looks at it every 5 polls. It ends when the bandit units are 0 and a family came back, or after 120 game seconds (game time, because the game may be paused).
- The price follows the families that can return: `min(outstanding, free slots)` x 10 x multiplier.

## Spike S1: does the letter return families for the conversion squads?
Spec 15 found 0 of 3 for `spawnArmy` squads (`homeless-rebellion.md` part 3, test 5). The squads of the conversion are `spawnArmy` squads. New measurements, fixture `base`, letter 20 silver 10 game seconds after the conversion (2 families, 1 rebel squad of 18, free slots 4):
| Run | Result |
| --- | --- |
| `20261018-011056-91be` | +2 families, silver 83 to 63, bandit units 36 to 0 |
| `20261018-011706-785b`, `-011938-44f9`, `-012921-0043`, `-015406-1e47` | +2 families each |
| `20261018-012543-c784` | 0 families. Silver was taken, units were removed, population stayed 29 for 270 game seconds |
| `20261018-013232-64c7` cycle 0, `-013735-45ac` cycle 0, `-013935-ff13` cycle 0 | +2 families each |
| `20261018-014558-f9bd`, `-014725-5aa6`, `-014852-5b73` (camp units killed first) | +2, +2, 0 |
| `20261018-015930-1211`, `-020227-dd05`, `-020504-b610` (final scenario, new code) | 0, +2, +2 |
- First letter in a fresh game: families came back in 12 of 15 tries (including the final scenario). The 3 failures looked the same as the successes in every value the mod reads.
- A second letter in the same game (cycles 1 to 3 of runs 64c7 and ff13, with a decoy raid in ff13): 0 of 6 (some were refused by the mod while the first was pending). A cooldown is a guess, not proven.
- The bandit camp squad is not the source of the families: with the camp killed first, the rebel squad alone gave +2 in 2 of 3 tries.
- A decoy raid (`spawn_raid`) before the letter did not help in cycles 1 to 3 of run ff13. It is not used.
- The cause of the failures is open. The mod handles it: when no family comes back, it gives the silver back (up to the price) and puts the families back in the outstanding count (`refunded` in the result). The bandit units are gone then. The families stay in the pool for a later buy-back.

## Other findings
- The letter takes exactly the price in silver in every run (83 to 63, 100 to 80). Silver read while paused matches `before - price`.
- The harness run cap (400 runs, `runs/.iterations` in the main repo folder) was reached during the spikes. The runs used `--max-runs 500`.
- One run (`20261018-012215-4744`) ended with a harness_error in the 5 day wait after all buy-back checks passed (bridge blocked 15 s). One run (`20261018-013735-45ac`) ended after `calling 'write' on bad self (FILE* expected, got FILE*)` in HarnessCommands. Both look like the known Lua state fragility of long runs (issue 163), not a buy-back fault. Not isolated.
- Known gap: the player can still send the native letter from the diplomacy screen at any price. The mod does not intercept it.
- C6 (no free home slot) is covered by the fake game test only. The real game village has free slots after a conversion, and the harness has no safe way to fill them.
