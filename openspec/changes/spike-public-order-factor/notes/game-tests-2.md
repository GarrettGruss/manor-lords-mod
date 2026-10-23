# Game tests 2 (runs order2-ctl, order2-e5, order2-e20, order2-cfg; fixture base, slot 0, 2026-10-22)

Player region Nusslohe. Start: publicOrder 42, Approval 71. Sampled every 0.5 s at speed 3 for 10 game days. Day 0 is the start day (205, the control ran on in the same game from day 217).

## Existing entries (read first)
- `summedPublicOrderFactors` (game made, renewed each day): Type 17 effectByPopulation -10.0 count 1, Type 19 +10.0 count 1, window day..day+5.
- `publicOrderMemory` is empty at start. A game-made Type 17 entry in the summed list is -10.0 with count 1, so I appended Type 17, effectByPopulation -10.0, count N, expirationDay day+10.

## A. Control and strength test
| Day | control (stable po / ap) | count 5 | count 20 |
|---|---|---|---|
| 0 to 8 | 42 / 71 | 42 / 71 | 42 / 71 |
| 9 | 40 / 70 | 40 / 70 | 40 / 70 |
| 10 | 100 (one sample) | 40 / 70 | 100 (one sample) |

- Control (no writes): publicOrder is 42 and sometimes shows a single-sample 100 (once or twice per game day). The 100 is a transient value during the game recompute, and is not an effect. A first control run with one sample per day showed the same noise (42, 42, 42, 42, 100, 100, 42, 100, 42, 40, 100).
- Day 9 drop 42 to 40 (Approval 71 to 70) is in the control too. It is natural (population growth).
- With the entry (count 5 and 20) the stable publicOrder is identical to the control on every day. No effect.
- The game rewrites effectByPopulation of the appended entry from -10.0 to -0.04 within one day (-10 / population about 250 to 750), the same as in game-tests.md. count stays 5 or 20. The entry stays after its expirationDay.
- The entry never appears in `summedPublicOrderFactors` (still only types 17 and 19, count 1).
- Verdict: appending to `publicOrderMemory` is safe but does nothing for publicOrder. It is not a way to add an order factor. (Not tried: other Types, `summedPublicOrderFactors` writes, which the game rebuilds each day.)
- Tooltip: not checked (no mouse device).

## B. Config route
- Static: the pak `pakchunk0-Windows.pak` holds `ManorLords/Config/DefaultGame.ini` (plain text, read with repak `get`). Section `[/Script/ManorLords.ApprovalSettings]`, keys `ApprovalFactors[0]` to `ApprovalFactors[33]`. `ApprovalFactors[17]=-1.200000` (unemployment), `[19]=1.000000` (administration). The user file `%LOCALAPPDATA%\ManorLords\Saved\Config\Windows\` only has GameUserSettings.ini and UserSettings.ini (no Game.ini). Not edited.
- Test: pak `orderini_P.pak` with only `ManorLords/Config/DefaultGame.ini` (the original with `ApprovalFactors[17]=-50.000000`), run with `--pak orderini`.
- Result: a `~mods` pak CAN override the config. `GetDefaultApprovalRateForFactor(17)` read -50.0 (default -1.2), index 19 stayed 1.0. So the weights are changeable by pak, for the whole game.
- BUT publicOrder (42, same noise, same day 9 drop to 40) and Approval (71) were unchanged over 10 days, and the summed Type 17 entry stayed -10.0. So `ApprovalFactors[17]` is not what drives the -10 order factor, at least in this save (Approval factor weight, not order factor).
- Pak keeps a full copy of an original game file. It lives only in `modtools/work` (git-ignored). Not committed. The pak was removed after the run.

## Housekeeping
- Raw eval: the deploy of each run resets `allow_eval = false`. I set it to true after each launch and reloaded. Original file restored at the end (cmp equal to `mod/UEBridge/scripts/settings.lua`, backup `backups/settings.lua.order2.bak`).
- The game was stopped with the harness MCP `stop_game` (no game-close script). Fixture slot removed (`fixtures.py uninstall`). Save folder compared with `backups/saves-20261022-233705-order2`: identical. No crash.
