## 1. Picks
- [ ] 1.1 `config.lua` (`tech_tree`): remove `slots_per_level`; add `picks_per_year` 1, `initial_picks` 1. Remove `slots_for_level` from `rules.lua`.
- [ ] 1.2 ModState keys `tech_picks_earned`, `tech_year_seen`, `tech_woods_used`. Add a getter for the season year in `features/invasion`. Yearly grant in the tech tree poll, saved before the log.
- [ ] 1.3 `rules.unlock_refusal`: pick check ("no free pick"); skip the path and order checks for a common tech.
- [ ] 1.4 Update `tech_tree_state` (picks earned and free, common techs).

## 2. Data
- [ ] 2.1 `tree.json` version 2: `common_nodes`, four common laws with `path` "common" and `excludes`, new effect kinds. Update `tree.lua` load and checks.
- [ ] 2.2 `rules.totals` and `rules.enact_refusal`: new flags, the exclusion check, common laws without a path.

## 3. Laws and action
- [ ] 3.1 Strip the Dead: gate the pit pay-out in `raid_behavior` on the law, add bandit and soldier bodies, `strip_the_dead.body_goods` and `order_loss` in config, order write in `bandits`.
- [ ] 3.2 Disarm the Peasantry: home tick in `tech_tree/world.lua` (`consumeGoodNoCheck`, `addToInventory`), `disarm.tick_days` config, log `disarm_homes_missed`. Use `bandits.rebellion_weapon_ids` (fallback list if the rebellion change is not merged).
- [ ] 3.3 Mass Graves: daily clear (`SetActorHiddenInGame`, `Region.corpses:Empty()`), pay overrides to the storehouse, no `K2_DestroyActor`.
- [ ] 3.4 Curfew: `banditry_gain_multiplier` in `bandits.set_modifiers` and the order tick.
- [ ] 3.5 Clear the Woods: command `tech_tree_clear_woods` (`just_die`, hide, `demolish(true)`).

## 4. Tests
- [ ] 4.1 Fake game tests: picks and years, load round trip of the pick state, refusals, exclusion, order loss and Curfew math, pit pay-out with and without the law. Update the "Checked by" lines in the delta specs.
- [ ] 4.2 Test scenarios in `mod/InvasionMod/scenarios/tech_tree/`: `picks_roundtrip`, `strip_the_dead`, `disarm`, `mass_graves`, `clear_woods`. Run each once in the real game. Back up saves first. Rerun `raid_behavior/pit_loot.py` with the law.
- [ ] 4.3 Pictures: Clear the Woods (camp gone), Mass Graves (no bodies). List them in `evidence/README.md`.

## 5. Docs
- [ ] 5.1 Move engine facts from `notes/` into `docs/wiki`. Update the tech tree wiki page, the affected skills and `CHANGELOG.md` (corpse loot is now opt-in).
- [ ] 5.2 Merge `origin/main` before the archive. Rebase on `update-banditry-rebellion-raid` if it is merged. Archive as the last commit.
- [ ] 5.3 Ask the owner for the follow-up change that updates the F9 menu (common techs, pick count).
