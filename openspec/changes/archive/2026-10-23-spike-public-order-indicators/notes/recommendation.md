# Recommendation (spike-public-order-indicators, #422)

## Verdicts

| Route | Verdict | What the player sees |
|---|---|---|
| A: append to `summedPublicOrderFactors` | Partly works | A row with the **native label** of the enum value ("Unburied Bodies -40%"), in "Recent Factors"; with `past = true` the sum shows under "Lingering Memories". The game rebuilds the list each game day, so the mod appends again after each day change. No effect on `publicOrder`. `publicOrderMemory` is not read. |
| B: edit the tooltip widget from Lua | **Works** | A row with the **mod's own text and colour** ("Bandit fear -40%"), a relabelled native row, a changed sum. A pre-hook on `updateContents` with a short delay adds the row each time the tooltip opens. |
| C: pak | Not needed | (A pak cannot add a factor; native enum.) |
| Top bar | Follows the written value | Only while the game runs and the mod writes each tick, for the region under the camera. |

Opening the tooltip needs no widget call and no owner: the harness mouse hover works (`tooltip-open.md`).

## Suggested design for the follow-up change (owner decision)

Use **route B** for the rows. The mod keeps a list of (text, value) for the home region, written by the bandits feature (and later others), and:

1. a pre-hook on `BigTooltip_ApprovalAndPublicOrder_C:updateContents` that, after a short delay, adds one `approvalFactorWidget_C` row for each mod factor and writes the header sum (native sum plus the mod values);
2. keep the `publicOrder` write as it is (the top bar shows it).

Route A can be added at no cost for factors that fit a native label (`unburied`, `homelessness`, `taxation`), but it needs a re-append after each day change and shows the native label, so it is not needed when B is used. Do not use both for the same factor (two rows).

Decide in the design:
- the sum rule: the tooltip header (sum of the rows) and the top bar value are separate numbers today. The mod should make the rows add up to the difference between the native order and the written value, or the player sees "-50%" in the tooltip and "77%" in the bar;
- the texts (English only today; the game has a translation table, the mod strings are plain);
- the hook timing (60 ms delay is a guess) and a fallback when the hook does not fire (then no mod rows, no error);
- the indent and the arrow image of the new row (it has no arrow);
- a test scenario: needs the real mouse (`ctx.hover_with_mouse`), so run it alone (EXCLUSIVE) with a visible window; add a read command that returns the row texts (`recentFactors_VB` children) so the check does not need a picture.

## Not verified

The TAB details view; the tooltip while the game runs with changing factors; two regions; save and load; a controller; the 60 ms delay on a slow frame.

## Safety notes

No save function was called. `allow_eval` was set to true in the settings of the slot copy in use (`slots/2`, reset by each deploy). No game file outside the slot copy was changed. The hold run scenario is scratch and not committed.
