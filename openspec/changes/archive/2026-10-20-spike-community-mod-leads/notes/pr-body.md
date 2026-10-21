## Summary

Change: `spike-community-mod-leads` (#280). Gate: implementation.

Owner decision (2026-10-20): follow all five leads. Result per lead:

- 1.1 Real loot: `GetEquippedID` works on a living unit; a dead unit is not readable, so gear must be read before death. Item map for ids not found. Drop unless gear-based loot is wanted.
- 1.2 Stances: `SetBehaviourStance` works (no error), but the stance cannot be read back and its effect on a fight is not proven. Lead stays open (needs an A/B test).
- 1.3 Unit growth: `spawnCompleteUnit` adds a full squad to an AI lord (32 to 128 units in 3 calls). Keep.
- 1.4 Camp state: `Squad.camp` and `campLocation` cannot be read (a Squad struct read ends the game). Use `lords_state` instead. Drop.
- 1.5 Building mesh swap: `SetStaticMesh` works on a finished building, restore works, collision follows the new mesh. Keep.

Also: new `HarnessLeads` module and probe commands; `parseRequest` of `HarnessActions` now reads `stance`, `component`, `mesh` and `restore` (bug fix).

Closes #280.

## Spec changes

None (no delta spec; `skip_specs` is set).

## Test results

| Check | Run id or test file | Verdict | Key number or range |
|---|---|---|---|
| Loot gear read | 20261021-041104-4698, 20261021-041325-0a68 | pass | 128 of 128 slot reads numeric; dead units unreadable |
| Stance call | 20261021-044002-405f | pass (call only) | `call_ok_aggressive` 1, `call_ok_defensive` 1 |
| Squad struct read | 20261021-041541-74de | crash (finding) | exit 3221226505 at `GetSquad` read |
| Unit growth | 20261021-042957-de11 | pass | squads 1 to 4, units 32 to 128 |
| Camp state | 20261021-043111-bea3 | struct unreadable | army walked ~17500 units, then waited |
| Mesh swap | 20261021-043848-a321 | pass | 22 convex before, 0 after, 22 after restore |
| `test_runlib*` | harness/tests | pass | 527 tests |
| `test_suitelib*` | harness/tests | pass | 116 tests |
| `test_harness_tools*` | harness/tests | pass | 50 tests (1 skipped) |
| `test_reload_mods` | harness/tests | pass | 15 tests |
| `test_pakmod` | harness/tests | pass | 78 tests (1 skipped) |
| `test_coverage` | harness/tests | pass | 26 tests |
| `test_fakegame_*` | harness/tests | pass | 902 tests |
| `test_telemetry_mock` | harness/tests | pass | 19 tests |
| `test_boundary`, `test_save_call_sites` | harness/tests | pass | 2 and 5 tests |
| `lua_syntax.py`, `boot_state_machine.py` | harness/tests | pass | all ok |
| `coverage.py --check-spec` | harness/tools | pass | criteria and spec agree |
| `wiki.py check` | repo-wiki | pass | ok |
| `openspec validate --strict` | spike-community-mod-leads | pass | valid |

## Evidence

Links use the commit SHA: `https://github.com/GarrettGruss/manor-lords-mod/raw/<SHA>/openspec/changes/archive/<date>-spike-community-mod-leads/evidence/<file>`

- `mesh-before.jpg`, `mesh-after.jpg` (run 20261021-043848-a321): bridge before and after the mesh swap.
- `stance-0-before.jpg`, `stance-1-after.jpg`, `stance-2-end.jpg` (run 20261021-044002-405f): the fight is out of view, so they show no stance effect.

## Not verified

- The effect of a stance on a fight (one run, one squad each).
- The item map for equipped ids (item data table not readable through the bridge).
- Camp state fields (`Squad.camp`, `campLocation`): unreadable.
- Risk of `game-close.ps1` (#354).
- What a save and load does with a swapped mesh; navigation and placement after a swap.
