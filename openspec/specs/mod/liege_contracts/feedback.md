# liege_contracts feedback

- 2026-11-06 (owner playtest): a Small contract asked for 60 eggs; it should be 20. Tuned `liege_contracts.weight[220]` to 0.4 in `config.lua` (50 x 0.4 = 20 at medium difficulty; 15 easy, 25 hard).
- 2026-11-06 (owner request): hides and pelts, and berries and mushrooms, are interchangeable in a contract (change `update-contract-interchangeable-goods`, #589). The card label for berries is "berries/fungi" so it fits the card. `weight[279]` has no effect now; use `weight[171]`.
