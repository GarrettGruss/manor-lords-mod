## 1. Code
- [x] 1.1 `bandits`: read "manor built" (reuse `HarnessManor.manor_state()`), pass it to `tick_order`; manor term is 0 without a built manor; add `manor_built` to the tick record, log line and telemetry.
- [x] 1.2 `order_tooltip`: no `Manor` row when the manor term is 0.
- [x] 1.3 `order_tooltip`: tint the arrow image green for a positive row and red for a negative row (find the right call in the real game; record it in `notes/arrow-colour.md`).

## 2. Tests
- [x] 2.1 Rules tests: tick with and without a built manor, with `order_bonus`.
- [x] 2.2 Fake-game tests: row list without a manor, arrow colour for each sign.
- [x] 2.3 Real run (extend `bandits/order_tick.py` and `order_tooltip/rows.py`) with a picture of a green up arrow.

## 3. Close
- [x] 3.1 CHANGELOG (Fixed), wiki, evidence README.
- [x] 3.2 Archive: `openspec archive fix-public-order-manor-term --yes`.
