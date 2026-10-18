# Design: start sack

## Context

Legacy source: `docs/mod/M14-plundered_start/README.md`. The sack tools and the start flow are in `docs/harness/26-game-start-settings/implementation-notes/claim-victory-test.md` and `start-settings.md`. The sack by share is in `docs/harness/10-invasion-testability/implementation-notes/spike-S6.md`. A depopulation ends the game (`spike-S8.md`), so people must stay alive.

## Open questions

1. Which shares of buildings, stock and people make a village that is recently plundered and still playable? M00 gives no numbers. Answer: a spike with several shares (task 1.1) and the user.
2. When does the start sack run: on the first load or at the first game day? Answer: the spike in task 1.2. A flag in ModState must stop a repeat after a load.
3. Should the first raid story event be a raid of M02? This is the fallback start of M00 and is not part of this change.
4. Do ruins from the sack rebuild at partial cost? This needs the change `add-raid-storage-tiers`.
