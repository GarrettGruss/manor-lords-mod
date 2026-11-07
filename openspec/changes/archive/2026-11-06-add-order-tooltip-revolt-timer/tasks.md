## 1. Spike
- [x] 1.1 Check if the tooltip can show a text item with no value and no arrow. Record in `notes/text-item-spike.md`.

## 2. Code
- [x] 2.1 `bandits/rules.lua`: `revolt_days`. `bandits/init.lua`: `revolt_status()` with the armed home cache, and `terms.revolt`.
- [x] 2.2 `order_tooltip/rows.lua` and `widget.lua`: rename the row, draw the counter and the blocked item.
- [x] 2.3 `config.lua`: `armed_cache_seconds`.

## 3. Tests
- [x] 3.1 Fake-game tests for rows, widget and the bandits status (cache, no side effect).
- [x] 3.2 Plain Lua rules test for `revolt_days`.
- [x] 3.3 Real run `order-tooltip-revolt-timer` on slot 1 with three pictures: no timer, timer and revolt possible, timer and revolt blocked. Measure the cost of the armed count.
- [x] 3.4 Full fast test set.

## 4. Close
- [x] 4.1 CHANGELOG (root and mod), wiki, evidence README.
- [x] 4.2 Archive: `openspec archive add-order-tooltip-revolt-timer --yes`.
