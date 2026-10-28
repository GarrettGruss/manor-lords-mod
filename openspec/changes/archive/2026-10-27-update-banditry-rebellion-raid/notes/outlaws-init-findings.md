# Outlaws init in the real game (tasks 2.4 and 2.10)

Test scenario `bandits-outlaws-init` on fixture `playtest-noai` (no pawn, no camp at the start). Runs: `rb-init-6`, `rb-init-7` (pass). Failed runs `rb-init-1` to `rb-init-5` found the order problem.

## Findings
- The init runs by itself 5 polls after the player pawn is seen (log `OUTLAWS pawn created ... camp_units=18 camps=1`). The pawn exists at once.
- **A camp is built by its Brigands.** The first design killed the 18 Brigands and called `demolish(true)` in the same tick. The camp then stayed (`IsConstructed` false, 17 parts) for 300 game s, and 61 calls of `demolish(true)` did nothing (runs `rb-init-4`, `rb-init-5`; a bridge call and `collapseBuilding()` also did nothing). A second `spawnBanditCamp()` with the pawn present gave a camp that was built after one poll, and `demolish(true)` removed it (parts 17 to 0).
- **New order** (run `rb-init-6`): the pawn is made, the camp is built (one poll), the mod kills and hides the 18 Brigands, and calls `demolish(true)` until the camp is gone (35 polls, about 80 game s). Then no living bandit unit and no camp building (`encampment_sites`) are left, a second call does nothing, and in 3 game days the game made no new camp.
- The bridge read of `buildings` on the destroyed camp master crashed the game (spike read after the demolish). The mod keeps only addresses and never reads a camp after `demolish(true)`.

## Pawn survival over a save and a load (task 2.10)
Run `rb-rt-w1` (write, slot `saveGame_57`) and `rb-rt-r1`, `rb-rt-r2`, `rb-rt-r3` (read): after the camp removal and a harness `save_game`, the loaded game had the Outlaws pawn (`bandit_pawn` true) and the init did nothing (no `OUTLAWS` log line). The pawn survives a save and a load.

## Not verified
A second `spawnBanditCamp` after a removal when the pawn is gone, and later bandit raid behavior with a pawn that has no camp (only the rebellion squad was watched).
