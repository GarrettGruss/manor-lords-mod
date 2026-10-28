## Why

Issue: #502. Owner decision 2026-10-27. The tech menu (F9) is a plain list of buttons: three text lines and a grid of colored buttons (picture: `openspec/changes/archive/2026-10-23-update-single-mod-pak/evidence/tech-tree-widget.jpg`). The change `update-tech-tree-yearly-picks` (#499) gives the tree yearly picks, three common techs and three common laws. The menu must show them. The owner chose a "Civilization" style layout (option A), drawn as an HTML mockup.

## What Changes

- The tech tree window gets a new layout, defined by the mockup `mockups/tech-tree-layout.html` (gate 2 copies it to `openspec/specs/mod/tech_tree_widget/mockups/tech-tree-layout.html`):
  - header with the title, the tech picks counter (free picks) and the close button;
  - column heads I to IV by order (not by settlement level);
  - rows Oppression, Prosperity and Common (3 common techs), node cards with links;
  - each card shows effects and its law with Enact or Repeal;
  - a laws strip with "N of 2 max" and Repeal buttons;
  - a footer with the last result and "One tech pick each spring. The path you swear to is final."
- The three text header lines are replaced by the header counter and the row labels.
- The law buttons move into the cards and the strip (today up to 3 buttons for the chosen path).
- Common techs can be clicked before a path is chosen. Path nodes cannot.
- Out of scope: new game rules (all rules are in `update-tech-tree-yearly-picks`); game textures and icons; the mockup demo buttons ("Next spring +1", "Reset") are not part of the window.

## Decisions (owner, 2026-10-27)

- Layout option A in the "Civilization layout" style.
- The mockup is the layout reference. Fonts and textures of the game may differ.
- The requirement says "follows the layout of the mockup" and names the parts, not pixels.

## Open questions (with defaults)

1. Law effects on the card. Default: the card shows the law name, and the effects show in the tooltip and in the laws strip. A card has no room for the law effects as text.
2. Icons in the node rings. Default: the game has no icon for a path. Gate 2 uses a letter or a color ring if an icon texture is not available (see `design.md`).

## Impact

- Specs: `mod/tech_tree_widget` (RENAMED and MODIFIED: header, tree drawing, path buttons, laws; ADDED: layout, footer). Gate 2 also adds the mockup file to `openspec/specs/mod/tech_tree_widget/mockups/`.
- Code (gate 2): `mod/InvasionMod/Scripts/features/tech_tree_widget/` (init, lines), the pak widget generator `mod/InvasionMod/ue/make_tech_widget.py` and the pak, `config.lua` (`tech_tree_widget`), tests, test scenarios, wiki, CHANGELOG.
- Depends on `update-tech-tree-yearly-picks` (#499): merge it first, or rebase on it. The tree state must give the picks and the common techs.
- Risk: the widget is a pool of Borders cooked into the pak, so the layout needs a new pak with larger pools (see `design.md`).
