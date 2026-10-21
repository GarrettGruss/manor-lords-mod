# Design: Update raid clock yearly

## Season roll
- A game year has four seasons. The mod keeps the year number and a flag "raid done this year" in ModState (survives a load).
- At each season change in year 2 or later, if no raid was done this year, the mod rolls once. The chance in percent is `chance_by_season_left` (default: 25, 33, 50, 100 for the first to the fourth season of the year). The fourth season always brings the raid.
- The season change check is like the one in `mod/bandits` (the last season is saved before the roll, so a load does not repeat a roll).
- When the roll succeeds, the raid day is a random day in the season (warning time as before, never longer than the wait).

## Open questions
1. Should the yearly raid replace the subjugation raid timing, or should the subjugation raid be one of the yearly raids (for example every second year)? This design keeps the kind rules and only changes the timing; the owner should confirm.
2. The default chances (25, 33, 50, 100) are a first guess for the owner to tune.
