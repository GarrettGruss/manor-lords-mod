# Gate 2 findings

## Real-game runs (slot 0 and 2, fixture `base-corpse-pit`)
| Test scenario | Run id | Verdict |
|---|---|---|
| `tech-tree-picks-roundtrip` (write) | 20261028-004303-31fa | pass (start pick, no pick in summer, 1 pick in spring, once only, common tech without path, save) |
| `tech-tree-picks-roundtrip` (read, `--save saveGame_53`) | 20261028-005228-0178 | pass (picks, tech and spring counter came back; no second pick in the same spring) |
| `tech-tree-strip-the-dead` | 20261028-011035-d3da | pass (no pay and no order change without the law; with it 1 body: 1 sword, 1 small shield, order -1) |
| `tech-tree-disarm` | 20261028-013342-671c | pass (44 weapons moved, 44 stored; no tick after the repeal) |
| `raid-behavior-pit-loot` (law enacted first) | 20261028-021741-fdd6 | pass |
| `tech-tree-path-choice` | 20261028-013756-10c6 | pass |
| `tech-tree-militia-factor` | 20261028-021501-ffab | pass; flaky: failed in 20261028-014517-3231 and 20261028-020744-c3e0 (M3), and also on unchanged `origin/main` (20261028-021251-610a). The sample unit of `militia_summary` is the first record of a `pairs` loop and changes between reads. |
| `tech-tree-laws` | 20261028-014203-e7ef | fail before L3: the tribute tick calls `raid_world.deposit`, which no longer exists (issue #517, not caused by this change). L1 and L2 pass. |

Slot kept by the round trip (`saveGame_53`) and its coat pictures were deleted after the read run.

## Findings
- Spring is `Season` 1 (winter 0, spring 1, summer 2, autumn 3), see `spring-season.md`. The fixture starts in autumn (day 270).
- A body at the pit has no identity. Only dead raiders that `raid_behavior` tracked can be attributed. Native raid dead (Brigands of `spawnRaiders`) pay the `bandit` loot variants. Villager, militia and soldier bodies pay nothing and cost no order. This narrows the spec text "a bandit or a soldier"; the delta specs and `design.md` say so.
- Bodies that reach the pit while the law is off are consumed with no pay-out, so enacting the law does not pay old bodies.
- The raid keeps losing units after the test kill (the village fights it), so the scenario counts bodies with the pit state counters `consumed` and `looted`, not with `unpaid_other`.
- Disarm: the fixture homes (9 burgage plots) held 20 spears and 20 large shields (militia gear). The tick moved 44 goods and the store kept all of them (`stored=44`). Later the game moved about 4 of them out of the store again (store gain 40 at the end). The game also moves weapons back to homes by itself when the law is off. The tick reads the store before and after the add and logs `disarm_homes_missed` when it kept less.
- `approval` effects (-3 Disarm, -4 Curfew) are totals only, like the approval of the existing laws: `bandits` ignores `approval_bonus` today.
- The old "storehouse" type is 6 in `store_tiers`, but the spike fixture storehouse has `bType` 72. Disarm uses type 6 first, then 72.

## Rebellion change
`update-banditry-rebellion-raid` was not merged when this change was finished. Disarm uses the fallback list `tech_tree.disarm.weapon_ids` = {133, 271} (it switches to `bandits.rebellion_weapon_ids` when that config key exists). The loot override of rule 1 is skipped. The spec scenarios "A rebel body with an override" and "No rebellion" are not checked.

## Owner questions
- Soldier bodies: no loot values (kind `soldier` is empty), and the mod cannot tell soldier bodies apart at the pit.
- The F9 window needs the common techs and the pick count (follow-up change `update-tech-tree-widget-layout`).
