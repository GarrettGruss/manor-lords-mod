# Design: buildings inside the bailey

## Open questions

| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 1 | Run the remaining tests, or fold the spec into spec 12 as "not possible" and close issue #68? | Project owner | Owner reply on the issue |
| 2 | Is the refusal a bailey rule, or only a missing road path inside a ring with one gate? | Spike | Gate-free ring test (task 2.1) |
| 3 | Which reflected flag, if any, changes the result (legacy Q4)? | Spike | Task 2.2 |
| 4 | Does the plot commit skip the check that the mouse path uses, and are its sites ever built? Answered in the legacy note: the commit skips the check, the sites stay unbuilt (30 game days). | Done | Legacy note |

## Decisions

- A fixture with a ring that has no gate may need the owner to build a manor in the game. The owner decides who makes it.
- The old non-goal "no pak change" came from a missing AES key. The key is now set in the environment, so a pak route may be tried if the owner wants it.
