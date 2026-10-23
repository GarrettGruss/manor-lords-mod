# Tick write test (route A), 2026-10-23

Owner decision: the mod keeps its own value `mod_order`. Route A writes `publicOrder = game value + mod_order` after each game recompute, every tick. Route B (only if A fails) is an overlay bar or number on the game's top bar.

## Method
- Probe mod `mod/OrderProbe` (not shipped) and test scenario `probe-order-tick-write` (hidden). `--env ORDER_TARGET=<n>` holds `Region.publicOrder = n` (0..100); -1 only reads (control).
- A loop (100 ms real time, on the game thread) reads `publicOrder`, `Approval` and the family count, then writes the target. 10 game days at speed 3, fixture base, player region Riesenbuckel. Game value at start: 42 (a natural drop to 40 on day 214 is in the control).
- Target 2 = game value 42 minus 40, clamped to 0..100.
- Runs: control `20261023-182031-3a47`, hold `20261023-182228-deea`. Run limit raised with `--max-runs 1000`. Raw eval was not used. No save call. The save folder hash is the same before and after (backup `backups/saves-20261023-order`).

## Flicker (samples that did not read the target)
| Run | samples | read the target | other values |
|---|---|---|---|
| Control | 583 | n/a | 42: 405, 40: 134, transient 100: 44 (7.5%) |
| Hold at 2 | 581 | 513 (88.3%) | 68 (11.7%): transient 0: 57, transient 100: 10, game value 42: 1 |

- The game value 42 was read only once, on the first sample before our first write. After that the game never restored its own value. Our write is kept as the new state.
- The other reads are short transients, about 5 to 6 per game day (one per game hour of the recompute). They are also in the control (value 100, 1 to 9 per day). In the hold run they read 0 (and 100 once per day). The player sees the final stable value: the paused top bar shows 2% at day 5 and day 10.

## Effect check
Measured: family count and approval (the inputs of immigration and family growth).
| Run | families day 209 | day 214 | day 219 | approval |
|---|---|---|---|---|
| Control (order 42) | 10 | 11 | 11 | 71, 70 on day 214 and 215, then 71 |
| Hold (order 2) | 10 | 11 | 11 | identical |
No difference. Order 2 against 42 did not change family growth or approval in 10 days. Other game effects (tithe, tax, unrest, bandits) were not measured. The test shows only that these two do not follow the written value.

## Findings
1. The write holds. The shown value (top bar) follows `publicOrder` within a tick. The game does not pull it back to its own value.
2. Because the game does not restore its value, "game value" cannot be read after we write. The game's own value changes (the 42 to 40 drop) are hidden while we hold. The mod must keep the last game value itself, or write only an offset on the first read. This breaks the formula `game + mod_order` for a longer time: the value we read is our own.
3. Transient values (0 and 100) show for a part of the samples. A reader that samples at a random time, such as a hook inside the recompute, can see them.
4. No game effect followed (families, approval).

## Verdict
A partly works. The display follows the value and holds across polls. A game effect did not follow in the two things measured, and the game's own value is lost while we write. Recommendation: use A only as the display of order (write every tick, keep `mod_order` and the last known game value in the mod). Apply the effects of the mod order in mod code (the mod reads `mod_order` itself), not through the game. Build route B (overlay) only if the owner wants the number without changing the game's own value.

## Route B (recorded, not built)
Overlay a mod bar or number on the game's top bar. The widget that would host it: the right group of the top bar (icons: population, approval 71%, the scale = public order 42%, and a fourth number 91). The spike mod `HarnessUiProbe` and `notes` of spike-playtest-telemetry show that mod widgets can be made at run time. The exact UMG widget name of the scale item was not searched.

## Housekeeping
- `allow_eval` was not changed (file still false). Game stopped by the harness itself after each run. No crash.
