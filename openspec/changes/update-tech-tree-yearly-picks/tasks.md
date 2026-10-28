## 1. Picks
- [ ] 1.1 `config.lua` (`tech_tree`): remove `slots_per_level`; add `picks_per_year` 1, `initial_picks` 1, `spring_season`. Remove `slots_for_level` from `rules.lua`.
- [ ] 1.2 ModState keys `tech_picks_earned`, `tech_spring_no`. Add a getter for the season value and counter in `features/invasion`. Start grant and spring grant in the tech tree poll, saved before the log.
- [ ] 1.3 Read the spring value of the calendar season enum in the real game (spike, read only) and set `spring_season`. Write it to `notes/`.
- [ ] 1.4 `rules.unlock_refusal`: pick check ("no free pick"); skip the path and order checks for a common tech.
- [ ] 1.5 Update `tech_tree_state` (picks earned and free, common techs).

## 2. Data
- [ ] 2.1 `tree.json` version 2: `common_nodes` (3), three common laws with `path` "common", new effect kinds. Update `tree.lua` load and checks.
- [ ] 2.2 `rules.totals` and `rules.enact_refusal`: new flags, common laws without a path.

## 3. Laws
- [ ] 3.1 Strip the Dead: gate the pit pay-out in `raid_behavior` on the law, add bandit and soldier bodies, loot order (override, Hussite share, `raid_behavior.body_loot`), `strip_the_dead.order_loss` in config, order write in `bandits`. Ask the owner for the `body_loot` values.
- [ ] 3.2 Disarm the Peasantry: home tick in `tech_tree/world.lua` (`consumeGoodNoCheck`, `addToInventory`), `disarm.tick_days` config, log `disarm_homes_missed`. Use `bandits.rebellion_weapon_ids` (fallback list if the rebellion change is not merged).
- [ ] 3.3 Curfew: `banditry_gain_multiplier` in `bandits.set_modifiers` and the order tick.

## 4. Tests
- [ ] 4.1 Fake game tests: start grant, spring grant, start in each season, load round trip of the pick state, refusals, order loss and Curfew math, pit pay-out with and without the law. Update the "Checked by" lines in the delta specs.
- [ ] 4.2 Test scenarios in `mod/InvasionMod/scenarios/tech_tree/`: `picks_roundtrip`, `strip_the_dead`, `disarm`. Run each once in the real game. Back up saves first. Rerun `raid_behavior/pit_loot.py` with the law.

## 5. Docs
- [ ] 5.1 Move engine facts from `notes/` into `docs/wiki`. Update the tech tree wiki page, the affected skills and `CHANGELOG.md` (corpse loot is now opt-in).
- [ ] 5.2 Merge `origin/main` before the archive. Rebase on `update-banditry-rebellion-raid` if it is merged. Archive as the last commit.
- [ ] 5.3 Ask the owner for the follow-up change that updates the F9 menu (common techs, pick count).
