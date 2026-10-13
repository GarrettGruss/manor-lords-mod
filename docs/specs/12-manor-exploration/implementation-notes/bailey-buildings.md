# Buildings inside the bailey (M2), spike for issue #68

Date: 2026-10-13. Fixture `manor-bailey`, 2 real runs (`s17-bailey-1`, `s17-bailey-2`), probe `harness/scenarios/probe_bailey.py`. No save function was called.

## Method
- Centre of the wall ring: mean of the two wall road middles (10682, -51173). The screenshot shows the plots at the ring edge, inside the palisade.
- Open the burgage tool, `plot_field_place` 2 plots, `addCommitFieldRequest`. Count with `getBuildingCount(3, false)`.
- Control: the same 2 plots 90 m east of the centre, outside the ring.
- Run 2 also gave 50 each of food goods (171, 172, 230, 296) and watched 20 game days.

## Results
- Inside the ring: the commit made 2 plot sites (count 0 -> 2). Outside: 2 more (2 -> 4). So the mouse-free commit does not apply the bailey rule. This matches the earlier finding that the commit accepts odd places.
- Q3 (are they built?): NOT answered. After 8 days (run 1) and 20 days (run 2), 0 of 4 plots were built, inside and outside alike. The village in this fixture does not build (no builders working, 5 homeless, food 0 at save). The control failed, so the result says nothing about the bailey.
- Normal building by the OS mouse inside the ring: not tested (no launches left worth the cost; the probe has no mouse mode).
- The refusing check: still not found. It is C++ with no reflected function (see `rule-search.md`). No reflected flag was found to toggle.

## Decision
Spec 17 is dropped. The plot commit route shows that plot sites can exist inside the bailey. Open step for a later spike: use a fixture where builders work (for example `base` plus a manor), then repeat the inside/outside test and place a non-plot building with `place_building`.
M2 stays not verified.
