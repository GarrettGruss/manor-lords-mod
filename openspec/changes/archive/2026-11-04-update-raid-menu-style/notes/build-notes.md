# Build notes

- Font and panel: the result of `update-liege-contracts-window-style` is reused (game font `CombinedFont_Mikadan`, flat grey panel).
- Gold values (design decision "choose in gate 2"): the value text block is gold as a whole. Rich text was not used.
- The info line is the difficulty line: label "Raid levels:" in light grey and the value in gold, side by side in an Overlay-centred HorizontalBox. So the menu shows four rows and one info line (the five lines).
- Empty row: the SizeBox `RaidRow<i>` gets `SetVisibility(Collapsed)` and `SetRenderOpacity(0)`. The collapse works in the game (run `20261105-040324-74e2`).
- The three unused `DifficultyButton` Borders of the old widget are removed.
- Build: private UE workspace and private pak `work_dir` (`pakmod.py --config <C:/ path> buildmod InvasionMod`). The log line `built ...InvasionMod_P.pak` appeared.
- Runs: `20261105-040144-9657` (pass; the harness reported harness_error because another agent's fixture save `saveGame_59` was deleted during the run), `20261105-040324-74e2` (pass, final).
