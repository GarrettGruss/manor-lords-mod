## Context

Spike result (`notes/spike-native-retinue.md`): `PawnCPP:InitializeEmptyRetinueSquad(region)` adds a native empty retinue squad. `SMBuildingMaster:hireExtraRetinue()` then hires into it at the native cost. The squad and its men survive a save and a load. No safe read tells a retinue squad from another squad.

## Decisions

1. **Native squad, no mod save code for the squad.** The reward calls `retinue.add_native_squad(men)`. It adds the silver that `men` hires cost (so the reward is free), calls `InitializeEmptyRetinueSquad`, then `hireExtraRetinue` once for each man, and checks the men count. If fewer men were hired, the function takes back the silver of the hires that did not happen, and returns a reason. The caller logs it and counts it in `failed_rewards`.
2. **Retinue squad ids are kept in mod state.** A string key `retinue_squad_ids` (ids separated by dots, ModState text form). The ids are stable across a load (spike). The feature adds the id of the manor bound squad at each tick, and the ids of the squads that the reward makes. A squad counts as retinue only when its id is in the list. The mod squads of manor_stronghold (template `retinue_tier1`, known to the helper registry) also count as retinue.
3. **Cap 4.** The integer key `contracts_retinue_squads` counts the reward squads (config `retinue_squad_cap`, owner decision 2026-11-06). `reward_allowed("retinue_squad")` is false at the cap, so the offer holds no such reward. A fulfilment at the cap pays King's Favour (the amount of the `kings_favour` row), as `law_slot` does.
4. **Loan.** `loan_candidates` keeps only squads with an id in `retinue_squad_ids` and living men. None: reason "Needs a retinue squad". The loan record template is `retinue` for a native squad, or the registry template for a mod squad. The return is a native squad for `retinue` and `spawn_squad` otherwise. The returned squad has the same men and mean experience. The config `loan_templates` goes away.
5. **Which squad is loaned (owner question).** The smallest retinue squad: it costs the player least.
6. **Banner.** When a loan returns, `ManorCore.show_banner("The liege returns your squad (N men)")` runs in the tick that returns it. A failed banner is logged and does not stop the return.
7. **Card text.** Reward: "+1 retinue squad". The data row is `{ "kind": "retinue_squad", "min": 1, "max": 1 }`; the saved letter is `r`.
8. **Native limit.** Native recruiting stops at 12 men for each squad (code constant). The owner decides in the pull request whether this is enough.

## Risks

- `addRemoveSquadRequest` on a native retinue squad (the loan) was only tested on script squads. The test scenario checks it in the real game.
- The squad id list can miss a squad that the player made by hand and replaced before a tick (poll_ms apart). The loan then does not see it. This is accepted.
