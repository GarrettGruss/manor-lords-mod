# Proposal: Add trailer pipeline

Issue: #133. Legacy source: `docs/harness/27-trailer-animatic/README.md`. Legacy issue: #133.

## Why
The Invasion Mod trailer (`docs/mod/M00-invasion-mod/trailer.md`) needs drafts and a cheap review. The agent cannot play video or audio. Spec 27 plans a pipeline: a shot list, a build tool, and a review pack of frames, transcript and reports. The spec is approved, but nothing is built (no `trailer/` folder). Four decisions are open (TTS for Czech, gameplay capture, asset storage, folder place).

## What Changes
- The user answers the four open questions (see `design.md`).
- Version 0: text cards and a TTS voice, `trailer/build.py`, `trailer/review.py`, unit tests for the YAML checks and the timing report.
- Later versions (gameplay clips, real art, music) are separate changes.

## Non-goals
- Final art, music or voice acting.
- Upload to YouTube.
- Judging motion, music or voice feel (the user watches the video).
- A video editing UI.

## Legacy folders
`docs/harness/27-trailer-animatic/` (read only).

## Capabilities
### New Capabilities
- `harness/trailer-pipeline`: build a draft trailer and a review pack.

### Modified Capabilities
None.

## Impact
New folder (place decided by the user), new tool ffmpeg, new Python packages added with `uv add` (a YAML reader, Pillow, a Whisper package, a TTS tool). The harness code must not name the Invasion Mod: the shot list is data.
