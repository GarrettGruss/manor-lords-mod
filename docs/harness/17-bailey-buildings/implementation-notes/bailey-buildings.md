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

## Retest on manor-closed (2026-10-14, 1 launch, run `s17r-1`)
Fixture `manor-closed`: a valid castle (Large, bailey 1,184 m2, `canConstructCastle` true; spec 12 round 3). One game launch kept open and driven by `harness/tools/s17_plots.py` and `harness/tools/s94_drive.py`. No save function was called. The game was closed at the end. Screenshots are in the git-ignored `runs/s17r-1/screenshots/` of the agent worktree (`C:\Users\garre\development\manor-lords-mod\.claude\worktrees\agent-aabff81e4ec4abfea\runs\s17r-1\screenshots\`).

### Ring
- The ring is one square palisade with one gate (screenshot `start.png`). Its wall roads are 2 wall roads (middles 9487,-50580 and 12185,-52883). `wall_state` gives no polygon, so spots were found with the mouse ground point (`getMouse3d`).
- Inside ground points: (10741,-52509), (10507,-50538). Outside: (10533,-49050), (8186,-48232).

### Normal building, real OS mouse (hitching post, type 30)
- Ghost inside the ring: ORANGE with the text "Road Access obstructed", also next to the inner gate path (`ghost_in.png`, `g_in2.png`).
- Ghost outside, next to the gate: WHITE, no text (`g_out2.png`).
- Real click inside (0.47, 0.60): count 1 -> 1, nothing placed (`click_in.png`). Real click outside (0.58, 0.55): placed (count 2).
- The outside post was built (`constructed` true by day 50). Inside: refused. So the refusal is reproduced on a valid castle. The refusal text is "Road Access obstructed", not a bailey text. It may be the road-access check failing because the palisade blocks roads, and not a direct bailey rule. Not separated.

### Burgage plots, mouse-free (2 rows inside, 2 rows outside, 2 plots each, depth 2000)
- Commit accepted all 4 rows: count 0 -> 8 (`plots_placed.png`: the inside sites are visible in the ring).
- Goods: timber 80 (60 into the manor), fish 30, berries 171 (and 50 each of 172, 230, 296), manor storehouse slot with 3 workers.
- Day 10 after commit: 1 outside plot built, 0 inside. Then a bandit raid burned the outside plots (`day40.png`); they became ruins (type 75, "built"). The control WAS built (day 10 count 1, burning houses at day 40).
- Day 30 after commit (`day50.png`): the 4 inside plots are still unbuilt sites (type 3, `built` false); builders worked elsewhere. 0 of 4 inside built, outside 4 of 4 built (later burned).

## Verdict (retest)
Same result as on `manor-bailey`, now on a valid castle with a working control. Buildings and plots inside the bailey are not built, and the mouse refuses them ("Road Access obstructed"). Reachability (one gate) is still not separated from a bailey rule. Q1 yes. Q2 yes (commit skips the check, but the sites stay unbuilt). Q3 no (not built in 30 days). Q4 not tested. Spec 17 should fold into spec 12 as "not possible with current knowledge" unless the gate-free ring test is wanted.
