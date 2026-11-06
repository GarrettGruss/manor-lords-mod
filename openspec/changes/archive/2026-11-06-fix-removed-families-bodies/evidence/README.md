# Evidence

Test scenario `removed-families-bodies` (`mod/InvasionMod/scenarios/liege_contracts/removed_bodies.py`), fixture `playtest-noai`, slot 1. The camera looks at the first person that dies.

| File | Run | What it shows |
|---|---|---|
| `fix-before.jpg` | `20261106-140343-6d10` | Before the removal. |
| `fix-after.jpg` | `20261106-140343-6d10` | 4 game s after removing 2 families (6 people): no bodies, no corpse notice, top bar unchanged. |
| `fix-after-days.jpg` | `20261106-140343-6d10` | 3 game days later, same view. |
| `control-after.jpg` | `20261106-140856-36ad` | Control (old behaviour, `HARNESS_CONTROL=1`), same moment. Bodies are small on screen. |
