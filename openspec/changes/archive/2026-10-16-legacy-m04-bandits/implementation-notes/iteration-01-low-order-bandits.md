# M04 iteration 01: notes

Game 0.8.111, fixture `base` (10 families, approval about 71, Public Order 100).

## Spike: does the game keep a written Public Order?
Scenario (since removed) wrote `publicOrder = 50` and read it after each game day. Runs `20261017-213853-d83a` (pass) and `20261017-213728-57b9` (crash on game day 2, UE4SS "Abort signal" in `process_simple_actions`; one crash in 3 runs, not repeated, cause not isolated).
- Written 50, read 50 at once, read 100 after 1 game day, then 100 on every day. So the game does not move the value slowly. It rewrites the value from its own factors about once per game day.
- On `base` the game value is 100 (no factor lowers it).
- Result: a single write does not hold. The mod must write again after each rewrite.

## Design
- The mod keeps `natural_order` (the game's own value) and `written_order` (the last value it wrote).
- Each poll (1 s real time): if `publicOrder` differs from `written_order`, the game rewrote it, so that value is the new natural value. Then the mod writes `natural - debuff` if it differs. The debuff is `ceil((100 - approval) x difficulty)`, order is clamped to 0 to 100. The debuff never stacks, because it is always taken from the natural value.
- The pair is saved in ModState (`bandits_natural_order`, `bandits_written_order`). After a load, a Public Order equal to the saved written value is known as the mod's value.
- Approval stays the game's value. The mod writes Approval only in the test setter.
- Conversion calls `HarnessBandits.homeless_rebel` (mode `home`, template `Brigands`, 2 families, 1 squad of 18). The last family always stays (`min_families_left`).
- Deviation: the tick is a fixed interval of 30 game days (iteration 02 brings the season tick). The poll writes ModState only when a value changes (a write each second may crash the game, see M03).

## Findings
- The rewrite happens once per game day. Between a rewrite and the next poll (at most 1 s) the displayed order is the natural value.
- Approval is also recalculated fast: a written 65 read 71 two game days later.
- The bandit census of `base` shows 18 bandit units before any conversion (a squad from the start).
