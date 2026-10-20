# Design: Wagenburg manor

## Answered questions (owner, 2026-10-19)

| # | Answer |
|---|---|
| 1 | The Wagenburg must NOT change or replace the player's manor. A global pak swap of the manor is out. A per-manor Lua swap of the player's manor is out. |
| 7 | The Meshy models belong to the owner (paid tokens). A public release is allowed. |
| 4 (part) | The first real `save_game` call is approved. The owner has backups outside the harness. A fresh backup and the guarded action are still required (CLAUDE.md, Safety). |

## Route left

The pak swap is global, so it also changes the player's manor. It is out. The only route left is a per-manor Lua reskin (`wagen_apply`) of a manor that the player does not own: an AI lord, invader or enemy manor. This route is not proven. Spec 32 did not study an AI lord with a manor and a wall, and a manor needs a region owner and a manor build. Task 2.1 decides it.

If task 2.1 shows that no AI or enemy manor with a wall exists, or the Lua reskin does not reach it, there is no route left that keeps the player's manor unchanged. Then the recommendation is: stop this change and use the related change `spike-wagenburg-bandit-camp` (#229) as the fallback. Do not invent a new feature here.

## Open questions

| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 2 | Is an enemy or AI camp with a real wall wanted? | Project owner | Answered (owner, 2026-10-20): yes. The ideal flow: the baron AI claims a region, builds a Wagenburg fort in it with a real wall, and garrisons units in it. If that is not possible, fall back to the Wagenburg camp (#229). The owner deferred this work on 2026-10-20. |
| 3 | Does an AI lord build a manor and a wall, and can the Lua reskin reach that manor without the player's manor? | Spike | Task 2.1 |
| 4 | Does the reskin of a non-player manor survive a rebuild and a load, or must Lua apply it again each time? | Spike | Tasks 2.2 and 2.3 (`save_game` approved) |
| 5 | What do a closed gate, defenders on the wall, wall damage and fire do with the wagon look? | Spike | Task 2.4 |
| 6 | Are a gate model, a tower model and a taller wagon wanted? | Project owner | Owner reply; then task 3.1 |

## Decisions

- Engine facts and numbers stay in the legacy notes.
- The user check "by eye" is still open: the legacy screenshots are agent captures.
- The player's manor is never reskinned. A test must prove that the player's manor keeps its vanilla look.
