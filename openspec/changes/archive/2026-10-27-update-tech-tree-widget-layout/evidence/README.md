# Evidence: tech tree window layout

The owner compares these pictures with the mockup `openspec/specs/mod/tech_tree_widget/mockups/tech-tree-layout.html`.
All pictures: test scenario `tech-tree-widget-layout` (`--pak InvasionMod --slot 2`), run id `20261028-040825-49af` (verdict pass, 39 checks).
The game window was 1302 x 776; the pictures are scaled to 1208 x 720 (JPEG).

| File | State | What to compare with the mockup |
|---|---|---|
| `layout-1-no-path.jpg` | A new game: one free pick, no path chosen | Header with the counter "1 free (0 of 1 used)", column heads I to IV, the three rows, "Swear to this path" in the Oppression and Prosperity rows, "Choose a path" on the path cards, common techs "Available", empty laws strip, footer start message |
| `layout-2-path-two-techs.jpg` | Prosperity sworn, Fair Courts and Amnesty unlocked | The Prosperity row says "Sworn path", the Oppression row "Closed" and its cards dim, lit links after the unlocked techs, "Enact" under the laws of the two unlocked techs, footer "You swore to Prosperity. This is final." |
| `layout-3-two-laws.jpg` | Militia Charter and Trade Pacts enacted | "Repeal" on both cards, two filled places in the laws strip with the effects, "2 of 2 max", footer "Trade Pacts enacted." |

Known differences from the mockup (design.md): flat colours instead of rounded corners and glow; a letter ring (O, P, C) instead of an icon; the game font instead of Cinzel and Alegreya Sans; the card text is centred; the bottom button "Close" in the middle of the screen is the base menu close button, not part of the window.
