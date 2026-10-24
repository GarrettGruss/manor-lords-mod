# Proposal: spike-militia-corpses-and-camp-removal

Issue: #489

## Why
The owner wants a rebellion where villagers become armed militia, and dead militia leave no lasting bodies or lost weapons. The owner also wants to remove a bandit camp and its bandits after `spawnBanditCamp`, but keep the Outlaws pawn for later rebellions.

## What Changes
Spike only. No code, no delta spec. Notes in `notes/`, lasting engine facts in `docs/wiki/concepts/engine-limits.md`.

## Questions and short answers
- Q1: rallied militia. No reflected call rallies a squad: the Rally button only enters a rally-point mode that needs a real mouse click. `SMUnit:equip` and `unequip` work, but the gear is cosmetic and reverts. Dead militia leave bodies in `Region.corpses`. The weapons of a dead man go back to the storehouse and no goods are lost. Hiding the bodies and `Region.corpses:Empty()` are safe. Disband from Lua did not work. See `notes/q1-militia.md`.
- Q2: camp removal. Yes. `just_die` on the 18 Brigands, hide the bodies, then `SMBuildingMaster:demolish(true)` on the camp removes it (parts 17 to 0, camp sites 1 to 0). The Outlaws pawn survives. No brigands came back in about 28 game days. No crash. See `notes/q2-camp-removal.md`.
