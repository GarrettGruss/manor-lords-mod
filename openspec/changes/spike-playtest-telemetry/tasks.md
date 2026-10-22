## 1. Spike

- [x] 1.1 Logger: write and flush each line to `Saved\InvasionMod\logs\session-<time>.log` from a probe; kill the game process; count lost lines. Write `notes/crash-safe-log.md` with run ids.
- [x] 1.2 Clean exit vs crash: find a quit hook or use a heartbeat marker; detect the crash at the next start. Write `notes/crash-detection.md`.
- [x] 1.3 File access: read a save file (fixture copy in the private appdata) and the newest `Saved\Crashes` folder; write a report folder. Write `notes/file-access.md`.
- [x] 1.4 Zip: write a stored zip in Lua with a save inside; measure time in one go and in steps. Write `notes/lua-zip.md`.
- [x] 1.5 Menu: a probe menu with a text box and a checkbox (menu framework of #308). Picture evidence with `ctx.screenshot`. Write `notes/menu-text-box.md`.
- [x] 1.6 Volume: `soak-days` with decision lines at the `decision` level; MB per game year and lines per feature. Write `notes/volume.md`.
- [x] 1.7 Bug replay: for #337, #357 and #325, list the events and state a bundle needs. Write `notes/bug-replay.md`.
- [x] 1.8 Recommend the design of `add-playtest-telemetry` (levels, budget, events, sample rate, report content) and list the open points for the owner. Write `notes/recommendation.md`.

## 2. Close

- [x] 2.1 Move lasting engine facts to the wiki, `CHANGELOG.md` line if a tool changed, archive.
