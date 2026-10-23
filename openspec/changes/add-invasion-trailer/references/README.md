# References

Reference images for the trailer. They define a design; they are not trailer frames.

| File | What it shows | Made with |
| --- | --- | --- |
| `banners.png` | The banner of each side (requirement "Each side is known by its banner"): the Hussite banner, a gold chalice on a red field; the crusader banner, a red cross on white; the king's seal, a single-headed black eagle on gold in red wax. The militia carries the player's heraldry from the game, so it has no panel. | Gemini `gemini-3.1-flash-image` through `harness/tools/genimage.py --ref`, 2026-10-23, second attempt (the first had square banners and a double-headed eagle). |

## `banners.png`

- **Reference image:** `design/trailer/references/wikipedia/Hussitenkriege.tif.jpg`, a page of the Jena Codex (Bohemia, late 15th or early 16th century), public domain by age. Used only for drawing style and palette. SHA-256 `bba8cc4440469791992cf8d5d12504f519401c7d524888b1cf53924dd1af7a71`. Check the file page on Wikimedia Commons before any public use.
- **Design source:** the Jena Codex shows the Hussite banner as a gold chalice on red (owner decision A, 2026-10-23). The single-headed eagle fits Sigismund as King of the Romans; he was crowned emperor only in 1433.
- **Prompt:**

  > A wide reference sheet with three panels side by side, painted like a page of the attached late medieval Bohemian manuscript: hand-drawn black ink outlines, slightly uneven flat mineral colors, worn parchment ground, a thin red ink frame around each panel. No figures, no landscape. Panel 1 (left): a tall, narrow vertical war banner, about three times taller than wide, hanging down from a short wooden crossbar on a long wooden pole, the lower edge cut into a swallowtail. Deep red cloth. In its upper half, one gold chalice: a simple cup on a stem with one round knob and a wide round foot, no gems, no decoration. Panel 2 (middle): the same tall narrow hanging banner shape and pole, white cloth with a plain red cross. Panel 3 (right): a round red wax seal with a single-headed black eagle, wings spread, head turned to one side, on a gold field. Absolutely no text, letters, mottos or labels anywhere. Use the attached image only for drawing style and palette; do not copy any figure from it.
