# Proposal: Spike public order indicators

Issue: #422. Related: #403 (spike-public-order-factor).

## Why
Owner request (chat, 2026-10-23): the game shows a Public Order tooltip when the player hovers the scale icon in the top bar. The picture is in `reference/order-tooltip.png`. It shows:
- a header "Public Order";
- a section "Recent Factors -10%" with a row "Unemployment -10%";
- a section "Lingering Memories +0%" with "None".

Question: can the mod add its own rows, for example "Bandit fear -40%" or "Raid -20%", so the player sees why order changed?

Context:
- The mod writes `Region.publicOrder` on each tick (owner decision in #403). The top bar order value follows that value, but the tooltip shows only native factors. The player sees a low order and no reason.
- Known from #403 (`openspec/changes/archive/2026-10-23-spike-public-order-factor/notes/`, `docs/wiki/concepts/engine-limits.md`, "Public order factors"):
  - factors are the native enum `EApprovalFactorType` (34 values) with weights from config;
  - `summedPublicOrderFactors` entries are plain structs;
  - `publicOrderMemory` entries can be appended safely, but the game rewrote `effectByPopulation`.
- The bandits feature (`mod/InvasionMod/Scripts/features/bandits/`) writes an order debuff. In a playtest the owner saw order held at 0 and 6 unexplained deaths. This is context only. This spike does not fix it.

## What Changes
Test three routes in this order. Stop at the first route that gives a readable custom row.
- **Route A:** append or edit entries in the region's summed factor list and in `publicOrderMemory`. Find out if the tooltip reads them, if the game clears them, and which enum value and label show.
- **Route B:** edit the tooltip widget at run time from Lua. Find the widget class when the tooltip opens. Try to add a text row, and to change a label or a value.
- **Route C:** a pak that adds a label or factor row. Only if A and B fail. Likely impossible, because factors are a native enum.

Also record: the order percentage in the top bar follows the value the mod writes.

Write each result to `notes/<topic>.md`, with pictures in `evidence/`. End with a recommendation and the owner decision.

## Non-goals
- The final indicator design (names, values, layout, which events show). That is a later change, after the owner decision.
- Changing `mod/bandits` or other features.
- Fixing the order held at 0 or the unexplained deaths.
- Any save call. Never call a save function (CLAUDE.md, Safety).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None. A spike records findings only (`skip_specs: true`).

## Impact
- Real game runs, one at a time, single-player. Each run id goes into the notes.
- Pictures go in `evidence/`, each listed in `evidence/README.md` with its test scenario and run id.
- Lasting engine facts go to `docs/wiki/concepts/engine-limits.md` before the archive.
