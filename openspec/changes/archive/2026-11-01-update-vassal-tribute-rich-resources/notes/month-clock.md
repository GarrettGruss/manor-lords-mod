# Month clock (task 1.1)

Question: which game value gives a month change?

## Answer

`TemporalComponent.month` (an `IntProperty` of the calendar object of `RTSMultiEngineCPP`, next to `day`, `dayOfTheMonth`, `Year`, `Season`, `daysTotal`). It is 1 based (January is 1). The tribute feature polls it and pays when it differs from the saved value `tribute_last_month`.

## Evidence

- Earlier note `2026-10-30-update-liege-contracts-tiers/notes/season-days.md`: `TemporalComponent.day` is the day of a 365-day year and the new game fixture starts on day 61 (Mar 2); `month` and `dayOfTheMonth` exist.
- The harness action `set_day` writes the day and the month follows (action docstring).
- Real game run `tr-rich-1` (test scenario `tribute-rich`, read of `tribute_state.month`): the fixture started in month 9 (day 209). `set_day` 15, 46 and 74 gave months 1, 2 and 3. Each jump made exactly one tribute tick (`TRIBUTE month change 9 to 1`, `1 to 2`, `2 to 3` in `mod.log`). The first poll after the load paid nothing (`ticks` 0).
- No spike was needed. The read is cheap and safe (an integer property of the calendar object, no crash-list item).

## Consequences

- A jump of the season or the day that changes the month also pays once. A season change inside one month pays nothing (fake-game test).
- The December to January wrap (12 to 1) is a change, because the rule compares with `~=`.
- The saved key is `tribute_last_month`. The old key `tribute_last_season` stays in the pawn tags as an unknown ModState entry and is ignored.
- Real month length follows the game calendar (28 to 31 days), not a fixed 30 days.
