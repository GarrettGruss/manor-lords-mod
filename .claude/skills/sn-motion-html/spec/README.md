# Spec: sn-motion-html skill

Status: built (2026-10-22). Issue: #407. Draft: the owner will write the full spec after the first trailer output.

This spec belongs to the skill. The skill (`SKILL.md`), this spec, the scripts and the tests live together in `.claude/skills/sn-motion-html/`. The skill imports nothing from the harness.

## Goal

Build a scroll-driven web story on one fixed media stage, from stills and Seedance clips, and export the same story as a video.

## Non-goals

- Sound design. The export only adds a finished audio file.
- Public hosting.

## Requirements

Each requirement names its test in `tests/test_pipeline_and_export.py`, or says "Checked by a test export".

1. **Key lookup.** The pipeline reads `SEEDANCE_API_KEY`, then `ARK_API_KEY`, then `VOLCENGINE_API_KEY`, from the environment (the project `.env` is loaded into it first), then from the Windows user variables. A missing key stops the run with a message that names the variables. The key is never printed or logged. (`KeyLookupTest`)
2. **Spend cap.** `--max-clips` (default 0) caps the paid task creations of one run, retries included. When the pending clips are more than the cap, the run stops before it creates a client. (`SpendCapTest`)
3. **Spend log.** Each paid request adds one JSON line to `logs/spend.jsonl`: time, clip, kind, model, attempt, task id, duration, status and usage. No key, no Authorization header, no data URL. (`GenerateClipTest`)
4. **Retries.** HTTP 401, 402 and 403, and the account, billing and activation error codes, are not retried. Other errors are retried up to `--attempts`. (`GenerateClipTest`)
5. **Export timeline.** `content/timing.json` gives the seconds of each segment. An unknown segment id is an error. Video time maps linearly into route units inside each segment; the head holds the first frame and the tail holds the last. (`ExportScheduleTest`)
6. **Export mode.** With `?export=1` the page ignores scroll, hides the page chrome, turns off CSS transitions, loads every clip as an all-intra VP9 copy, and exposes `window.__motionStory`. Checked by a test export.
7. **Export output.** The MP4 has the `timing.json` size and frame rate, H.264 `yuv420p`, and the scheduled duration. Checked by a test export (`ffprobe`).
8. **Media out of git.** The project template ignores `assets/video/`, PNG scene masters, `tmp/`, `logs/` and `export/`. Checked by review.
