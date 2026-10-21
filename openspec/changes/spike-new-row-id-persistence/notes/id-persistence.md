# Row id persistence results (spike #284, tasks 1.1 to 1.3)

Date: 2026-10-20. Real game, single player, game slot 2, base fixture. Pak `rowid` (made fresh from the game paks with
`harness/tools/s127_make_ids_json.py`): `buildingStats` rows 126, 486, 1000, 2000, 32767, 65536 cloned from row 30 (hitching post),
`DT_Upgrades` rows 117 (offered by 486, `upgradesInto` 126) and 118, and the names `buildingID_<id>`.
Test scenario: `harness/scenarios/probe_row_id_persistence.py` (hidden, real mouse). Save only through `save_game`.

## Runs
| Run id | What | Result |
|---|---|---|
| `rowid-write-a` | place 126, 32767, 65536, 486; build; use upgrade 117; `save_game` (slot saveGame_53) | Placed 126, 32767, 486 and built them. 65536 was blocked at the chosen click spot (a bad spot, not an id problem). Upgrade not finished. |
| `rowid-write-b` | same, better spots | All four ids placed and built. Upgrade request accepted. Save written (saveGame_57). |
| `rowid-read-a` | load saveGame_57, count buildings of each id, watch the upgrade for 40 game days | All four ids load and keep their buildings (see 1.1). |
| `rowid-lord-a` | `probe-lord-village` with the pak, AI lord village, 30 game days | pass, no crash (see 1.3). |

## 1.1 Save and load of a building with a new id: PASS
- Ids 126, 32767 and 65536 (and 486) were built, then saved with the guarded action `save_game`, then loaded.
- After the load each type still has 1 built building (`building_sites` counts), and the row is read (`building_stat` kind 126: `bVisibleInUi` true, `maxHp` 50).
- The game did not crash at save or at load. 1000 and 2000 were not placed (the range 126 to 65536 is covered by 126, 486, 32767, 65536).
- Save guard: `rowid-write-b` reports "the user's save files did not change" and the launcher hash of the user save folder was equal before and after (`user_saves_sha256` ca9f0c74fc54 in `rowid-lord-a`; the write and read runs report the same message). The kept slots were deleted by hand after the check. The save folder was backed up before each saving run (`SaveGames-backup-20261020-224351`, `-225440`, `-230339`).

## 1.2 New upgrade row: PARTLY
- Row read: `upgrade_stat` 117 gives `upgradesInto` 126, `bUseOnlyOnce` true, as in the pak.
- `plot_upgrade` (addUpgradeRequest) on a building of id 486 with upgrade 117 was accepted. The building then shows the cost goods of the new row (2 timber (16) and 6 planks (17)) in `needs`, so the game reads the new row.
- The pending upgrade state survives the save and the load (same `needs` after the load).
- NOT seen: the upgrade finishing (486 turning into 126). 20 game days before the save and 40 game days after the load (stock of planks and timber given): the `needs` stayed and the type stayed 486.
- Cause not found. No control run with a vanilla upgrade on a non-plot building was done, so the cause may be the hitching post clone (no builder work for an upgrade of this building) and not the id. It is not proven that a new upgrade id works to the end. This needs a spike with a control (for example vanilla upgrade 14 on a vanilla stable), or a decision by the user.

## 1.3 AI lord village with the new ids in the pak for 30 game days: PASS
- `rowid-lord-a`: pass, no crash, no new crash folder in the real `Crashes` folder.
- Lord debug logs (`debugLog_AI_construction`, general, tactics) have no error line. The only "failed" lines are `AI_build failed to find place: LoggingCamp, Sawpit, BurgagePlotTool`, which are normal (no place found), not an id error.
- The lord village stayed at 5 buildings and 5 families and made no `AI_build` line in 30 days. No new id was built by the AI: the ids exist in the table, and the AI ignores them. This was not compared with a run without the pak.

## Verdict
No id range failed. Task 2.1 is not needed for the ids. Open: the completion of an upgrade with a new row (1.2).

## Not verified
- Ids 1000 and 2000 in a save, a mesh or blueprint other than the hitching post, and an AI lord that builds a new id.
- A run of the lord village without the pak (control for the build count).

## Tool changes
- `HarnessBuild.MAX_TYPE` and `actions.MAX_BUILDING_TYPE` raised to 70000 (both capped at 600 and 300).
