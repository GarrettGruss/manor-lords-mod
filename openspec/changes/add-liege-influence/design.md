# Design: influence balance

## Context

Legacy source: `openspec/changes/archive/2026-10-16-legacy-m11-liege-influence/README.md`. Decision 9 of M00 is in `design/mod/invasion-mod.md`. The review of the liege rules is `openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/implementation-notes/feasibility-vassals.md`. Silver, wealth and influence payouts by game calls: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-P5.md`.

## Decisions (owner, 2026-10-19)

- The player sends tribute through a pak widget menu. The named command `InvasionMod.liege_send_tribute` stays as the action behind the menu and for tests.
- Influence does not decay and has no cap.
- `influence_per_unit` is 0.1 for now (10 tribute gives 1 influence). It is a value in the feature `config.lua`.
- The player sends silver from the lord's treasury. Not goods, not the regional treasury.
- Start of the feature is approved.

## Menu approach

The menu is a cooked Widget Blueprint in the Invasion Mod pak (skill `harness-pak-mod`, "Widget pak"). Buttons use the click button pattern of `HarnessClickHooks` (`WBP_ClickButton`, "Widget clicks"). The menu script follows the existing widget features `raid_widget` and `tech_tree_widget`. The menu calls the same code as `liege_send_tribute`. The menu shows the influence and the silver of the lord's treasury.

## Open questions

1. How does the player send tribute to the liege: a pak widget menu or a named command? Answered 2026-10-19: a pak widget menu. The named command stays as the action behind it.
2. Does influence decay or have a cap? Answered 2026-10-19: no decay, no cap.
3. How much influence does one unit of tribute give (`influence_per_unit`)? Answered 2026-10-19: 10 tribute gives 1 influence for now (0.1, configurable).
4. What does the player send: silver or goods? Answered 2026-10-19: silver from the lord's treasury.
5. The command name `InvasionMod.liege_send_tribute`. Answered 2026-10-19: accepted.
6. Start of the feature. Answered 2026-10-19: approved.
7. New: how does the player open the menu (key, button, or an existing mod menu)? The owner decides.
8. New: how does the player choose the amount (fixed buttons such as 10 and 100, or a free input)? The owner decides.
9. New: does influence show as a whole number or with a fraction (a tribute of 5 gives 0.5)? The owner decides.
