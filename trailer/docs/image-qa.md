# Image QA (task 2.2)

The final scene stills, 2026-10-23. Masters: `assets/images/scenes/<id>.png` (git-ignored). Posters: `<id>.webp`, 1920x1080 (in git). Made by `docs/make_stills.sh` with Gemini `gemini-3.1-flash-image` (Nano Banana 2) and `harness/tools/genimage.py --ref`. Rejected tries are kept in the git-ignored `runs/storyboard/rejected/`.

13 Gemini calls: 10 stills and 3 retries. The two Jena Codex regrades and the two black frames are local (FFmpeg, no API).

| Chapter | Source | Result |
| --- | --- | --- |
| `00-darkness`, `15-whisper` | Black frame, FFmpeg | Accepted. |
| `01-flint` | Gemini, Hus codex page as style reference | Accepted. |
| `02-torch` | Draft panel S04 (approved reference set) | Try 1 copied the Hus codex page (scrolls, crowd, green ground). Try 2, with `08-burned-house` as reference, set the stake inside the narrator's house. The draft panel was used instead; no extra call. |
| `03-stake` | Jena Codex page (public domain), regraded on a dark field | Accepted. The page is narrow in 16:9; the clip can push in on it. |
| `04-given-word` | Gemini, Hus page and banner sheet | Accepted. The letter's edge burns, which fits. |
| `05-answer` | Gemini, `08-burned-house` and banner sheet | Try 1 had a white shield with a cross (breaks the banner rule). Try 2 accepted: no crosses, chalice cloth on the wall. |
| `06-banner` | Gemini, battle page and banner sheet | Accepted. Tall swallowtail banner, gold chalice on red. |
| `07-red-sky` | Jena Codex battle page (public domain), regraded on a dark field | Accepted. |
| `08-burned-house` | Gemini, Hus page | Accepted. The character and room reference for 10 and 12. |
| `10-still` | Gemini, `08-burned-house` | Accepted. A closer framing than 08, as the storyboard asks. |
| `12-turn` | Draft panel S19 (approved reference set) | Try 1 pasted codex figures into the room. Try 2 kept him seated and wrote text into the image. The draft panel was used instead; no extra call. Same man as 10; the draft's wider parchment border makes it sit a little smaller. |
| `14-map` | Gemini, battle page and banner sheet | Accepted. No text. |
| `16-title` | Gemini, Hus page | Accepted. The title is set as text. |
| `09-raids`, `11-choice`, `13-battle` | Gameplay captures | Not made yet (tasks 4.1 and 4.2). |

## Lessons for the next stills

- A reference image with strong figures gets copied, even when the prompt says not to. The Hus page did this twice. For people and rooms, use our own approved stills as references, not the codex pages.
- An own still used as a reference can pull its whole room into the new image (try 2 of `02-torch`). Use it only for shots set in that room.
- Say "no text" in every prompt; the model still added a caption once.
