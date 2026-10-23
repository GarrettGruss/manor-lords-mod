## Context

The upstream skill (see `.claude/skills/sn-motion-html/UPSTREAM.md`) has these parts:

- `scripts/init_project.py`: copies `assets/template/` into a new story project.
- `scripts/seedance_pipeline.py`: dives (scene clips) in parallel, then connectors from real boundary frames, then FFmpeg normalization. Ark async task API.
- `scripts/verify_media.py`, `contact_sheet.py`, `make_posters.py`, `serve_project.py`.
- `assets/template/src/motion-runtime.js`: one fixed stage. Scroll progress maps to one ordered timeline of clips.

## Decisions

1. **Keep the skill separate from the harness.** It goes in `.claude/skills/sn-motion-html/` with `spec/`, `scripts/`, `tests/`. It imports nothing from `harness/`. Reason: owner rule (memory "keep skills separate from harness").
2. **Keep upstream changes small and marked.** Each changed upstream file gets a short comment at the top that says what this repo changed. This makes a later upstream update easier.
3. **Key lookup order:** `SEEDANCE_API_KEY`, `ARK_API_KEY`, `VOLCENGINE_API_KEY` from the environment; then the same names from the project `.env`; then the Windows user registry through `powershell.exe` (same method as `harness/tools/genimage.py`). The key value is never printed or logged.
4. **Video export drives the page, not the clips.** `export_video.py` loads the page with a query flag (`?export=1`). In export mode the runtime exposes `window.__story.seek(t)` and ignores scroll. The script steps `t` at the target frame rate, waits until the video frame and fonts are ready, and takes a screenshot. FFmpeg joins the PNG frames into H.264 MP4. Reason: text, gradients and seal marks are HTML; only a page capture keeps them.
5. **Timing file.** `content/timing.json` gives the seconds each scene and connector takes in the video, and holds times for each chapter copy. The scroll page ignores it. The video export uses it. Reason: a reader scrolls at any speed, but the trailer must hit voice and music marks.
6. **Headless browser:** Playwright for Python (`uv add playwright`). Chromium is installed with `uv run python -m playwright install chromium`. Alternative was a Node script, but the repo uses Python tools.
7. **Spend guard:** `--max-clips N` (default 0 = dry run only) and a spend log `logs/spend.jsonl` in the story project.

## Open questions

- Provider region: Volcengine Ark (China) or BytePlus ModelArk (international)? Answered by a dry-run request against each base URL with the key (task 2.2; no clip is created).
- Model ID and price for each second of video at the chosen resolution. Answered from the provider console by the owner, and recorded in `notes/provider.md`.
- Does a headless Chromium decode H.264 in WSL? Playwright's Chromium may lack the codec. Spike in task 3.1; fallback is Playwright's bundled Chrome channel or WebM (VP9) clips.

## Risks

- Seedance output drifts from the woodcut style. Mitigation: the still gate and first/last frame conditioning.
- Frame-exact seeking in a `<video>` element can show the wrong frame. Mitigation: wait for `requestVideoFrameCallback` after each seek, and compare a contact sheet of the export with the clip frames.
