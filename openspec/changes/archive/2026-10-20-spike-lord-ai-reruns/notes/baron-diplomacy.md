# Baron diplomacy (S11): probe `probe-lord-diplomacy`

Run: `20261019-223202-8611` (pass, 2026-10-19). Records: `probe.jsonl` (26 steps).

## Results

| Step | Result |
|---|---|
| `spawn_ai_lord` | Works. Lords 4 -> 5. |
| `lord_claim` (region Nusslohe) | Works. Claims 0 -> 1. The AI log says "claimRegions: not enough influence" for another lord, so the AI itself does not claim without influence. |
| `lord_declare_war` | Works. The relation to the player gets the tag `at_war`. Friendship and status stay 0. |
| `lord_declare_peace` | Works. The tag `at_war` is removed. War can be declared again after peace. |
| `lord_spawn_army` | Works. One squad (36) is spawned and commanded. |
| Challenge | A challenge starts at `battlefield_BP18`, 90 days. Days go down (90 -> 81 in 6 steps). `contested` stays false. |
| Battle | No fight in 6 steps. `battle_state` shows only the 3 player squads (108 of 108 alive). The lord squad 36 is not in `battle_state`. |

## Not reached

The "challenge lost" path was not reached. The lord army did not come to the battlefield in the watch time. A longer watch, or an army spawned at the battlefield, is needed for that path.
