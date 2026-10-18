# Design: Spike community mod leads

## Open questions
| Question | Who decides | How it is answered |
|---|---|---|
| Can loot follow the gear of dead units (R3)? | A spike | Task 1.1 |
| Does `SetBehaviourStance` change how an AI squad fights or where it stands? | A spike | Task 1.2 |
| Can `spawnCompleteUnit` grow a lord army during a challenge? | A spike | Task 1.3 |
| What do `Squad.camp` and `campLocation` hold while an army waits? | A spike | Task 1.4 |
| Does a `SetStaticMesh` swap work on a finished building, and does collision follow? | A spike | Task 1.5 |
| Which of these does a mod feature need? Drop the rest. | The user | Ask before task 1.1. |

## Related lead items that other changes own
- M2 data lead (`maxInRegion`, `placedWithin`): see `spike-bailey-buildings`.
- P3 refugee lead (`growPopulation`): done in spec 15.
- Tent placement through the preview and a real click: spec 15.
