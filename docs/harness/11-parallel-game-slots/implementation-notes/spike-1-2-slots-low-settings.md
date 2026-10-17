# Spikes 1 and 2: slot folders, 2 and 3 games at once, low settings (2026-10-17)

Tools: `harness/tools/spike11_slots.py` (build slots, start N workers) and `harness/tools/spike11_worker.py` (one game).
Each worker starts a NEW game (no fixture, so nothing is installed in the user's save folder), waits for READY,
runs 20 s at speed index 1 and 20 s at index 3, then stops the game. Results: `runs/spike11-*.json` and `runs/spike11-*.out`.

## Slot folder (spike 1)
- Layout: `slots/<n>/Manor Lords/`. Win64 is a full copy. `Content/Paks` is a real folder with hard links to the 20 game paks
  and a copy of `LogicMods`, so each slot has its own `~mods`. `Engine`, `Plugins`, `Content/Movies` and `Content/Slate` are junctions.
- Disk: about 0.6 GB per slot (free space went from 317 GB to 316 GB for two slots). `du` shows 15 GB because it counts hard links.
- A slot boots to READY with all harness mods (HarnessBoot log, bridge works). Boot 31 to 40 s alone, the same as the game folder.
- No single-instance block: 3 games run at once.

## The game ignores the private LOCALAPPDATA for its settings
- A `GameUserSettings.ini` and `UserSettings.ini` written into the private appdata had no effect: the window stayed 2560x1440.
- The game reads its settings from the REAL `%LOCALAPPDATA%\ManorLords\Saved\Config\Windows\UserSettings.ini` (game keys such as
  `r.setres`, `t.MaxFps`). This is like the saves (spec 06 `fixture-load-bug.md`).
- **The game also WRITES that file.** Console commands sent through the bridge (`scalability 0`, `t.MaxFps 30`, `r.Streaming.PoolSize 400`,
  `r.VolumetricFog 0`, ...) were saved into the user's real `UserSettings.ini` (10:13). `rtsSettings.sav` in the real save folder also changed.
  Copies: original text and the changed files are kept for the restore; `rtsSettings.sav` matches the backup `runs/manual-save-backup-20261015-223600`.
  Rule from now: never change a cvar in the live game through the console. It is a write to the user's settings.

## Numbers
| Test | Settings | Boot s | Clock rate x1 / x8 | GPU dedicated per game | GPU total peak (8 GB) | RSS per game |
|---|---|---|---|---|---|---|
| 1 game | user (high, 1440p) | 32 to 56 | 1.00 / 7.94 | 2507 MB | 4.6 GB | 3.3 to 3.6 GB |
| 1 game | live low (console) | 32 | 1.00 / 7.91 | 2172 MB | 4.6 GB | 3.7 GB |
| 2 games | live low | 41, 41 | 1.00 / 7.91 | 2153, 2213 MB | 7.0 GB | 2.6, 2.8 GB |
| 3 games | live low | 53 to 58 | 1.00 / 7.92 | 1468 to 2152 MB | 7.7 GB | 1.8 to 2.7 GB |
| 3 games tiled | live low | 40 to 49, then 88 (repeat) | 1.00 / 7.78 to 7.90 | - | 7.8 GB | - |

- Baseline GPU use with no game: about 2.0 GB (desktop and other apps).
- Low settings save only about 0.3 GB of GPU memory per game. The texture pool is not the main cost. The 8 GB card is the limit at 3 games.
- RSS per game is 3.3 to 3.7 GB alone, not the 1.3 GB in the README. With 3 games the RSS drops (Windows pages memory out); free RAM before the test was 6.6 GB of 16 GB.
- The clock rate stays full with 3 games. Boot gets slower (one sample of 88 s; not explained).

## Windows and the loading screen
- Launch arguments `-windowed -ResX=1280 -ResY=720` work: the game starts in a 1280x720 window, no fullscreen screen at start.
- `-WinX` and `-WinY` are ignored (windows cascade at 38, 76). `SetWindowPos` moves the window (verified).
- At the map load the game applies the real user settings again: the window becomes 2560x1440 windowed and centred.
  The spike then sent `r.setres 1280x720w` and moved the window again. Result: tiles at (0,0), (1280,0), (0,720). The outer window is 1302x776, so tiles must step by the outer size.
  But `r.setres` is a console write (see above), so this method is NOT allowed.

## Verdict
- Concurrent games work: 2 games are safe; 3 run, at the GPU memory limit.
- Per-run settings are not possible with the private LOCALAPPDATA. Options, not tested:
  1. A second Windows user account for the harness, so the game has its own real config and save folder (also fixes the shared save folder, gap 1 of `feasibility-review.md`).
  2. Launch arguments only (`-windowed -ResX -ResY`), and accept the 2560x1440 window after the map load; then move it with `SetWindowPos` without resizing.
  3. Ask the user to set the game itself to windowed 1280x720 and low settings.
- OS mouse scenarios: one shared cursor and focus. They stay `EXCLUSIVE`, or they run next to non-mouse games when no window covers theirs.

## Not verified
- Scenarios from fixtures in parallel (gap 1). Pak A/B in slots (`~mods` per slot). Crash in one slot while others run.
