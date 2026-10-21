# Suppress ways (task 1.3)

Test: modes of the probe command `message_probe` (in `HarnessBandits`). Same test scenario each time, bandit letter at the same step.

| # | Way | Run | Result |
|---|---|---|---|
| 1a | Hook and skip. A UE4SS pre-hook cannot cancel a UFunction. A hook on the Blueprint timer `displayNewDiplomaticMessages` ran about 99 times (`pre` count) and the banner still showed (mode `count`). | `s343-c1` | Not possible. The post callback of Blueprint hooks never fired (`post` 0 in every run). |
| 1b | Pre-hook sets `read` and `wasOpened` on the bandit letters (mode `markread`). The struct write worked (`opened` true). | `s343-m1`, `s343-m2` | Banner still shows, with the number 2. The flags are not the trigger (the game already sets `read` true). |
| 1c | Pre-hook empties InBox when it holds only bandit letters (mode `emptybox`). `InBox:Empty()` worked (InBox size 0). | `s343-e1` | Banner still shows. The banner is not made from InBox. |
| 2 | Data table row (pak): `DT_Para` rows `raider_refuseSettle` and `raider_acceptSettle`. | not run | Not tested (it needs a pak run; the 8-run cap was used). It would also change data that the mod letter uses. |
| 3 | Setting or flag | none found | No reflected setting for letters or banners found in the jmap (`PawnCPP` has `letterCreatorMode` only). |
| 4 | Detach the banner widget: `RemoveFromParent` on every live `questMessageElaborate_C` (mode `hidebanners`). | `s343-b1` | WORKS. `evidence/1-banner-before-hide.jpg` (banner with 2) and `evidence/2-banner-after-hide.jpg` (no banner, same run, 6 s later). It stayed away for the rest of the run (about 30 game seconds). |

Details of way 4: 2 live widgets were found and both were detached (`live` 2, `hidden` 2). The widget objects stay in memory, only the screen element is gone. The game did not crash.
The banner is made once per reply, so the mod must hide it for each letter.
