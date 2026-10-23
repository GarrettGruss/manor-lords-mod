## Why

The tech tree menu shows only the name of a node or a law. The player cannot see what it does before a click, and a node choice or a path choice is final. The owner asked (2026-10-23) for a tooltip on mouse over. It lists all effects of the tech (the owner calls a tech a "law"). A statistical change shows as a percentage.

Issue: #428.

## What changes

- Mouse over a node button or a law button of the tech tree menu shows a tooltip.
- The tooltip lists the numerical effects of the node or law, each with its value. The design builds the text from the effect data in `data/tech_tree/tree.json`, so there is no hand-written duplicate text (a design choice, not a requirement).
- A percent effect (factor) shows as a signed percentage: factor 0.10 shows "+10%", factor -0.25 shows "-25%".
- A flat effect (public order, approval, retinue capacity, manor storage) shows as a signed number, with its name.
- An effect with a condition (`min_garrison_squads`) shows the condition on the same line.
- The tooltip MAY show other information, for example a condition or an opened vassal policy.
- A pure text builder in `tech_tree_widget/lines.lua` makes the text. It is tested in the fake game.

## Non-goals

- No change to the effects, the values or the tree data.
- No new effect kinds, and no change to the header line "Effects: ...".
- No tooltip on path buttons (a path has no effect data).
- No new model, texture or animation.
- No rule that every effect kind needs a text, and no rule that every value is a percentage.

## Design pillars

Source: `design/mod/invasion-mod.md`, pillar 6 (one path of rule, exclusive) and pillar 4 (dread from knowing). The choice of a path and of nodes is final, so the player must know the cost and the gain before the click. The tooltip adds information only. It changes no rule, so it does not contradict a pillar.

## Legacy

This change continues the tech tree menu (`mod/tech_tree_widget`, M12 iteration 02). It does not continue a legacy doc folder directly.

## Impact

- Spec: delta for `mod/tech_tree_widget` (ADDED requirement).
- Code: `mod/InvasionMod/Scripts/features/tech_tree_widget/lines.lua` and `init.lua`. Possibly `mod/InvasionMod/ue/make_tech_widget.py` and the pak `techmenu_P.pak` (decided by the spike, see `design.md`).
- `CHANGELOG.md` and the wiki page of the tech tree menu.
