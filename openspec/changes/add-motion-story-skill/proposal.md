## Why

Issue #407.

The Invasion Mod needs a trailer (`design/mod/trailer.md`). The owner wants to build it as a scroll-driven web story and then export that story as a video (chat, 2026-10-22). The skill `sn-motion-html` from SenseNova-Skills (MIT) already does most of the web story: style gate, still images, Seedance scene clips, connector clips made from real boundary frames, and a scroll page with one fixed media stage. It does not export a video, and it expects a key setup that does not match this machine.

Owner decisions (chat, 2026-10-22):

- Copy the skill into this repo and adapt it here.
- The Seedance key is the Windows user variable `SEEDANCE_API_KEY`.
- The owner waived the gate 1 pull request for this change and for `add-invasion-trailer`, because the work is pair programming. The gate 2 pull request stays.

No legacy doc folder is continued. The legacy animatic pipeline (spec 27, `openspec/changes/archive/2026-10-16-legacy-27-trailer-animatic/`) is source material only.

## What Changes

- The skill lives in `.claude/skills/sn-motion-html/`, with its own spec (`spec/README.md`), scripts and tests, like `repo-wiki` and `reliability-assessment`. `UPSTREAM.md` names the source commit. `LICENSE` keeps the MIT notice.
- Key lookup: the pipeline reads `SEEDANCE_API_KEY` from the environment, then from the project `.env`, then (on Windows or WSL) from the Windows user registry. It never prints the key. The old names `ARK_API_KEY` and `VOLCENGINE_API_KEY` still work.
- The provider base URL and model ID are settings, because the account region (Volcengine Ark or BytePlus ModelArk) decides them.
- Every paid request is written to a spend log in the project (clip id, model, duration, status, no key and no data URLs).
- A batch has a clip cap. The pipeline stops before it sends more paid requests than the cap.
- New script `export_video.py`: it opens the scroll page in a headless browser, sets the timeline progress frame by frame, captures each frame, and joins the frames with FFmpeg into an MP4 at a fixed frame rate. It can add one audio track. A timing file maps scroll progress to video time, so the scroll page and the video use the same story data.
- All Python runs through `uv run python`. New packages (for example Playwright) are added with `uv add`.
- A process spec `process/trailer-production` holds the repo rules: approval gates, cost approval, and generated media kept out of git.

## Non-goals

- The trailer content itself. That is change `add-invasion-trailer`.
- Sound design, voice recording and music. The export only muxes a finished audio file.
- Hosting the scroll page in public.
- A video editor. Cuts that the timeline cannot express are out of scope.

## Capabilities

### New Capabilities

- `process/trailer-production`: rules for paid media generation and for media files in git.

The behavior of the skill itself is specified in `.claude/skills/sn-motion-html/spec/README.md`, not in `openspec/specs/` (repo rule for skills that are not game harness code).

## Impact

- New folder `.claude/skills/sn-motion-html/` (copied in commit `chore(skills): copy sn-motion-html skill`).
- `pyproject.toml` and `uv.lock` (Playwright, if chosen in the design).
- `CLAUDE.md` skill list, `.gitignore`, `CHANGELOG.md`.
- Cost: Seedance clips cost money. No paid request is sent without the owner's explicit approval for that batch.
