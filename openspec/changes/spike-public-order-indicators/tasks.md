## 1. Preparation
- [x] 1.1 Read the #403 notes and `DANGEROUS_ACTIONS.md`. Written to `notes/prior-facts.md`.
- [x] 1.2 Find a way to open the tooltip without a mouse (widget function or hook). Written to `notes/tooltip-open.md`. If none works, mark task 5.1 as needing the owner.

## 2. Route A: factor list and memory
- [x] 2.1 Read the list structs and the tooltip data source. Written to `notes/route-a.md`.
- [x] 2.2 Append or edit an entry in `summedPublicOrderFactors`. Record whether the tooltip shows it, which enum value and label show, and whether the game clears it.
- [x] 2.3 Do the same for `publicOrderMemory` (Lingering Memories).
- [x] 2.4 Verdict for route A (works, partly, fails).

## 3. Route B: widget edit
- [x] 3.1 Find the tooltip widget class and its row widgets. Written to `notes/route-b.md`.
- [x] 3.2 Add a text row, change a label, change a value. Check it survives a refresh.
- [x] 3.3 Verdict for route B.

## 4. Route C and top bar
- [x] 4.1 Route C only if A and B fail. Written to `notes/route-c.md`.
- [x] 4.2 Record that the top bar percentage follows the value the mod writes. Written to `notes/top-bar.md`.

## 5. Evidence and close
- [x] 5.1 Pictures of the tooltip (before, and with each working route), in `evidence/` with `evidence/README.md` (test scenario, run id). Needs the owner if the mouse is the only way to open the tooltip.
- [x] 5.2 Move lasting engine facts to `docs/wiki/concepts/engine-limits.md`. Add a `CHANGELOG.md` line.
- [x] 5.3 Write the recommendation (`notes/recommendation.md`). Owner decision still open: route B is suggested.
