## Why

The vassal tribute pays fish and timber by family count, plus finite iron and salt. The owner decided on 2026-11-01 to replace it. A vassal now sends the rich resources of its own region. This makes the region choice matter (pillar 3, scarcity forces expansion: vassals supply what home lacks) and ties the amount to the policy only.

Issue: #552 (`Change: update-vassal-tribute-rich-resources`).

## What changes

- Each game month (owner decision 2026-11-01: month, not season), each paying vassal sends a fixed base of 100 units of each of 2 goods of its region.
- The vassal policy scales the base: `light` x0.5 (50), `fair` x1 (100), `heavy` x1.5 (150). The policy names and factors are unchanged (`config.vassals.policies`, spec `mod/vassals`).
- Only rich resources count. The mod reads them at run time, because they are random for each game start. There is no table of regions.
- Detection comes from the spikes `spike-region-rich-resources` and `spike-rich-food-resources`: ore, clay, salt and stone by the deposit decal size; berries, fish, eel and mushrooms by the sum of the clump capacity.
- Rich game is NOT detectable (spike `spike-rich-game-detection`, #551). Owner decision: game never counts as a rich resource.
- Rich soil is not detectable. Flax stands in for it. Every region pays 2 goods: 1 detected pays that good and flax, 0 detected pays flax twice (owner decision 2026-11-01). More than 2 detected keep 2 by priority: tier 1 iron, stone, salt; tier 2 clay and fish/eel; tier 3 berries and mushrooms; list order inside a tier (owner decision 2026-11-01; the ore tier reading is the lead's).
- The old rule is removed: share of a family production, fish and timber, and the finite goods iron and salt.
- Kept: the poll, no payment on the first poll after a load, the refused deposit count, the named commands, no payment for a vassal that is rebuilding or lost, the siege rule.

## Non-goals

- The vassals menu (mockup in the design canvas `Vassals.dc.html`). Showing the rich resources and the monthly amount there is future work.
- Moving goods between regions (decision 21 stays: the mod adds goods to a home store).
- New game design. The open questions in `design.md` stay with the owner.

## Design link

Serves `design/mod/invasion-mod.md`, section Vassals, and pillar 3 (scarcity forces expansion). It keeps pillar 2: vassals are ruled only by policies. Decision 21 said "at each season tick". The owner changed the period to a month on 2026-11-01 and approved the one-word change of decision 21 in `design/mod/decisions.md` (season to month).

Continues the legacy work of M08 (tribute), now in the living spec `mod/tribute`.

## Spec changes (owner decisions of 2026-11-01, folded in at gate 2)

- A region with 0 detected rich resources pays flax twice. Every region pays 2 goods. More than 2 detected are cut by priority (new requirements "A region always pays two goods" and "More than two rich resources are cut by priority").
- The period is a month (`TemporalComponent.month`). Two requirements are renamed from "season" to "month" (RENAMED). The scenario names keep the word "season" because the validator needs them to match the living spec.
- The requirement "Vassals pay iron and salt as the permanent supply" of `mod/finite_resources` is removed (its goods are now paid only when rich).
