# Evidence: add-contract-retinue-reward (#591)

All runs on slot 2 (config.json checked). Pictures are 1280 x 714, JPEG.

| File | Test scenario and run | What it shows |
|---|---|---|
| `contracts-retinue-reward-card.jpg` | `liege-contracts-window`, fixture manor-closed, run 20261107-003742-4d8e | The Large card "Cost: TRIBUTE FOR 3 MONTHS, Reward: +1 RETINUE SQUAD"; the loan card shows "Retinue squads: 1". |
| `loan-returned-banner.jpg` | `liege-contracts-fulfil` (loan), fixture manor-bailey, run 20261107-003936-ea97 | The banner "The liege returns your squad (5 men)" after the loan ended (made due with `liege_contracts_loans_due_now`). |
| `retinue-reward-paid.jpg` | `liege-contracts-fulfil` (`HARNESS_LARGE=retinue`), fixture manor-closed, run 20261107-003629-e923 | The world after the reward: the new 5-man squad beside the others. |
