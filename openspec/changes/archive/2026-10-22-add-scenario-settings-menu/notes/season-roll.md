# 1.2 The yearly season roll (change `update-raid-clock-yearly`, #339)

Checked on the branch (merged with `feat/update-raid-clock-yearly`):

- ModState keys of the invasion feature: `yearly_season_no` (-1: no season seen), `yearly_last_season`, `yearly_done_year`. The year is `floor(season_no / 4) + 1`,
  the position is `season_no % 4 + 1` (`plan.season_year`). The year counts season changes since the mod started, not the calendar year.
- `plan.should_raid(year, position, done_year, chances, roll)` returned false for `year < 2`. It has a new optional argument `first_year` (default 2, so older callers are the same).
  `roll_season` passes `first_raid_years + 1`.
- Chances per season: 25, 33, 50, 100 percent (`invasion.yearly.chance_by_season`); the raid comes 1 to 90 days after the roll (`yearly.season_days`).
- Length of a game year: the roll counts seasons, not days; a calendar year is 4 seasons. A real calendar year takes about 1800 wall seconds at speed 3 (test scenario
  `invasion-yearly-raid` therefore counts season changes with `invasion_yearly_advance_season`).
- State keys added by this change: `first_raid_years` (registered default 1, which is the old "year 2"), `size_class_fixed` (0), `great_raids` (1), `settings_applied` (0).
  The registered defaults keep the old behaviour. The config defaults (2, 2, 1 and difficulty 2) are written by the menu, by `scenario_settings_skip` and for an old save.
- Run `20261022-045326-ff47` (`scenario-settings-first-raid-delay`): after 2 years no raid in years 1 and 2, the roll of year 3 plans one 1 to 90 days ahead.
