# Production spec

Change `add-invasion-trailer` (#408). Decisions for the `sn-motion-html` project. The story belongs to the owner (`design/mod/trailer.md`); this file records how it is produced.

| Decision | Value |
| --- | --- |
| Goal | A 60 s YouTube trailer for the Invasion Mod, and the same story as a scroll page. |
| Audience | Manor Lords players; players of medieval city builders; history fans. |
| Cut | The slow cut (`design/trailer/invasion-mod/slow/`). The fast cut differs only in 0:00–0:12. |
| Factual fidelity | Historical claims follow the facts list in `design/mod/trailer.md`. Costume follows the 1429 notes in the mood board; the Jena Codex is used for drawing style, not armour detail. |
| Chapters | 17 (see `docs/storyboard.md`). |
| Visual language | Manuscript panels (ink, parchment, flat mineral colors), Ember (the burned house), Ash and Day (gameplay). Palette: near-black, bone white, ember orange, dried-blood red, a little gold. |
| Banners | As in `openspec/changes/add-invasion-trailer/references/banners.png`: Hussites a gold chalice on red; crusaders a red cross on white; the king's seal a single-headed black eagle on gold. |
| Copy language | English only. Exceptions: the Latin line of Hus, and the Hussite hymn in Czech over the title (sung, not shown). |
| Target devices | Desktop and phone width (390 px) for the page; 1920x1080, 30 fps for the video. |
| Sound | The page is silent. The video takes a finished audio track (voices, room tone, drums, hymn) when it exists. |
| Image model | Gemini `gemini-3.1-flash-image` (Nano Banana 2) through `harness/tools/genimage.py --ref`, with public domain Jena Codex pages and approved panels as references. |
| Video model | Seedance (from `prompts/video-manifest.json`). No paid call before the owner's cost approval; `--max-clips` stays 0 until then. |
| UI preset | `folio`. Style preset `cinematic`, overridden by `prompts/style-preamble.txt`. |

## Approvals

| Gate | Status |
| --- | --- |
| Style approval (gate 1 of the skill) | Draft panels shown and accepted as guides (owner, 2026-10-23). Formal approval of `prompts/style-preamble.txt` and `docs/identity-blocks.md`: pending. |
| Content and shot-plan approval (gate 2) | Pending: `docs/storyboard.md`. |
| Paid video | Not authorized. |
