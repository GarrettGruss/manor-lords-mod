# Real game runs (slot 2, config.json checked each time)

| Run | Scenario | Fixture | Verdict | Note |
|---|---|---|---|---|
| 20261106-235527-c84c | probe-retinue-native | manor-bailey | pass | native squad + native hire |
| 20261106-235727-0c5c / 20261106-235907-dbcf | probe-retinue-native write / read | manor-bailey | pass | guarded save_game, load: squads 22 and 24 (5 men each) kept, native hire goes on. The kept slot saveGame_60 was deleted. |
| 20261107-003936-ea97 | liege-contracts-fulfil (loan) | manor-bailey | pass | the retinue squad (5 men) is loaned, the militia squad stays, a native 5-man squad returns, banner logged, no banner failure |
| 20261107-003629-e923 | liege-contracts-fulfil (`HARNESS_LARGE=retinue`) | manor-closed | pass | new squad of 5 men, silver unchanged, count 1, id in `retinue_squad_ids` |
| 20261107-003742-4d8e | liege-contracts-window | manor-closed | fail (fixture) | layout checks W1 to W15 pass, including the new reward text. W16, W20 and W24 fail because manor-closed has no storehouse for the goods rewards (clay, ale): not a change of this work. |

Findings:
- `addRemoveSquadRequest` works on a native retinue squad (the loan), no crash.
- The boot of one run (20261107-000453-8d26) failed with `HarnessBoot ended in FAILED`; the rerun passed.
- A first run (20261106-235145-5316) ended with `harness_error: the user's save files changed during the run: new saveGame_35`. No save call was made by this work; another agent's game wrote it.
- The scenarios `liege-contracts-fulfil` families and tribute modes need a fixture with a manor (playtest-noai has none); not run.
