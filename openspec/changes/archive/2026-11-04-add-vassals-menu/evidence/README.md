# Evidence: Vassals menu

Test scenario: `mod/InvasionMod/scenarios/vassals_menu/window.py` (`vassals-menu-window`, `--pak InvasionMod --slot 1`, default fixture).
Run id: `20261105-042459-6e9c` (game slot 1, 22 of 22 asserts passed; the run verdict is `harness_error` only because the teardown save-folder guard saw new save files from other agents' fixtures, see `../notes/real-game-runs.md`).
Pictures are the game window, scaled to 1232 x 720.

| File | What it shows |
|---|---|
| `01-vassal-wiped-village-free-slot.jpg` | Header "1 / 3", a thriving vassal, a wiped village with the restore button, a dim free slot |
| `02-restore-disabled.jpg` | 50 silver: the restore button is grey and the hint "Needs 100 silver." is muted red |
| `03-policy-heavy.jpg` | After a click on Heavy: gold Heavy, the hint "Tribute x1.5: 150 ...", a new header tribute |
| `04-rebuilding-village.jpg` | After "Restore the village": status Rebuilding, tribute none, silver 400, header "2 / 3" |
