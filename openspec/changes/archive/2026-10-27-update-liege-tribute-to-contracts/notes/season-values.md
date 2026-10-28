# Season values (task 1.4)

`TemporalComponent.Season` (read by `features/invasion` as `current_season()`): winter 0, spring 1, summer 2, autumn 3. A new year starts in winter.

- Spring 1: measured by `update-tech-tree-yearly-picks` (run 20261028-004303-31fa, notes `spring-season.md`) and by older time measurements.
- Winter 0: measured here. In the test scenario `liege-contracts-progress` (run 20261028-032343-3809) the action `set_season("winter")` moved the calendar to winter, the poll read `Season` = 0 (metric `winter_value` 0), and the active contract failed at once (deadline rule).

Config: `liege_contracts.spring_season` = 1 (the value of `tech_tree.spring_season` is used when that key exists) and `liege_contracts.winter_season` = 0.
