# Storyboard panels (draft)

Status: draft storyboard images, 2026-10-23. Written by an agent at the user's request. They show composition and content for the Manuscript shots that need new art. They are not final trailer stills: the change `add-invasion-trailer` still needs the owner's style approval (task 2.1) before the full still set.

Shot ids are those of `../slow/05-shot-list.md`; from S06 on they are the same in `../fast/`.

| File | Shot | Shows | Notes for the final still |
| --- | --- | --- | --- |
| `S03.jpg` | S03 | Hands strike a flint; the torch catches; only the flame lights the frame. | Ready as a guide. |
| `S04.jpg` | S04 | The torch falls toward the straw at the foot of the stake; onlookers in the dark. | Ready as a guide. |
| `S06b.jpg` | S06b | A gloved hand holds a letter with the king's seal (single-headed black eagle on gold) over black water. | Ready as a guide. |
| `S10.jpg` | S10 | Anchor 1, wide: the narrator alone at a table in a burned house, eyes down. | The room is lit more brightly than the Ember look; darken it in the grade. |
| `S07.jpg` | S07 | Men and women at a village forge; a gold chalice on red hangs on the wall. | Show one flail head close up; the flails are not clear here. |
| `S08.jpg` | S08 | A captain raises the chalice banner over a ring of war wagons. | The banner must be the tall swallowtail of `banners.png`; here it is small and square. |
| `S17.jpg` | S17 | Anchor 2: the same man, still, his hand on a sheathed sword on the table. | The camera should be closer than S10; here it is the same framing. |
| `S19.jpg` | S19 | Anchor 3, the turn: he stands, the chair knocked back, and grips the sword. | Ready as a guide. |
| `S27.jpg` | S27 | A parchment map: an army with red banners marches on a walled town. | Ready as a guide. |
| `S29.jpg` | S29 | Burning parchment with an empty center for the title. | The title is set later as text. |

Not made: S05a, S05b and S09 (use the public domain Jena Codex pages after a regrade).

The narrator anchors (S10, S17, S19) are storybook panels, not gameplay (owner decision, 2026-10-23). The narrator is an original figure. S10 was made first and is the character and room reference for S17 and S19 (`generate_anchor.sh`).

## How they were made

- Tool: `harness/tools/genimage.py --ref`, model `gemini-3.1-flash-image`. 11 calls: 10 panels, 1 retry of S07 (the first try dressed the peasants in crusader crosses) and 1 retry of S19 (the first try kept him seated).
- Style references, public domain by age: `design/trailer/references/wikipedia/Jan_Hus_at_the_Stake.jpg` and `Hussitenkriege.tif.jpg` (Jena Codex). Check their Wikimedia Commons pages before public use. Banner reference: `openspec/changes/add-invasion-trailer/references/banners.png`.
- Prompts: `generate.sh` and `generate_anchor.sh`, one line per shot, with the shared style text at the top. The script skips a shot whose PNG already exists, so delete the PNG to remake one.
- Full-size PNG originals are in the git-ignored `runs/storyboard/invasion-mod/`. The JPEG copies here are 1280 px wide.
