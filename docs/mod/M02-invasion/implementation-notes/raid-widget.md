# Raid widget notes (M02 iteration 05)

- Method: spec 16 `pak-widget-spike.md` and `policy-menu-followups.md`. The widget is a copy of a stock engine widget (`/MoverExamples/Widgets/ControlsDisplay`). The seed widget stays, the graphs are removed, children are added from Python.
- New against PolicyMenu: a `Border` (brush colour dark, 85 percent) wraps the column. `Border.set_content` and the `brush_color` and `padding` properties work from Python. The panel shows well in the game (text stays readable on the land).
- Build steps: `make_raid_widget.py` in the editor (`-ExecutePythonScript`, about 10 s), cook (`-run=cook ... -skipeditorcontent`, 66 s cached), copy `WBP_RaidMenu.uasset` and `.uexp` (6.5 KB and 1 KB) into `modtools/work/raidmenu/ManorLords/Content/HarnessMod/`, `pakmod.py build raidmenu` (8 KB pak). The key was only in the environment of that command.
- Polling: the scheduler tick is 100 ms and the job runs every 200 ms. A real click was caught in two of two runs. If a click is missed on a slow PC, lower `poll_ms`.
- The scenario finds a button by hover (the geometry calls return zero sizes, see spec 16). The scan covers x 0.22 to 0.46 and y 0.30 to 0.96 of the window. Another game window on top of the screen can break it. The scenario is `EXCLUSIVE` (real mouse).
- The pak class path `/Game/HarnessMod/` is shared with PolicyMenu. The asset names differ, so both paks can be installed.
