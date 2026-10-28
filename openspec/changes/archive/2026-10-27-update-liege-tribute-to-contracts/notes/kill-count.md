# Kill count for `kill_raiders` (task 1.3)

Question: does `raid_behavior` count the dead units of a bandit camp raid?

Method: test scenario `liege-contracts-progress` (run 20261028-032343-3809). Part 1 forces a small Hussite raid, picks `clear_the_roads` after the raiders spawned, and kills half of them with `raid_behavior_test_kill_raiders`. Part 2 spawns a bandit camp (`spawn_bandit_camp`, 18 to 36 bandit units) and kills 5 bandit units (`kill_units side=bandit count=5`).

Result:
- Raids that the invasion feature tracks: 9 killed, 9 counted (metrics `raid_killed` 9, `raid_kills_counted` 9). The getter is `raid_behavior.raiders_killed()`, a count of the deaths that `rules.update` reported in this session.
- Bandit camp units: 5 killed, 0 counted (metric `camp_kills_counted` 0). Units of a bandit camp are not tracked by `raid_behavior`.

Gap (as the design allowed): the objective `kill_raiders` counts raiders of tracked raids only (Hussite raids and the bandit squad raids that the mod plans). The objective text says "raiders", not "bandits". The count is not saved: after a load it restarts from the number of the session, and the baseline of the contract is taken again at the pick only. A contract that is active over a load keeps its saved progress value, but new deaths count from the session counter (which restarts at 0, so the baseline is clamped at 0). This is a known limit; a later change can save the counter.
