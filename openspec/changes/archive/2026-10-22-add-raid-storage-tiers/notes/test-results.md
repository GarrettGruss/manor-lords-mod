# Test results (implementation)

| Check | Run id or test file | Verdict | Key number or range |
|---|---|---|---|
| Baron steal, small lord raid | `20261022-045654-d4b7` (`raid-behavior-baron-steal`, slot 2) | pass | stolen 100 = goal 100 on the first look (about 18 raiders x 10); never above the goal over 26 days |
| Manor store safe in a baron raid | `20261022-050248-6076` (`raid-behavior-storage-tiers`) | pass | manor stone 100 at every day (min 100); stolen 100 from tier 1 |
| Game raid has no mod steal | `20261022-050804-c72a` (`raid-behavior-storage-tiers`, `RAID=game`) | pass | tracker has no raid, stolen 0; the game robbed the manor store (min stone 76 of 100), accepted by the owner |
| Carry cap, again | `20261022-051650-0b90` (`raid-behavior-carry-caps`) | pass | - |
| Role leave, again | `20261022-052209-1346` (`raid-behavior-role-leave`) | pass | - |
| Fake game tests | `harness/tests/test_fakegame_*.py` | pass | 897 tests (9 new in `test_fakegame_raid_behavior.py`) |
| Other test groups, `test_boundary`, `test_save_call_sites`, `lua_syntax.py`, `boot_state_machine.py`, `coverage.py --check-spec` | harness/tests | pass | - |
| `openspec validate add-raid-storage-tiers --strict`, `wiki.py check` | CLI | pass | - |

## Findings
- The steal goal is reached at once: 18 raiders far from the marker take 10 each, so 180 would be wanted and the goal (100) cuts it. The rate per unit (10 a day) makes the day-by-day spread short. The owner may want a lower rate or a per-raid rate (open).
- The battle marker of a lord raid is the anchor (the manor); units spawn 50000 units away, so they steal from the first look.
- The mod plunder tick (lord raid, units near the manor) now also takes from tier 1 stores only.
- Raid size to goal: by raid kind (plunder 100, great 300). Difficulty scaling is not built (open questions 1 and 4 of `design.md` are not answered).
- Which tier 1 store is robbed: the store that holds most goods first (open question 2 not answered).
- 1 unit = 1 cm is still not checked against a known length.
