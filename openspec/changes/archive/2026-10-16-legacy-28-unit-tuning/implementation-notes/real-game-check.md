# Real-game check (spec 28)

Date: 2026-10-16. HarnessActions version 53. Run `s28-tune-check` (`--scenario noop --keep-open`), driven with `runlib.tune.TuneClient`. Game stopped at the end.

| Step | Command | Result |
|---|---|---|
| Normal game state | `tune_state` | player 25, bandit 18, ai_lord 91 units; 201 unowned. Bandit mean def 3.333, att 2.667. Player mean def 3.52, att 3.36 |
| Override | `tune_set` player def 77, att 5; bandit def 33, att 6 | `tune_state`: player def 77 att 5, bandit def 33 att 6; ai_lord unchanged (def 0, att 1.868). The units were NOT registered by a harness spawn |
| Later spawn | `spawn_units` 1 squad spearMilitia (32) and 1 squad Brigands (18) | right after: bandit mean def 22.9, player 51.8 (new units at original values). After 3 s: bandit def 33, att 6; player def 77, att 5. The 2 s timer re-applied the override |
| Reset | `tune_reset` | overrides empty. Bandit def 3, att 2.5; player def 6.022, att 3.843: the means of the original values of old and new units |
| Clean cycle | set bandit att 9, then reset | before 2.5, mid 9 (54 of 54 written), reset removed 1 and restored 54, after 2.5 |

Notes
- `tune_set` returned `changed` 0 when the timer or an earlier call had already written the value. This is correct: only a differing value is written.
- A morale override pins morale; the game cannot lower it while the override is active.
- The first `tune_reset` result was lost in a double run of the script. The state after it and the clean cycle show the restore.
