## Context

The menu is a Widget Blueprint cooked in the pak (`make_tech_widget.py`): a canvas with a POOL of `Border` widgets. Lua puts a `WBP_ClickButton` (shared module `HarnessClickHooks`) into each Border, then labels, shows, hides, colors and moves them from the tree data (`features/tech_tree_widget/init.lua`, `lines.lua`). Today the pool has 3 text lines, 2 path buttons, 16 node buttons and 3 law buttons. A click is a hook event that Lua queues and handles on the next scheduler tick. The menu is built on `core/menu.lua`.

The mockup is `mockups/tech-tree-layout.html` (1440x810 board). It is the layout reference only.

## What the mockup needs, and how UMG does it

| Mockup part | UMG / Lua approach | Feasible? |
|---|---|---|
| Header: title, picks counter, close | Two `TextBlock` in the pak canvas; the close button is the existing menu close | Yes |
| Column heads I to IV | 4 `TextBlock` in the pak, text set from config | Yes |
| Column bands | 4 `Border` with a flat brush color | Yes |
| 3 row labels with status lines | 3 `TextBlock` pairs; the path buttons are the 2 existing pool buttons | Yes |
| Node cards (11) | The 16 node Borders. A card is a bigger Border with 3 to 4 text lines (name, status, effects) set by `SetText` | Yes. Needs a bigger Border and text blocks in the pool slot |
| Links between nodes | A thin `Border` (height 4) between two cards; color set by status. A pool of 8 link Borders | Yes, new pool |
| Law name and Enact/Repeal on the card | One extra click button per card (9 laws) | Yes, new pool of 9 law buttons (today 3) |
| Laws strip | 2 places, each a Border with 2 text blocks and a Repeal click button, plus a count text | Yes, new pool |
| Footer message and fixed text | 2 `TextBlock` | Yes |
| Rounded corners, glow, SVG icons | Not in a plain `Border` brush without a texture | Partly. Use flat colors and a colored border; icons are a gap (open question 2) |
| Fonts Cinzel and Alegreya Sans | The game fonts are used | Differs by design |
| Effects of a law on hover | The existing tooltip route (`SetToolTipText` on the Border) | Yes |
| "Next spring +1" and "Reset" | Demo only | Not built |

## Approach (gate 2)

1. Extend `make_tech_widget.py`: new pool sizes (11 node cards of fixed size, 8 link Borders, 9 card law buttons, 2 strip places, text blocks for header, column heads, row labels and footer). Keep the pool limit of 16 nodes. Rebuild `InvasionMod_P.pak`.
2. `lines.lua` gets pure functions (testable in the fake game kit): the picks counter text, the row of a node, the status text, the footer message and the strip places.
3. `init.lua` places every control from the `layout` data (`step_x`, `step_y`) and the row label positions from config. No pixel value is in the requirement; they are in config.
4. The refresh reads the tree state once and updates each control only when its text changes (as `set_line` does today).

## Constraints from DANGEROUS_ACTIONS.md and the engine notes

- Never call `Button.OnClicked:Add` on a Button made at run time (#308). All buttons are the `WBP_ClickButton` of `HarnessClickHooks`, put into the cooked Borders. No new button kind is made at run time.
- When Lua walks the children of the canvas with `GetChildAt`, check each child with `IsValid` before use.
- A UFunction that takes an `FName` is not called on a widget that may lack it. The mod sets text and visibility only (`SetText`, `SetVisibility`, `SetToolTipText`).
- Touch UObjects on the game thread only (the scheduler tick). The key callback only sets a flag.
- The mod never calls a save function. A test scenario that needs a save uses the harness action `save_game` only.
- No Lua raw eval in the test scenarios; they use named commands (`tech_tree_widget_press`, `tech_tree_widget_state`).

## Feasibility concerns

- The pak must be rebuilt, so the work needs the AES key from `modtools/work/aes_key.txt` through the environment, and the pak is committed (check the diff for the key).
- Text length: a card with 3 effect lines at the game font may not fit 260 px. Gate 2 sets the card size in config and checks the picture.
- Icons: the game has no icon for the paths. A flat colored ring with a letter is the fallback.
- The window needs the tree state of change #499 (picks, common techs, common laws). The widget work cannot finish before that state exists.
- The mockup shows the card of the other path at low opacity. Low opacity lowers text contrast. This is intended for a closed card; the status text still names it.

## Not in scope

New rules, textures made with Meshy, the demo buttons of the mockup.
