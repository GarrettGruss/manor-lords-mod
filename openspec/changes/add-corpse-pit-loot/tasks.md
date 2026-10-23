## 1. Implementation (after the spec pull request is merged)

- [x] 1.1 Record the goods taken by the plunder tick per Hussite raid in ModState.
- [x] 1.2 Poll the pit `Type 233` and pay the share with `addToInventory`; pay each body once.
- [x] 1.3 Skip native raids and a missing pit without an error.
- [x] 1.4 Fake game tests for the record, the share math, rounding, two bodies per poll, native raid and no pit.
- [x] 1.5 Test scenario `mod/InvasionMod/scenarios/raid_behavior/pit_loot.py` on `base-corpse-pit` with `building_assign_worker type=113`, `invasion_force_next` (a Hussite raid), `raid_behavior_test_kill_raiders`; picture evidence of the workers at the pit. Real run 20261023-032125-a80d passed; evidence in `evidence/`; notes in `notes/real-run.md`.
- [x] 1.6 Update the "Checked by" lines, the wiki, the skills and `CHANGELOG.md`.
- [x] 1.7 Archive the change as the last commit.
