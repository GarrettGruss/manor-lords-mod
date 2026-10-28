# Gate 2 findings: tech tree window layout

## Build
- The generator `mod/InvasionMod/ue/make_tech_widget.py` makes one canvas of 1152 x 704 (the mockup at 0.8, a little taller for the law row). Pools: 16 node buttons, 16 rings (Border plus letter), 16 card law names, 16 card law buttons, 6 links, 2 path buttons, 2 strip places (Border, name, Repeal button), a close button, and fixed text blocks. 37 click buttons are attached at open; the open command took 0.16 s in the real game (the command log warns above 0.1 s).
- Design said 8 link Borders and 9 card law buttons. The shipped tree needs 6 links (one for each path node that requires another). A law button is indexed by its card (16 in the pool, 11 used), so a button and its card share an index.
- Pak: `uv run python harness/tools/pakmod.py buildmod InvasionMod` (14 files), widget cooked in the shared UE workspace `mlm-ue`. The AES key stayed in the main checkout files.

## Engine facts found
1. The stock source widget (`/MoverExamples/Widgets/ControlsDisplay`) holds the root seed (`StackBox_51`) in a canvas slot with anchors (0, 0.583). The old window only looked "bottom left" because of that. The generator now gives the slot centre anchors and an alignment of 0.5, so the window is centred at its own size. The config no longer has `position`.
2. The base menu (`core/menu.lua`, `let_clicks_reach_the_backdrop`) sets every Border of the new widget to SelfHitTestInvisible right after `on_open`. That undid a Collapsed pool entry of the first refresh (run `20261028-033258-a6da`: all 16 ring Borders read visibility 4, and one unused ring showed as a grey square on the first card). Fix: the first tick after the open forgets the visibility it set and sets it again.
3. A shown pool Border is set to SelfHitTestInvisible and a hidden one to Collapsed, so an empty pool entry takes no clicks. Static colour Borders are HitTestInvisible (set in the generator).
4. `effect_line` crashed (`%+d` with 0.5) on the flag and factor effect kinds of the three common laws (Strip the Dead, Disarm the Peasantry, Curfew), which no window showed before. They now read "Corpse loot at the pit", "Home weapons go to the storehouse" and "Banditry order loss x0.5".
5. A screenshot copies screen pixels. With parallel slots, the UE4SS debug window of another slot lay over the game window in the first pictures. The scenario `widget_layout.py` minimizes debug windows that overlap its game before each picture (no input, no focus). This is local to the scenario; the harness code is not changed.
6. Parallel real-mouse scenarios: `tech-tree-widget` failed twice with `InputError: the game window is not in the foreground` because another slot took the focus. A retry passed.

## Decisions (defaults of the proposal, plus)
- Open question 1 (law effects on the card): the card shows the law name; the effects are in the tooltip and in the strip (default).
- Open question 2 (icons): a letter ring (O, P, C) with a flat colour (default).
- A law of an unlocked tech with no free law place keeps an "Enact" button. A click is refused and the footer says "2 of 2 laws are in force." The delta spec asks for this refusal ("a third enact is refused as a third law"); a hidden button could not be clicked.
- The card text is centred in the click area (the click button label cannot be top aligned from Lua without a risky call). The law name and its button take the bottom 48 pixels of the card.

## Spec changes
- "The tree is drawn from the data": the position is the card origin (config) plus the layout times the step.
- "Labels say what a click does": a law that is closed only by the limit of laws keeps its Enact button.
- "Checked by" lines of all new spec scenarios now name their test (see the delta spec).
