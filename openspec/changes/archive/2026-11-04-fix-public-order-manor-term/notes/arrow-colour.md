# Arrow colour and manor check

- The row image has a dark red default tint for both signs. `Image:SetColorAndOpacity(<row colour>)` after the add gives a green arrow for a positive row and a red arrow for a negative row (run `20261105-014942-c083`, picture in `evidence/`). The red arrow of a negative row is checked only by the fake-game test.
- Manor detection: `HarnessManor.manor_state()`, first module with `built = true` (same rule as liege_contracts).
- The default fixture `base-corpse-pit` already has a built manor, so the real run did not show the no-manor case or a construction site. The scenario `order-tooltip-rows` covers them when the fixture has no manor. Not verified in the real game.
- The tooltip icon position in `order_tooltip/rows.py` was moved to (0.711, 0.065): the old value missed the icon in the 2582x1440 window.
