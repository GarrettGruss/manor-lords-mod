# Report of agent group MC

Date: 2026-10-18. Files: six delta specs under `specs/mod/` and `specs/mods/`. `openspec validate backfill-living-specs --strict` shows no error in these files.

## Counts
| Capability | Requirements | Spec scenarios | Without a check |
|---|---|---|---|
| mod/finite_resources | 6 | 10 | 0 |
| mod/tech_tree | 9 | 20 | 0 |
| mod/tech_tree_widget | 8 | 10 | 1 (real mouse clicks) |
| mod/manor_stronghold | 6 | 13 | 0 |
| mods/refugee-waves | 8 | 13 | 0 |
| mods/policy-menu | 6 | 7 | 2 (missing pak, release manifest) |

Checks are test scenarios or fake-game tests. The checks were read, not run.

## Planned iterations that are not built
- M11 (liege_influence) and M14 (plundered_start): not started, no capability.
- M12 `02-pak-ui.md`: open issue #203. Only U1 to U4 are on main and are in the spec. U5 and U6 (real mouse clicks) stay in the legacy folder.
- M10, M12, M13: every iteration file is done. No unbuilt iteration file.

## Legacy claims dropped
- M10 "2 to 4 game years at normal use": the sizes (400, 300, 500) are guesses and the use rate is not measured. Left out.
- M10 "player sees the remaining stock": there is no UI. Left out.
- M10 "clay has no vassal supply": stated only as sizes; no clay tribute requirement.
- M13 "Raiders treat the manor store differently" and the "manor holds" layer: not built.
- M13.03 squads saved by the mod: not built (squad ids are not in mod state).
- M12 "Forced Labor on Walls affects walls": the effect is a stand-in. The spec states only its Public Order and approval values in the data.
- M12 "Veteran Levies has a visible effect": not verified in the game. The spec states only the factor.
- Spec 15 spike material (settle letter, eject, tent placement, rebellion timing): engine facts, not mod behavior.
- Spec 16 spike material (policy system not usable, pak widget method): engine facts.

## Feedback files written
None. No `feedback.md` exists in M10, M12 or M13.

## Doubts
- tech_tree_widget "Mouse clicks" has no real-game check. The same click rule is verified in PolicyMenu (`policy_menu.py`). `widget.py` U5/U6 did not pass.
- `tech_tree/widget.py` is named as the check for the header lines and positions (U1 to U4). The file also holds the unverified click steps.
- Tech tree boon values in the spec scenarios are the shipped data values (TBD in the legacy README). They can change with tuning.
- Level-2 slots, Golden Age, Amnesty and the 4-squad rule are checked by fake-game tests only, not by a real-game run.
- The "Tribute scales finite goods" check is a fake-game test in `test_fakegame_tribute.py`. Tribute itself belongs to the agent that owns `mod/tribute`.
- PolicyMenu has no fake-game test. All PolicyMenu checks need the real mouse (`policy_menu.py`).
- The PolicyMenu requirement "The mod is releasable" also mentions RefugeeWaves. Move it if the release agent writes `harness/mod-releases`.
