# Q2: removal without a body

| Try | Call | Result |
|---|---|---|
| a, search | usmap and function lists | No emigrate, leave, evict or kick function. Found `Region:removeWorkerFamilyAt(familyID)`, `unassignFamily(familyID)`, `SetFamilyHome(familyID, home, suppress)`, `SMUnit:removeFromFamilyIfHasOne(deleteEmptyFamily)`. |
| a, call | `Region:removeWorkerFamilyAt(0)` (run `corpses-2`) | Family record gone (families 8 -> 7). The 3 people stay alive and walk around (pop and units unchanged). They are not removed. Immigration continued. |
| a+c | the same, then `K2_DestroyActor` on the 3 living people | Calls return true, nothing changes at once, game crashed about 2 game days later: EXCEPTION_ACCESS_VIOLATION reading 0x938. |
| b1 | `SetActorHiddenInGame(true)` on bodies (run `corpses-4`) | Safe. `bHidden` true, no crash for more than 11 game days. Bodies still count in `Region.corpses` and expire like others. Visual effect not shown. |
| b2 | `Region.corpses:Empty()` | Safe. List 6 -> 0 at once, actors stay, no crash for 230 game s. |
| b3 | `K2_DestroyActor` on the 6 bodies after the list was emptied (`corpses-4`) | Crash within seconds: reading 0xe60. Same address with bodies still in the list (run `corpses-3`). |
| c | `K2_DestroyActor` on one living family member, family intact (`corpses-5`) | Crash, reading 0x938, same as a+c. |
| d | `turnToBandit` | Known: only leaves the family (militia spike). `turnToSoldierJoinSquad(squadToJoin: struct)` needs a Squad struct: reading squads crashes (DANGEROUS_ACTIONS). Not tried. No setter for side or owner found (`SetOwner` is the Actor owner). |

Verdict: no clean route. Best available: `just_die` plus hide (plus `Empty()` if the list must be clean). The people are dead (count drops at once), the body is not removed, only hidden (not verified in a picture).
