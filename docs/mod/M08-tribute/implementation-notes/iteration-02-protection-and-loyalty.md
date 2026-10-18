# M08 iteration 02: notes

## Open question 3 of the README
- Loyalty is lost by each raid on the vassal region that the player does not defend, not by time. A defended raid raises it.
- "Defended" is a simple rule on the end of the raid (TBD): the raid was destroyed, or it left because of losses. Any other end (loot, time, or a native leave) is undefended.
- Values (TBD): defended +5, undefended -15. Three undefended raids from loyalty 50 reach 5 and the vassal submits at the next season change (M07.04).

## Findings
- The tribute tick and the loyalty tick run on the same season change in separate polls. The tribute tick can pay one last time before the submission. The next season pays nothing.
- A raid has no vassal target until the follow-up "vassal-targets". Until then only the test command feeds the rule.
- A real raid end reaches the rule through `raid_behavior.watch_end` (fake game test), not yet through a real raid on a vassal.

## Open
- A better "defended" rule (for example the player army stood in the vassal region) is not designed.
