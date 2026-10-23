## Context

The mod order replaces the natural-plus-debuff model. The game value is unreadable after the first write (wiki, "Public order factors"), so the mod keeps its own value in ModState.

## Decisions

- Pure rules in `rules.lua`: `tick_order(order, manor, homeless, cfg)` and `timer_state(order, timer, now, cfg)`. Fake game tests cover them.
- ModState (saved) holds: mod order, last tick day, timer start day.
- Leave for banditry uses `ManorCore.remove_families`, as the old conversion did. A bandit band spawns only when the game's bandit pawn exists.
- Telemetry: one record per tick with day, order_before, manor_term, homeless_count, homeless_term, order_after (`HarnessTelemetry.register`).

## Open questions

The list is in `proposal.md`. Questions 4 and 5 need a spike in the real game (family removal near the minimum, bandit pawn check).
