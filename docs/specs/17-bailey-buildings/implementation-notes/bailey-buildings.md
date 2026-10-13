# Buildings inside the bailey (M2), spike for issue #68

Date: 2026-10-13. Fixture `manor-bailey`, 6 real runs (`s17-bailey-1` to `-6`), probe `harness/scenarios/probe_bailey.py` (modes `plots`, `plots+`). No save function was called.

## Method
- Ring centre: mean of the two wall road middles (10682, -51173). The screenshot shows the plots inside the palisade. The game labels the area "Manor".
- Burgage plots without the mouse: open the tool, `plot_field_place` 2 plots, `addCommitFieldRequest`. Count with `getBuildingCount(3, false)` and read `built` per plot id from `housing_state`.
- Control: 2 plots at the first `tent_find_spot` spot, outside the ring.
- Builders: runs 1 to 3 built nothing anywhere (control failed). Fix in run 4: give the manor the storehouse worker slot (`manor_worker_slot` 45, `manor_assign_worker` x3), put 60 timber into the manor, give 50 of each food good. Then the control plots were built.

## Results
- Plot commit inside the ring: makes sites (count +2 each row, runs 1 to 6). The commit does not apply the bailey rule.
- Builders (runs 5 and 6, 30 and 22 game days): the outside control plots were built (run 5: 2 of 2 by day 15; run 6: 2 of 2 by day 22). The inside plots were NOT built: 0 of 2 (run 5) and 0 of 4 (run 6, two inside rows), still unbuilt after the control was done. So a committed plot inside the bailey stays an unbuilt site.
- Normal building with the real OS mouse (run 6, a free HitchingPost, type 30): the click inside the ring placed nothing (count 1 -> 1). The click outside the ring placed one (1 -> 2). So the mouse path refuses inside the bailey. Q1 answered: yes, refused.
- Not separated: whether builders skip the inside sites because of the bailey rule, or because the sites are unreachable (wall ring with one gate). Not checked.
- The refusing check is still not found: C++, no reflected function (`rule-search.md`). No reflected flag that it reads was found.

## Verdict
Both routes fail in the real game: the mouse is refused inside, and the mouse-free commit makes sites that builders never build. M2 stays not verified. Open: test a flag or a gate-free ring to see if reachability explains the unbuilt plots.
