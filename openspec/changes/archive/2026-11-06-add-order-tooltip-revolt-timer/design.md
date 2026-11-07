## Context
`order_tooltip` adds rows to the game's Public Order tooltip with `approvalFactorWidget_C` (label `DescriptionText`, value `ValueText`, an arrow image). The data comes from `bandits.order_terms()`. The bandits feature keeps the timer (`bandits_timer_start`), the last tick day, `blocked_tick` and the rebellion check.

## Decisions
1. **Data.** `bandits.revolt_status()` returns nil or `{ days, blocked }`. `order_terms()` adds it as `terms.revolt`. The pure part is in `bandits/rules.lua` (`revolt_days`), so a plain Lua test checks it.
   - Timer running and not expired: `days = timer_days - (today - timer_start)`.
   - Timer expired and the revolt was blocked at the current tick count (`retry_due` is false): `days = last_tick_day + tick_days - today`, at least 0.
   - Timer expired and no block yet: `days = 0` (the leave happens at the next poll).
2. **Blocked flag.** Computed only when a timer runs. `needed = leavers_for(families, config)`. Blocked when `needed > 0` and the armed family count is below `needed` (text from `rebellion_block`), or when `world.bandit_pawn_exists()` is false. The check never calls `outlaws.ensure` (it would make a pawn).
3. **Cache.** `armed_families` reads the inventory of every home. The count is cached for `armed_cache_seconds` real seconds (`os.clock`). The cost of one read is measured in the real run and recorded in `notes/`.
4. **Rows.** `rows.build` returns `view.notes`, a list of text items `{ text, label, value, color }`. The counter is first. The widget draws them after the term rows.
5. **Text item without a value.** Default: the same row widget with `ValueText` and the arrow collapsed, and the text in `DescriptionText`. The spike checks that this draws well (picture) and that the text is not clipped. Fallback: a normal label and value row (`Peasants revolt in | 40 days`, `Revolt blocked | 3 of 6 armed homes`). The choice is recorded in `notes/text-item-spike.md`.
6. **Wording.** `Left for banditry` becomes `Peasants revolted`. Banners and logs keep their text.

## Risks
- Reading all homes at each open may lag the tooltip. The cache limits it to one read per few seconds.
- A long text item may be clipped. The spike checks it.
