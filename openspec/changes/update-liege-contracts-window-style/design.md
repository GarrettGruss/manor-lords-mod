## Context

PR #537 already left only the framework Close. This change is visual only. Data, Lua logic and commands do not change.

## Decisions

- The mockup `mockups/liege-contracts-game-style.html` is the visual source. Colours: gold #e8c87a, white text, muted red for a missing amount.
- Text format: goods and rewards in capitals ("Deliver 50 PLANKS", "In storage: x / y", "Reward: +30 CLAY"). Use separate text blocks or rich text so the gold and white parts differ.
- Fulfil is a text block inside the existing button Border. The Border stays transparent. Lua still finds `FulfilButton<r>_<c>` by name.

## Open technical questions (for gate 2, answer in a spike)

1. Which game font can the pak use? Find the serif font asset of the Diplomacy and Help Subjects windows. Check that a pak widget can reference it by path without copying the asset.
2. Which texture or material gives the dark grey panel with rough edges? Find the brush of the Diplomacy panel. Check that a pak widget can reference it.
3. Does the soft centre light need a texture? A flat near-black Border may be enough.
4. Fallback if a font is not usable: the closest engine font (a serif font that ships with UE). Fallback if a texture is not usable: flat colours (dark grey panel, near-black background) with no rough edge.
5. Write the result in `notes/` and name the fallback used in the pull request.

## Risks

- A font or texture path from the game may not load in a mod pak. The fallback keeps the layout and colours.
- Gold and capital text needs rich text or several blocks. Keep the number of widgets small.
