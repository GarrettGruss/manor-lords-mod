# Design: Wagenburg encampment

## Open questions

| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 1 | Does the Wagenburg camp become part of the Invasion Mod (bandit camps, invader camps, both, or none)? | Project owner | Owner reply on the issue; update of the design in `design/` by the owner |
| 2 | Does the Meshy license allow a public release of the model? | Project owner (checks the account terms) | Owner reply |
| 3 | Does a player-built camp (host b, new row in the block 4000 to 4099) place with the real mouse? | Spike | Task 2.1 |
| 4 | Do bandit units get stuck in the ring? Not tested. | Spike | Task 2.2 |
| 5 | Can some camps stay tents while others become Wagenburg (host a changes every camp)? | Spike, owner decides if it matters | Task 2.3 |
| 6 | Does the grey look stay fixed after the spec 33 re-cook? | Spike | Task 2.4 |
| 7 | Where is the saved list of host c places kept, and how does it respawn after a load? | Spike | Task 3.2 |

## Decisions

- The numbers (credits, sizes, counts) are in the legacy notes. They are not copied here.
- Host c needs a mod-owned spawn command. The harness command `encampment_spawn` is a test command only.
