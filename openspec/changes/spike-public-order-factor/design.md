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

## Owner decision (2026-10-23): route A and route B
- State: the mod keeps `mod_order`. The game keeps its own value.
- Route A: write `publicOrder = game value + mod_order` (clamped 0..100) on every tick, after the game recompute. Test: hold a fixed target for 10 game days, sample the flicker rate, compare a game effect with a control run (`notes/tick-write.md`).
- Route B (backup, not built now): an overlay bar or number on the game's top bar shows `mod_order`. Host candidate: the right group of the top bar (the scale icon).

## Owner decision (2026-10-23): route A accepted
- Route A is the chosen way. Route B is not needed now.
- The mod keeps `mod_order` and the last game value. It writes its own value to `publicOrder` every tick. The game never restores its value, so the mod cannot read the game value after a write.
- Game effects of order (families, approval) did not follow the written value in 10 days. The mod applies its own order effects in mod code (later change).
- Risk accepted: transient values 0 and 100 (about 12 percent of samples).
- Routes tested and closed: new factor row by pak (not possible), `publicOrderMemory` append (no effect), config weight by pak (no effect in 10 days), per-tick write (holds, display only).
