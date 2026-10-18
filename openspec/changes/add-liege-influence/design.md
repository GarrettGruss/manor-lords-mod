# Design: influence balance

## Context

Legacy source: `openspec/changes/archive/2026-10-16-legacy-m11-liege-influence/README.md`. Decision 9 of M00 is in `design/invasion-mod.md`. The review of the liege rules is `openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/implementation-notes/feasibility-vassals.md`. Silver, wealth and influence payouts by game calls: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-P5.md`.

## Open questions

1. How does the player send tribute to the liege: a pak widget menu or a named command? The first step uses a named command. The menu is a later change.
2. Does influence decay or have a cap? The user decides.
3. How much influence does one unit of tribute give (`influence_per_unit`)? M00 gives no number. The value is TBD and tuned in playtests.
4. What does the player send: silver or goods? The user decides.
5. The command name `InvasionMod.liege_send_tribute` is a proposal.
