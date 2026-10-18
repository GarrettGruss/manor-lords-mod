# Design: Add trailer pipeline

## Open questions
All four are decided by the user before version 0 starts (legacy spec 27).

| Question | Who decides | Notes |
|---|---|---|
| Piper (local) or a cloud TTS for the Czech lines? | The user | Piper is free and local. Czech may be too weak. |
| Which test scenario sets up the gameplay shots, and can the harness move the camera, or does the user record by hand? | The user, with a spike for the camera | Gameplay shots are version 1, not version 0. |
| Where do large assets live: local disk only, or Git LFS? | The user | Large files stay out of normal git. |
| Does `trailer/` live in the repo root or under `docs/mod/M00-invasion-mod/`? | The user | The harness must not name the mod, so the root is the likely answer. |

## Plan
`trailer.yaml` -> assets -> `build.py` -> `v<N>.mp4` -> `review.py` -> review pack -> notes -> edit `trailer.yaml`. Token cost of a pack: about 7000 tokens for 60 seconds (legacy table). `--every 2` halves it.

## Dependencies
ffmpeg is a new external tool. `build.py` and `review.py` check for it at the start. yt-dlp is only for the final review of the user's own published video.
