## Why

Issue: #530. A new game starts with 5 families of 2 people, which is 10 people. The kit value "10 villagers" therefore does nothing. The top bar of the game counts families. Owner decision (2026-10-28): the kit must give 10 families.

## What Changes

- The config value `start_kit.villagers = 10` becomes `start_kit.families = 10`.
- At "Begin the game" in a new game, the player region ends with exactly 10 families.
  - Fewer families: the mod adds families with `settleRegion` (5 families a call, as the refugees feature does). New families are homeless families in a tent camp. The camp place is the same as for refugees (woods, else near the village).
  - More families: the mod removes the last families with `just_die` on their members (never `K2_DestroyActor`).
- The kit still runs once, in a new game only, and the flag is stored in the mod state.
- The living spec no longer says "10 people (the count in the top bar)".

## Impact

- Spec: `mod/scenario_settings` (MODIFIED requirements).
- Code: `features/scenario_settings/` (init, rules), `config.lua`, the fake-game test and the test scenario `scenario_settings/start_kit.py`.
