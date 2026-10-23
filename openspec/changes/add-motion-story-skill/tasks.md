## 1. Skill setup

- [x] 1.1 Copy the upstream skill with its MIT license and `UPSTREAM.md`. Verified by review (commit `chore(skills): copy sn-motion-html skill`).
- [ ] 1.2 Write `.claude/skills/sn-motion-html/spec/README.md` (skill spec: init, pipeline, key lookup, spend guard, export, timing file). Verified by review.
- [ ] 1.3 Change `SKILL.md` and the references to `uv run python`, this repo's gates, and `process/trailer-production`. Verified by review.
- [ ] 1.4 Add the media and `.env` patterns of story projects to `.gitignore`. Verified by `git status` after a test render.

## 2. Seedance pipeline

- [ ] 2.1 Key lookup (`SEEDANCE_API_KEY`, old names, `.env`, Windows registry), never printed. Verified by tests in `tests/` with a fake environment.
- [ ] 2.2 Base URL and model as settings; dry-run request to find the region. Record the result in `notes/provider.md`. Verified by one call that creates no clip.
- [ ] 2.3 `--max-clips` cap, no retry on auth, billing or activation errors, spend log without secrets. Verified by tests with a fake HTTP client.

## 3. Video export

- [ ] 3.1 Spike: headless Chromium plays and seeks H.264 clips in WSL. Record in `notes/export-spike.md`. Verified by a 2 s test export.
- [ ] 3.2 `export=1` mode in `motion-runtime.js` with `window.__story.seek(t)`. Verified by a test export of the template story.
- [ ] 3.3 `content/timing.json` schema and reader. Verified by tests in `tests/`.
- [ ] 3.4 `scripts/export_video.py`: frames at a fixed frame rate, FFmpeg join, optional audio track, `ffprobe` check of duration and frame rate. Verified by tests and a test export.

## 4. Close

- [ ] 4.1 Update `CLAUDE.md` (skill list), the wiki (`repo-wiki` stale check) and `CHANGELOG.md`. Verified by `wiki.py check`.
- [ ] 4.2 Run the skill tests and `openspec validate add-motion-story-skill --strict`.
- [ ] 4.3 Archive the change as the last commit.
- [ ] 4.4 Test results table for the implementation pull request.
