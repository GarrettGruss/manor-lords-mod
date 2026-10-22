## 1. Implementation (after the spec pull request is merged)

- [ ] 1.1 Record the goods taken by the plunder tick per Hussite raid in ModState.
- [ ] 1.2 Poll the pit `Type 233` and pay the share with `addToInventory`; pay each body once.
- [ ] 1.3 Skip native raids and a missing pit without an error.
- [ ] 1.4 Fake game tests for the record, the share math, rounding, two bodies per poll, native raid and no pit.
- [ ] 1.5 Test scenario `mod/InvasionMod/scenarios/raid_behavior/pit_loot.py` on `base-corpse-pit` with `building_assign_worker type=113`, `spawn_raid`, `kill_units`; picture evidence of the workers at the pit.
- [ ] 1.6 Update the "Checked by" lines, the wiki, the skills and `CHANGELOG.md`.
- [ ] 1.7 Archive the change as the last commit.
