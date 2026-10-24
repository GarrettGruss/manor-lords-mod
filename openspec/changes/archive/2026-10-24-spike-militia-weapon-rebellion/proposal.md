# Proposal: spike-militia-weapon-rebellion

Issue: #482

## Why
The owner wants to know if a militia of villagers can store weapons in its homes, and if those armed villagers can then rebel as bandits. The Invasion Mod needs these engine facts before it can design a weapon-based rebellion.

## Questions (chain: stop when a step is false)
- Q1: Can an agent register a militia squad of spearmen from villagers, without the mouse?
- Q2: Can 30 spears (item 133) and 30 large shields (item 271) be added to the storehouse?
- Q3: Do the registered villagers move the weapons into their homes (not rallied)?
- Q4: Can the armed villagers become bandits, with the weapons taken out of their homes?

## Answers
See `notes/q1-register-militia.md`, `notes/q2-add-weapons.md`, `notes/q3-homes-stock-weapons.md`, `notes/q4-rebellion.md`.
Short: Q1 yes (`PawnCPP:addMilitiaSquad`). Q2 yes. Q3 yes (one spear and one shield per militia member). Q4: `turnToBandit` does not make bandit units; spawning a bandit squad at the homes works, and the bandits leave the map.

## Scope
Spike only. No harness code or mod code was changed. No delta spec.
