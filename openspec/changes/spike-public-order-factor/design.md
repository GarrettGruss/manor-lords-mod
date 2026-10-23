# Design: Spike public order factor

## Questions
1. Where are the order and approval factors defined? Candidates: a data table (which one), a field in `buildingStats`, a curve, or native code.
2. Can a pak add a new factor row, or a building or effect that applies an existing negative factor? Does the game apply it (real game run with `--pak`)?
3. Can the mod switch such a factor on and off at run time (a building the mod spawns and removes, or a field it toggles), so a feature lowers order by a chosen amount?
4. Is the effect visible in the order tooltip (picture evidence)?
5. Does it persist across save and load (guarded `save_game`; owner informed first)?

## Method
Static search first (extracted JSON, jmap, usmap). Then a pak test. Then a run-time toggle test. Stop early and record the reason if an answer is "no".

## Decision rule
Recommend a way only if it holds across polls (unlike `Region.Approval`) and the player can see it. Otherwise recommend keeping the `publicOrder` write of `mod/bandits`.
