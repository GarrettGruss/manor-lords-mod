# Storyboard (task 1.3)

Status: approved by the owner (2026-10-23, gate 2 of `sn-motion-html`). Slow cut. The table is generated from `docs/chapters.py`; edit the chapter list there and run `uv run python docs/chapters.py` from the project root.

Sources: the story is `design/mod/trailer.md` (owner). The shot plan is `design/trailer/invasion-mod/slow/` (05-shot-list.md for shot ids, 04-script.md for sound). Draft panels for the stills are in `design/trailer/invasion-mod/storyboard/`.

"Video s" is the chapter's time in the 60 s export, connector included. A connector takes its 0.5 s from the end of the chapter before it, so every cut stays on the shot-list time.

<!-- chapters:begin -->
| # | Chapter | Shots | Start | Video s | Look | Focal subject | Camera | Copy position | Display copy | Connector to the next chapter |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `00-darkness` Darkness | S01-S02 | 0:00.0 | 5.0 | Black | Nothing: full black | None | center | Christe, fili Dei vivi, miserere mei. | Hard cut |
| 1 | `01-flint` Flint | S03 | 0:05.0 | 1.5 | Manuscript | Hands strike a flint; the torch catches | Locked | bottom | — | The torch flame swings down and the camera follows it |
| 2 | `02-torch` The torch falls | S04 | 0:06.5 | 1.5 | Manuscript | The torch falls into the straw at the stake | Follow the torch down | bottom | — | Flames erupt from the straw and fill the frame, then thin to show the stake |
| 3 | `03-stake` Constance | S05a-S05b | 0:08.0 | 4.0 | Manuscript | Jan Hus at the stake, flames rising (Jena Codex page, regraded) | Static, then tilt up | right | — | The flames darken to smoke and the smoke becomes black water |
| 4 | `04-given-word` The given word | S06-S06b | 0:12.0 | 5.0 | Black, then Manuscript | Black; then the king's sealed letter over dark water | Static | left | Constance, in the year of our Lord fourteen fifteen. / They gave him their word. Then they burned him. | Sparks rise from the water and become sparks from a forge |
| 5 | `05-answer` Bohemia answered | S07 | 0:17.0 | 2.0 | Manuscript | Men and women beat flails into weapons at a forge | Parallax | left | Bohemia answered. | The camera rises past the forge roof to a hill with a ring of wagons |
| 6 | `06-banner` Four crusades | S08 | 0:19.0 | 2.5 | Manuscript | A captain raises the chalice banner over a ring of war wagons | Slow push-in | right | Four crusades marched against them. | The red sky behind the banner widens into the battle page |
| 7 | `07-red-sky` Four crusades broke | S09 | 0:21.5 | 2.5 | Manuscript | The Hussite army under a red sky (Jena Codex page, regraded) | Parallax; the page edge burns | left | Four crusades broke. | The page burns away and shows a dark room behind it |
| 8 | `08-burned-house` Franconia, 1429 | S10 | 0:24.0 | 3.0 | Ember | The narrator alone at a table in a burned house | Static after the page burn | right | Franconia, 1429. | The camera moves through the broken wall into grey daylight and smoke |
| 9 | `09-raids` The war comes | S11-S16c | 0:27.0 | 12.0 | Ash (gameplay) | Gameplay montage: raiders on the road, ransom and fire, looting, refugees and bandits, a barn burning | Gameplay cuts inside the stage | bottom | I did not choose this war. / Then they rode west, into Franconia. Towns that paid were spared. Towns that would not, burned. / And the hungry want bread. We marched on Bohemia. Now Bohemia marches on us. | Smoke fills the frame and clears to the hearth in the burned house |
| 10 | `10-still` He sits still | S17 | 0:39.0 | 2.5 | Ember | The narrator, still, his hand on the sword | Very slow push-in | right | — | The camera turns from the hearth to the doorway and the village beyond |
| 11 | `11-choice` Fear or faith | S18 | 0:41.5 | 3.0 | Ash and Day (gameplay) | Split frame: a gallows and a full market in the same village | Static split frame | center | Rule by fear, or by faith. | The split closes into the dark house again |
| 12 | `12-turn` He stands | S19 | 0:44.5 | 1.0 | Ember | The narrator stands and takes the sword | Static | left | — | He walks out of the house into daylight at the palisade gate |
| 13 | `13-battle` The line holds | S20-S26 | 0:45.5 | 7.5 | Day (gameplay) | The lord at the gate; the militia forms up; the lines meet; the raiders break and flee past their captain | Gameplay cuts inside the stage | bottom | — | The camera rises from the field into cloud, and the cloud becomes parchment |
| 14 | `14-map` The great raid | S27 | 0:53.0 | 2.5 | Manuscript | The region map: a larger army marches on the town | Slow crane down onto the map | right | — | Hard cut |
| 15 | `15-whisper` Black | S28 | 0:55.5 | 1.5 | Black | Nothing: full black | None | center | Restore order. Or burn with it. | Hard cut |
| 16 | `16-title` Title | S29 | 0:57.0 | 3.0 | Manuscript | Burning parchment; the title is set as text | Static; embers drift | center | The Hussites Are Coming | Hard cut |
<!-- chapters:end -->

## Stills per chapter

| Chapter | Still source |
| --- | --- |
| `00-darkness`, `15-whisper` | A plain black frame, made locally (no AI call). |
| `01-flint`, `02-torch`, `04-given-word`, `05-answer`, `06-banner`, `08-burned-house`, `10-still`, `12-turn`, `14-map`, `16-title` | The draft panels S03, S04, S06b, S07, S08, S10, S17, S19, S27, S29, remade as final stills after the style approval. |
| `03-stake`, `07-red-sky` | The public domain Jena Codex pages (Hus at the stake; the battle page), regraded to the palette. |
| `09-raids`, `11-choice`, `13-battle` | Gameplay captures (tasks 4.1 and 4.2). The chapter still is the first frame of the capture. |

## Open points for the owner

1. **Copy in the video export (decided).** The export hides the copy, except "Franconia, 1429." and the title (owner, 2026-10-23). The scroll page shows all copy.
2. **Hard cuts.** Four cuts are on purpose: black to the first light (00→01), the map to black (14→15), black to the title (15→16), and none in the middle of a gameplay montage. Every other chapter change is a connector.
3. **Gameplay chapters.** `09-raids` and `13-battle` hold several game shots each. Inside a chapter they are hard cuts in the capture itself, not Seedance connectors.
