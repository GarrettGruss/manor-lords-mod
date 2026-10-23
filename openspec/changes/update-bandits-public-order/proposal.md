## Why

Issue: #424. Design: `design/mod/invasion-mod.md` (pillar 1, order is the goal; pillar 3, unrest grows inside). Continues the spike `spike-public-order-factor` (#403).

The owner played the bandits feature on 2026-10-23. The old debuff (`order = natural - (100 - approval) x level`) held the order at 0 at approval 50 and level 2. The season-change conversion failed with "no pawn for side bandit", because the game settings had no bandit camps (`mod/shared/HarnessBattle/HarnessBattle.lua:173` needs the game's bandit pawn).

The spike found that a per-tick write of `Region.publicOrder` holds, and that game factors cannot be changed from data (`docs/wiki/concepts/engine-limits.md`, "Public order factors"). So the mod keeps its own order value and applies its own rules.

## What changes

Owner decisions (2026-10-23):

1. The mod keeps its own public order value (mod order). It overwrites `Region.publicOrder` with it every tick. Flicker is accepted (#403).
2. Public order ticks every 30 game days. Each tick: +10 from the manor, and -5 for each homeless villager. Each tick is logged in the telemetry (day, order before, manor term, homeless count, homeless term, order after) and in a `HarnessLog` line.
3. When public order drops below 25 percent, the mod starts a 90 game day timer. When the timer expires, 18 villagers leave to become bandits.
4. When villagers leave for banditry, public order rises by 25.
5. The mod public order starts at 100 in a new game.

This replaces the order debuff and the season-change conversion roll with order bands.

## Open questions (default in brackets, none blocks the work)

1. Clamp to 0..100 [yes].
2. Does the timer stop when order rises to 25 or more before it expires [yes, it resets].
3. Does the timer restart after the 18 leave, if order is still below 25 [yes, after the +25 is applied].
4. Fewer than 18 villagers, and a minimum left [at most all but 1 family leave].
5. What "leave to become bandits" spawns when no bandit pawn exists [they leave the map; the mod spawns a bandit band only if the bandit pawn exists; otherwise it logs it].
6. Are game factors (unemployment and others) ignored [yes, only mod terms count].
7. Units of the 30 day tick and 90 day timer [game days, 40 game seconds each].
8. Tech tree modifiers `order_bonus` and `approval_bonus` [keep `order_bonus` as an added term to the manor term; drop `approval_bonus`, which has no use now. The owner may prefer to drop both].
9. Raid levels (#404): the old debuff used the level as a factor [drop the level from the order rules; #404 may add a term later].

## Non-goals

- No change to buy-back and refund rules.
- No change to game factor weights (not possible from data).
- No new bandit models or camps.

## Impact

- `mod/InvasionMod/Scripts/features/bandits/` (rules, init, world, config), ModState (tick day, timer, mod order), telemetry metric, test scenarios, `CHANGELOG.md`, wiki.
- Living spec `mod/bandits` (see the delta spec).
