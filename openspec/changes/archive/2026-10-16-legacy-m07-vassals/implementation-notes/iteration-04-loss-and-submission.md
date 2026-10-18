# M07 iteration 04: notes

## Findings
- Submission works with the existing war and peace calls: `declareWar(player)` gave `at_war` and the player was in the enemies of the lord at once; `declarePeace` ended it (the same calls as in M07.02).
- Taking land from a vassal lord in the real game is dangerous: clearing the owner and writing another lord as owner both crashed the game within seconds (native frames, one run each). Both leave the vassal lord without a region while its AI timers run. The fallback capital (M06.03) did not crash with an owner write to the player. A difference may be that the player pawn has no AI timers.
- So the mod frees the slot and lets the lord keep the land. This is the "independent neighbor" answer to M00 question 8 (what the land becomes), TBD.
- The loss event is the single entry for M09: `vassals.on_lost(listener)`. The invasion feature (M02.03 subjugation) can call `lose_vassal(slot, "taken")` when its raid wins a vassal region.

## Open
- A real capture is not tested: the harness has no way to make an invader win a vassal region yet.
- The submitted vassal does not pay the invader.
- Loyalty loss from raids (M08.02) will push vassals to submit.
