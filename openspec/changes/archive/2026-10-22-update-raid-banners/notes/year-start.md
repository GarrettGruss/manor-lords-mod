# Game year and the great raid start (task 1.1)

- The year is not read from the game. The yearly rule of `update-raid-clock-yearly` counts season changes in ModState (`yearly_season_no`; `plan.season_year`: 4 changes make 1 year, year 1 is the first year the mod saw).
- The great raid uses the same count: year 10 starts at season change 36.
- A real game year has about 91 days a season. The clock keeps `great_raid_day` as an estimate (`season_estimate_days` 92, so the estimate is never early). When year `start_year` begins, the mod sets `great_raid_day` to that day and the waves start.
- Difference from the delta spec text "The end day SHALL be kept in ModState and does not change": the end day moves once, at the start of year 10, from the estimate to the real day. The spec text should say so at archive.
- "A missed warning after a load is skipped": the clock banner shows only when the year changed since the last daily step in this Lua session (`last_seen_year`), so the first step after a load shows none. `last_clock_banner_year` (ModState) stops a repeat in the same year.
- The raid menu list (type, target, size, days left) was an owner decision after the proposal. It is added as a delta spec `specs/mod/raid_widget/spec.md`. The widget pak has 5 text lines, so the old "Size estimate" line became the subjugation raid line.
- Open: the target text of the menu and banner uses `vassal_provider()` each refresh while the menu is open. Check in the real game that the menu does not crash or lag.
