# Set a high limit (task 1.2)

Run `20261021-052332-b91c` (probe step `limit`, fixture base, slot 1, no save).

The test used the region production limit (the workplace limit rule), not a mine deposit, because no mine exists in the fixture.

| Good | Before | After `setProductionLimit(good, 1000000)` | After 1 game day (40 s at speed 3) | After `setProductionUnlimited` |
|---|---|---|---|---|
| iron ore (14) | not limited, -1 | limited, 1000000 | limited, 1000000 | not limited, -1 |
| salt (145) | not limited, -1 | limited, 1000000 | limited, 1000000 | not limited, -1 |

Verdict: a high production limit can be set and it holds for a game day. This does not change a mine deposit. Not verified: the effect on a real mine, and the workplace screen.
