# Regional wealth write path (task 1.1)

Question: can the mod raise `Region.regionalWealth`, and does the value hold after a game day?

Method: the reward kind `regional_wealth` calls `Region:addRegionalWealth(amount)` from Lua (`world.add_regional_wealth`, game thread, read back before and after). The UFunction is the one that the harness action `add_regional_wealth` already called through the bridge (123 to 148, archived `actions-catalog.md`). Test scenario `liege-contracts-fulfil` fulfils a Small contract that pays 60 regional wealth, then runs one game day.

Result (runs 20261030-183650-7d2b and 20261030-184053-c309): the wealth went from 91 to 151 (+60), `failed_rewards` 0, and it was still 151 after one game day (metrics `wealth_before`, `wealth_after`, `wealth_after_a_day`).

Decision: the Small reward pool keeps the regional wealth row. Not checked: how the game HUD shows the value (no picture of a wealth panel was taken), and a long run of many game days.
