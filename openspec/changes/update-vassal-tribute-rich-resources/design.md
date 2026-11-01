## Context

Today `features/tribute/init.lua` pays at each season change: `round(families x 20 x 0.20 x policy x share_factor)` split over fish and timber, plus finite iron (10) and salt (6) by family count. `rules.lua` holds `production`, `amount`, `split`, `season_changed` and `siege_result`. The owner replaced this rule on 2026-11-01.

Engine facts are in the notes of the spikes (not copied here):
- `openspec/changes/archive/2026-11-01-spike-region-rich-resources/notes/region-rich-resources.md`
- `openspec/changes/archive/2026-11-01-spike-rich-food-resources/notes/rich-food-resources.md`
- `openspec/changes/archive/2026-11-01-spike-rich-game-detection/notes/rich-game-detection.md`

## Decisions

1. **Amount.** `round(tribute.base x policy factor x share_factor)` for each of 2 goods. `tribute.base` = 100. The policy factor is read from `config.vassals.policies[policy].tribute` as today (names `light`, `fair`, `heavy` are kept). An unknown policy counts as `fair`, as today.
2. **Period.** One tribute for each game month (owner decision 2026-11-01; the owner changed decision 21 in `design/mod/decisions.md` from "season" to "month"). The poll, the saved last-period value, the "no payment on the first poll" rule and the forced tick `tribute_tick_now` stay. The period source is `TemporalComponent.month` (`notes/month-clock.md`). The saved key is now `tribute_last_month` (the old `tribute_last_season` stays in the pawn tags as an unknown key and is ignored). The tick fires when the month differs from the saved one, so a jump of the season or the day also pays once.
3. **Detection** is a pure rule in `rules.lua` (fake-game testable) plus a world reader in a new `world.lua`: it lists `ResourceNode` objects, takes the decal or clump data, finds the region with `engine:getRegionByPos(pos, true)`, and returns a list of good ids for each region.
   - Thresholds are in `config.lua`, not in code: `tribute.rich.decal_size = 5000`, `tribute.rich.clump_capacity = { berries = 130, carp = 385, eel = 385, mushrooms = 122 }`, the goods ids in `tribute.rich.goods` (iron 14, clay 146, salt 145, stone 27, berries 171, mushrooms 279, carp 30, eel 32, flax 11), the node class and decal material names (`clump_goods`, `deposit_goods`) and `priority`. Clump kinds add up for one node (several `Resource_Fish_C` clumps), then the sum is compared.
   - The world reader reads only the decal material name, the decal size X and position, and the class and `capacity` of the clumps. It never reads a struct with soft object fields.
   - The removed config keys: `tribute.share`, `tribute.goods`, `tribute.finite_goods`, `tribute.units_per_family`.
4. **Game is never rich.** The spike `spike-rich-game-detection` (#551) found no readable value for the hunting area: deer nodes show the same numbers whether the area is rich or poor. The owner approved the fallback "game never counts" on 2026-11-01. This is final. If a new idea for reading it appears, it is a new change.
5. **Rich soil, the fill good and the number of goods (owner decisions 2026-11-01).** Rich soil is not detectable. Flax (good 11) stands in for rich soil. Every region has 2 rich resources, so a vassal always pays 2 goods (`tribute.rich.per_region`). Flax is added only when fewer than 2 are detected: 1 detected pays that good and flax, 0 detected pays flax twice (2 x base x policy factor of flax). If rich soil becomes detectable, it counts and pays flax.
5a. **More than 2 detected: priority (owner decision 2026-11-01).** The mod keeps 2 and drops the rest. Tier 1 ores, tier 2 clay and fish/eel, tier 3 the others (berries, mushrooms). Inside a tier the order of the list in `config.lua` decides. The ore tier is written as iron, stone, salt. This reading of "ores" is the lead's; the owner may correct it. The priority list is `tribute.rich.priority`. The dropped goods are logged and shown in `tribute_state` (`dropped`). With the test map data no region has more than 2, so the cut is only tested in the fake game.
6. **Cache.** The mod reads the rich resources of all regions once, at the first tribute tick (one scan of the `ResourceNode` objects), and keeps them in memory. The cache is not saved with mod state. Reason: the nodes are part of the map and do not change in a session; a re-read after a load costs one node scan, which is cheap, and a saved cache could go stale or wrong after a map change. It also needs no new state version. The cache belongs to one engine object (`RTSMultiEngineCPP`): a load makes a new engine object, so the next tick scans again. A scan that finds no node at all is not cached (the nodes may not be loaded yet); that tick pays the fill goods.
7. **Kept as is:** the poll interval, no payment on the first poll after a load, no payment for a vassal with no lord or a rebuilding vassal (a stalled or wiped vassal has no active slot), the refused deposit count `failed_deposits`, the deposit into the first store that takes the full amount, the banner "Tribute has arrived", the named commands `InvasionMod.tribute_state` and `tribute_tick_now`, the `share_factor` of the tech tree, and the whole siege and sack rule.
8. **State of the command.** `tribute_state` history entries drop `families`, `production`, `share` and `finite`; they gain `goods` (list of `name`, `id` and `paid` amount), `rich` (detected goods of the region) and `dropped` (detected goods cut by the priority). `finite_paid` is removed. The command state also gains `month` and `last_month` (`last_season` is removed; `season` stays).
9. **Future work (not in this change).** The vassals menu (mockup in `Vassals.dc.html` of the design canvas) can show the rich goods and the monthly amount of each vassal. It needs a read command for the cache; the change that builds the menu adds it.

## Open questions

None. Resolved by the owner on 2026-11-01:

1. A region with 0 detected rich resources pays flax twice (decision 5).
2. A region with more than 2 detected rich resources keeps 2 by priority (decision 5a). Open for correction only: the ore tier reading (iron, stone, salt).
3. The period is a month, read from `TemporalComponent.month` (decision 2, `notes/month-clock.md`).
4. Game as a rich resource: final, never counts (spike #551).

The data setting `tribute.rich.per_region` (2) is the owner rule "every region has 2 rich resources".

## Risks

- Reading `ResourceNode` objects must follow the crash list in `DANGEROUS_ACTIONS.md` (no soft object struct reads). The spikes read only decal size and clump capacity; the reader reads only those.
- Region lookup by decal position needs `getRegionByPos`. A node outside every region is ignored.
- Thresholds are measured on one test map. They go in `config.lua` so a playtest can tune them (tuning-only change, no new change folder).
