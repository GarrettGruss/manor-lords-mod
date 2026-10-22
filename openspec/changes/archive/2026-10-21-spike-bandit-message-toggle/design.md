# Design: Spike bandit message toggle

## Context
- `mod/InvasionMod/Scripts/features/bandits/world.lua` sends the native negotiation letter: tag `attacking`, then `raider_suggestSettle+<price>`. The game takes the price and does not check it.
- Read first: living spec `openspec/specs/mod/bandits/spec.md` (requirements "The player can buy families back" and "A failed buy-back gives the silver back"), and `docs/wiki/architecture/invasion-features.md`.
- The game shows messages through its message system (letters and notifications). The class that makes bandit negotiation messages is not known yet.

## Candidates
| # | Way | Good | Risk |
|---|---|---|---|
| 1 | Hook the function that creates the message and skip it | No data change | A skipped hook may break the negotiation state |
| 2 | Change or remove a data table row for the message (pak) | Clean | Needs a pak; may remove the text the mod letter uses |
| 3 | A setting or flag on the message class or player | Simple | May not exist |

## Questions the spike answers
1. Which class, function or event creates each bandit negotiation message? List the messages and when they appear.
2. Which of the candidates can switch them off from Lua? Is it per message type?
3. Side effects: does the bandit squad still behave (attack, retreat), and do other letters still show?
4. Does the mod buy-back letter still work with the game messages off?
5. Which way fits the menu of #308 best (the player sees only the mod button)?

## Safety
- Single-player only. No save function. Back up the save folder before runs.
- Do not pass Lua strings to `FName` parameters of objects that may lack them (CLAUDE.md, Safety).
- Do not edit game files or game paks.

## Decision
Owner (2026-10-21): hiding the banner (RemoveFromParent on questMessageElaborate_C, way 4) is enough. The reply letter may stay in the inbox. Engine facts are in docs/wiki/concepts/engine-limits.md. The mod step and test scenario belong to the change for #308.
