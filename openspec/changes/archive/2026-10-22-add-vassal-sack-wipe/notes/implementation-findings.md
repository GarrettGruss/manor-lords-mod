# Implementation findings

## Runs of the test scenario `vassals-wipe` (slot 0, fixture `base`)
| Run id | Verdict | Finding |
|---|---|---|
| 20261022-041951-c7e8 | pass | Wipe and restore work. The restore deposited all 3 goods (400 units). The camera looked at the wrong place (the centre came from `getSettledRegionCenter`, which is not a world position). The flag `rebuilding` ended at once, because `settleRegion` itself adds 3 to 4 buildings and the old target (50 percent of 5) was met. |
| 20261022-042514-3045 | crash | Access violation 0x2c right after `VASSALS lost ... wiped`. The collapses and the villager deletion ran in the same tick. Fix: the wipe waits for the next poll after the collapses (the spike did it with a gap of one game day, 2 of 2 passes). |
| 20261022-042821-813a | pass | Wipe one poll after the collapse. `rebuilding` stayed true (target = standing after the restore + 3). |
| 20261022-043309-1c2b | pass | Camera on a building of the region (`K2_GetActorLocation`). Evidence pictures taken. |

## Findings
- The AI did not rebuild in 20 game days after a restore with 5 families and 100 logs, 200 planks and 100 rubble stone (standing 4, rubble 4, unchanged from day 5 to day 20; run 20261022-043309-1c2b). Goods in a standing building are not enough to make the AI rebuild a village with few buildings. Because of this the tribute of a restored vassal does not restart in these runs. This needs an owner decision (see the pull request): clear the ruins (`HarnessBuild.demolish_ruins`), add buildings, or accept that the village stays at 5 families.
- The vassal in the test grows to only 5 buildings in 10 game days (stalled lord), so the wipe test uses 4 ruins of 5 buildings. The rule is tested with 20 buildings in the fake game.
- The restore adds 3 to 4 buildings (`settleRegion`). The `rebuilding` flag ends when 50 percent of the buildings before the wipe stand and at least 3 more than right after the restore (`restore.min_new_buildings`).
- The wipe is two steps on purpose: collapse, then (next poll) delete villagers. A running sack is not saved: a load during a sack ends it, and the vassal stays (the collapsed houses stay ruins).
- Not verified: a bigger village (more than 5 buildings) in the real game, a siege by a real subjugation raid after this change (see the run of `invasion-vassal-targets`), save and load between sack and wipe.
