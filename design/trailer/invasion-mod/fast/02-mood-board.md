# 02 Mood board (fast version)

Palette from `trailer.md`: black, bone white, ember orange, dried-blood red. Every look uses only these, plus the natural greens and browns of gameplay, graded down.

## Four looks

| Look | Used for | Light and color | Alfred counterpart |
| --- | --- | --- | --- |
| **Manuscript** | History: Constance, Bohemia, the crusades | Parchment, ink lines, bone white and black. Ember orange only for fire. Red only for the chalice banner and the sky. | None (new). |
| **Ember** | The narrator alone in the burned house (the anchor) | Near-black room. One warm light from a hearth or candle. Charred beams and a broken wall behind him. His face half in shadow. | Firelight: the king in the sacked house. |
| **Ash** | Raids, refugees, bandits | Gameplay, desaturated almost to grey. Smoke, overcast sky, winter or late autumn. Fire is the only saturated color. | Ash: ruined villages and the raid. |
| **Day** | The muster, the battle, the rout | Gameplay, natural overcast light, a little warmer than Ash. The militia's colors are visible. | Daylight: the muster and the battle. |

Rule: the narrator gets clean light once, when he stands up to lead (S20). Before that he is only seen in Ember.

## Camera language

- Manuscript: slow parallax between ink layers; embers drift across; transitions are page edges that burn.
- Ember: locked camera or a very slow push-in. Shallow depth of field. He does not look at the camera.
- Ash: slow tracking shots at village height; smoke on the horizon from a distance; people seen from behind.
- Raid: low and close, short cuts (about 1 s), the camera moves with the raiders.
- Battle: low, inside the militia line; one high top-down shot for scale.
- Map: the parchment map from the Manuscript look comes back at the end, so the trailer closes the way it opened.

## Motifs

- **Fire:** the flint and torch at Constance, the burning village, the ember light of the anchor, the burned edges of pages and of the title. The same fire runs from 1415 to 1429.
- **The burned house:** the narrator's anchor. The liege gave him a burned village; he lives in what the raid left.
- **The given word:** Hus was given a safe-conduct and burned. Then the king promised to drown every Hussite (S06b). Promises from above, kept only as threats.
- **Singing:** one man sings at the stake (Hus); at the very end, over the title, a whole army sings his cause (the hymn, S29). The trailer opens with the song of one and closes with the song of many.
- **The wagon fort:** the Hussite trademark, shown once in a panel (S08), never in gameplay.
- **Flails into weapons:** the peasants' farm flails (S07) come back in the hands of the militia (S21). The weapon of Bohemia's answer becomes the weapon of the defense.
- **Gallows and market:** the two paths of rule (S18), split in one frame.

## Banners

Each side is known by its banner at a glance, also in a 1 s cut. The spec change `add-invasion-trailer` holds the requirement and the reference image (`openspec/changes/add-invasion-trailer/references/banners.png`).

| Side | Banner | Where |
| --- | --- | --- |
| **Hussites** | A gold chalice on a red field, as in the Jena Codex (owner decision, 2026-10-23). Tall, narrow, carried on a pole above the heads. | S08 (over the wagon fort), S09, the raid shots, S25–S27. |
| **Crusaders and the king** | A white field with a red cross (crusaders). The king's seal (S06b) uses a black eagle on gold. | Only in the history act: S06b, and the broken crusader army behind S09 if one is shown. |
| **The narrator's militia** | The player's own heraldry, made in the game's banner editor. It is the only bright, clean color in the Day look. | S20, S21, S22–S24. |

Rules:
- The chalice is always a cup with a foot and a stem, never a goblet or a grail with gems.
- Red and gold belong to the Hussites. Do not use them for the militia. Black is neutral: in the Jena Codex the crusader knights wear black plate.
- The Jena Codex shows the chalice banner with the motto "Veritas vincit". Use the chalice, not the motto: text is noise at trailer speed.
- Chalice shape reference: the folio with illuminations in `design/trailer/references/museum-of-prague/` (cup, stem, knob, foot).

## Costume and arms (1429)

- Hussites: commoners, men and some women. Padded coats (gambesons), kettle hats, a little mail, no full plate. Flails, war hammers, spears, crossbows. Tall painted pavise shields.
- Leave out handguns and cannons in gameplay shots (out of scope in the mod). A panel may show one handgun behind a pavise.
- The Jena Codex armour is from about 1500. Use it for the drawing style, not for armour details.
- The militia (gameplay): the game's own unit models. Do not try to make them look like Hussites.
