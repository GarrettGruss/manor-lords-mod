# Proposal: fix-removed-families-bodies

Issue: #580

## Why
`ManorCore.remove_families` kills each family member with `just_die`. The code does not hide the bodies, although the bandits spec says it does. Each body lies on the ground and counts in `Region.corpses`. The owner (2026-11-06) wants the bodies hidden and no dead-bodies counter or notification. This hits liege contracts (send families), the bandit rebellion and vassals.

## What Changes
- After `just_die`, `ManorCore.remove_families` hides each body (`SetActorHiddenInGame(true)`).
- A spike on slot 1 reads the corpse counter and the notification. If hiding does not stop them, the change removes the bodies from `Region.corpses` or uses a native corpse call found by the spike. Never `K2_DestroyActor` (crash list).
- The false comment in `liege_contracts/world.lua` is fixed.

## Impact
- Spec: `mod/core` gets one added requirement.
- Code: `mod/shared/ManorCore/ManorCore.lua`, `mod/InvasionMod/Scripts/features/liege_contracts/world.lua`.
- Tests: fake-game test, real-game test scenario with pictures.
