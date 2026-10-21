---
type: Concept
title: Engine limits found by spikes
description: Things the game does not allow from Lua or data, found by spikes and closed as not possible, with the evidence and the reason. Now holds buildings inside the manor bailey.
tags: [engine, limits, bailey, manor, spike]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-19T00:00:00Z }
sources:
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-17-bailey-buildings/README.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-17-bailey-buildings/implementation-notes/bailey-buildings.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-12-manor-exploration/
---
# Engine limits found by spikes

## Buildings inside the manor bailey: not possible

Closed as not possible by owner decision, 2026-10-19 (issue #68, change `spike-bailey-buildings`). No more tests, no fixture and no pak route will be tried. Criterion M2 (wall in a whole town) stays not verified.

Facts that stay true:

- The mouse path refuses a normal building inside the bailey. The ghost is orange with the text "Road Access obstructed". The same building outside the ring is white and is placed (checked on the fixtures `manor-bailey` and `manor-closed`, a valid Large castle).
- The refusing check is native C++. Nine candidate functions were hooked and gave zero events. No data table holds the rule, and no reflected flag that it reads was found.
- A burgage plot committed without the mouse (`plot_field_place`, `addCommitFieldRequest`) skips the check and makes sites inside the ring. Builders never build them (0 of 4 after 30 game days, while 4 of 4 outside plots were built).
- Not separated: a bailey rule, or no reachable road path because the palisade blocks roads (ring with one gate). A gate-free ring test was never run.

Do not plan a feature that needs buildings inside the bailey.
