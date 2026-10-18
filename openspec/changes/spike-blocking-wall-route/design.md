# Design: a blocking wall route

## Context

Facts are in `docs/harness/14-free-walls/implementation-notes/free-walls.md` (sections "What exactly causes the wall collision", "Fire and damage as a breach", "Where this leaves free walls"). They are not copied here.

## Open questions

| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 1 | Is a wall that blocks units still wanted for the Invasion Mod (design: "Bulwark" defense style)? | Project owner | Owner reply on the issue |
| 2 | Which route ships a blocking wall or a partial breach: a native C++ UE4SS mod, a reflected game call, or a mod rule that slows units at a wall line? | Project owner, after the spike results | Spike tasks 2.1 to 2.3 |
| 3 | Can the planner functions on the pawn (`splitWallsByCastleModule`, `joinWalls`) make a blocking wall with a manor selected? | Spike | Task 2.1 |
| 4 | Does a wall survive a save and a load? | Owner approves the first real `save_game` call | Task 4.1 |
| 5 | How is the wall tool offered to the player (a key on the `commitRoad` hook, or a poll of `wall_state`)? | Project owner | Task 3.1 |
| 6 | Can one wall piece be removed (a partial breach)? No reflected call is known. | Spike | Task 2.4 |

## Decisions already made (not open)

- Burning or collapsing the manor is not the breach method (owner, 2026-10-12).
- Unsafe spike commands and memory tools stay in git behind `HARNESS_ALLOW_UNSAFE=1` (living spec `harness/building-commands`).

## Risks

- A native route needs code outside Lua. This may be out of scope for the project.
- Memory writes to the obstacle list crashed the game when the list was emptied. Do not repeat that in a shipped route.
