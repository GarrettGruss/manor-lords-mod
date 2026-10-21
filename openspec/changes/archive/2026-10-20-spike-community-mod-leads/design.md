# Design: Spike community mod leads

## Open questions
| Question | Who decides | How it is answered |
|---|---|---|
| Can loot follow the gear of dead units (R3)? | A spike | Task 1.1 |
| Does `SetBehaviourStance` change how an AI squad fights or where it stands? | A spike | Task 1.2 |
| Can `spawnCompleteUnit` grow a lord army during a challenge? | A spike | Task 1.3 |
| What do `Squad.camp` and `campLocation` hold while an army waits? | A spike | Task 1.4 |
| Does a `SetStaticMesh` swap work on a finished building, and does collision follow? | A spike | Task 1.5 |
| Which of these does a mod feature need? Drop the rest. | The user | Decided 2026-10-20: follow all five leads (see Decisions). After the runs the notes say which leads a feature needs. |

## Related lead items that other changes own
- M2 data lead (`maxInRegion`, `placedWithin`): see `spike-bailey-buildings`.
- P3 refugee lead (`growPopulation`): done in spec 15.
- Tent placement through the preview and a real click: spec 15.

## Decisions
- 2026-10-20, owner: follow ALL five leads (1.1 real loot, 1.2 stances, 1.3 unit growth, 1.4 camp state, 1.5 building mesh swap). No lead is dropped before its run.
- Results (notes in `notes/lead-1-*.md`): 1.3 and 1.5 work. 1.1 works only on living units. 1.2: the call works, its effect is not shown. 1.4: the fields cannot be read, because a `Squad` struct read ends the game (`HarnessLeads.READ_SQUAD_STRUCT` stays `false`).
