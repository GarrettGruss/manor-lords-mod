## Context

Today `features/tribute/init.lua` pays at each season change: `round(families x 20 x 0.20 x policy x share_factor)` split over fish and timber, plus finite iron (10) and salt (6) by family count. `rules.lua` holds `production`, `amount`, `split`, `season_changed` and `siege_result`. The owner replaced this rule on 2026-11-01.

Engine facts are in the notes of the spikes (not copied here):
- `openspec/changes/archive/2026-11-01-spike-region-rich-resources/notes/region-rich-resources.md`
- `openspec/changes/archive/2026-11-01-spike-rich-food-resources/notes/rich-food-resources.md`
- `openspec/changes/archive/2026-11-01-spike-rich-game-detection/notes/rich-game-detection.md`

## Decisions

1. **Amount.** `round(tribute.base x policy factor x share_factor)` for each of 2 goods. `tribute.base` = 100. The policy factor is read from `config.vassals.policies[policy].tribute` as today (names `light`, `fair`, `heavy` are kept). An unknown policy counts as `fair`, as today.
2. **Period.** One tribute for each game month. The poll, the saved last-period value, the "no payment on the first poll" rule and the forced tick `tribute_tick_now` stay. Only the period source changes (see open question 3).
3. **Detection** is a pure rule in `rules.lua` (fake-game testable) plus a world reader in a new `world.lua`: it lists `ResourceNode` objects, takes the decal or clump data, finds the region with `engine:getRegionByPos(pos, true)`, and returns a list of good ids for each region.
   - Thresholds are in `config.lua`, not in code: `tribute.rich.decal_size = 5000`, `tribute.rich.clump_capacity = { berries = 130, fish = 385, eel = 385, mushrooms = 122 }`, and the goods ids in `tribute.rich.goods` (iron 14, clay 146, salt 145, stone 27, berries 171, mushrooms 279, carp 30, eel 32, flax 11).
   - The removed config keys: `tribute.share`, `tribute.goods`, `tribute.finite_goods`, `tribute.units_per_family`.
4. **Game is never rich.** The spike `spike-rich-game-detection` (#551) found no readable value for the hunting area: deer nodes show the same numbers whether the area is rich or poor. The owner approved the fallback "game never counts" on 2026-11-01. This is final. If a new idea for reading it appears, it is a new change.
5. **Rich soil and the second good.** Rich soil is not detectable. A region with exactly 1 detected rich resource pays flax (good 11) as the second good, as the stand-in for rich soil. If rich soil becomes detectable, it counts and pays flax.
6. **Cache.** The mod reads the rich resources of a region once, at the first tribute tick that needs the region, and keeps them in memory. The cache is not saved with mod state. Reason: the nodes are part of the map and do not change in a session; a re-read after a load costs one node scan, which is cheap, and a saved cache could go stale or wrong after a map change. It also needs no new state version.
7. **Kept as is:** the poll interval, no payment on the first poll after a load, no payment for a vassal with no lord or a rebuilding vassal (a stalled or wiped vassal has no active slot), the refused deposit count `failed_deposits`, the deposit into the first store that takes the full amount, the banner "Tribute has arrived", the named commands `InvasionMod.tribute_state` and `tribute_tick_now`, the `share_factor` of the tech tree, and the whole siege and sack rule.
8. **State of the command.** `tribute_state` history entries drop `families`, `production`, `share` and `finite`; they gain `goods` (list of good id and paid amount) and `rich` (detected goods of the region). `finite_paid` is removed.
9. **Future work (not in this change).** The vassals menu (mockup in `Vassals.dc.html` of the design canvas) can show the rich goods and the monthly amount of each vassal. It needs a read command for the cache; the change that builds the menu adds it.

## Open questions

1. **A region with 0 detected rich resources.** The owner has not ruled. Nothing is decided here. Until the owner rules, the implementation pays nothing for such a region and logs it. Option to suggest: flax x2 (the rich soil stand-in twice).
2. **A region with more than 2 detected rich resources.** The owner has not ruled. Nothing is decided here. Options to suggest: a fixed order of goods (a list in `config.lua`, the first 2 win), or the 2 with the largest value (decal size, or clump capacity over its limit). Until the owner rules, the implementation takes the first 2 in the order of `tribute.rich.goods` and logs the rest.
3. **The month clock.** The spec says "game month". It is not yet known which time value gives a month change (a month field of `TemporalComponent`, or `daysTotal` in steps of one month). A task checks this in the implementation. If it needs a spike, it is a small read-only spike before the implementation.

Resolved (not open any more): game as a rich resource (final: never counts, spike #551).

## Risks

- Reading `ResourceNode` objects must follow the crash list in `DANGEROUS_ACTIONS.md` (no soft object struct reads). The spikes read only decal size and clump capacity; the reader reads only those.
- Region lookup by decal position needs `getRegionByPos`. A node outside every region is ignored.
- Thresholds are measured on one test map. They go in `config.lua` so a playtest can tune them (tuning-only change, no new change folder).
