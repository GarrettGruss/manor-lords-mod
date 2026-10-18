# Design: composite building gaps

## Open questions

| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 1 | Is a build menu card for a new building id wanted? The Invasion Mod design uses no new building yet. | Project owner | Owner reply on the issue |
| 2 | Is the Siege Camp (row 483) wanted? Leads: `setPlacedBuilding`, `finishSpawningSoloBuildingAsync`, `setupBuildings` (legacy `siege-camp-build.md`). | Project owner | Owner reply; then task 3.1 |
| 3 | Does the build menu filter on `bVisibleInUi` only, or also on category tab, tier or perks? | Spike | Task 2.1 |
| 4 | Why does `order_oxen` add only one ox? | Spike | Task 4.1 |
| 5 | Where do idle oxen stand? | Spike | Task 4.2 (run unpaused at night) |

## Decisions already made (not open)

- Capacity 4 (`stableSpace`) stays. Hitch spots are native. No further hitch tests unless a way to create a hitching post is found (owner, 2026-10-15).
