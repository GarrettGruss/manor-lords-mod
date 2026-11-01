## Why

The vassal tribute pays fish and timber by family count, plus finite iron and salt. The owner decided on 2026-11-01 to replace it. A vassal now sends the rich resources of its own region. This makes the region choice matter (pillar 3, scarcity forces expansion: vassals supply what home lacks) and ties the amount to the policy only.

Issue: #552 (`Change: update-vassal-tribute-rich-resources`).

## What changes

- Each game month, each paying vassal sends a fixed base of 100 units of each of the 2 rich resources of its region.
- The vassal policy scales the base: `light` x0.5 (50), `fair` x1 (100), `heavy` x1.5 (150). The policy names and factors are unchanged (`config.vassals.policies`, spec `mod/vassals`).
- Only rich resources count. The mod reads them at run time, because they are random for each game start. There is no table of regions.
- Detection comes from the spikes `spike-region-rich-resources` and `spike-rich-food-resources`: ore, clay, salt and stone by the deposit decal size; berries, fish, eel and mushrooms by the sum of the clump capacity.
- Rich game is NOT detectable (spike `spike-rich-game-detection`, #551). Owner decision: game never counts as a rich resource.
- Rich soil is not detectable. A region with only 1 detected rich resource takes rich soil (flax) as the second.
- The old rule is removed: share of a family production, fish and timber, and the finite goods iron and salt.
- Kept: the poll, no payment on the first poll after a load, the refused deposit count, the named commands, no payment for a vassal that is rebuilding or lost, the siege rule.

## Non-goals

- The vassals menu (mockup in the design canvas `Vassals.dc.html`). Showing the rich resources and the monthly amount there is future work.
- Moving goods between regions (decision 21 stays: the mod adds goods to a home store).
- New game design. The open questions in `design.md` stay with the owner.

## Design link

Serves `design/mod/invasion-mod.md`, section Vassals, and pillar 3 (scarcity forces expansion). It keeps pillar 2: vassals are ruled only by policies. Decision 21 says "at each season tick"; the owner changed the period to a month on 2026-11-01. The owner owns `decisions.md` and may update decision 21.

Continues the legacy work of M08 (tribute), now in the living spec `mod/tribute`.
