# Spec 27: Trailer animatic and review pipeline

Status: approved with open decisions TBD (2026-10-16). Branch: `feat/27-trailer-animatic`. Issue: #133.

## Goal
Build trailer drafts from a timed shot list, and let the agent review each draft at a low token cost.
The first target is the Invasion Mod trailer (`design/mod/trailer.md`), a YouTube video of 60 seconds or less.

The agent cannot play video or audio, and it cannot read a YouTube page's content.
So the pipeline turns a video into data the agent can read: contact sheets of frames, a timed transcript, and timing and audio reports.

## Non-goals
- No final art, music or voice acting. The pipeline makes drafts (animatics).
- No upload to YouTube from the harness. The user uploads by hand.
- No judgment of motion, music feel or voice emotion by the agent. The user watches the video for that.
- No video editing UI.

## Plan
```
trailer.yaml ──► assets ──► build.py ──► vN.mp4 ──► review.py ──► review pack ──► notes ──► edit trailer.yaml
```

1. **Shot list file** `trailer/trailer.yaml`. One entry per shot:
   - `start`, `end` (seconds)
   - `type`: `panel`, `gameplay`, `black` or `title`
   - `source`: image or clip path (a missing source makes a text card with the shot description)
   - `voice`: text, language, and the voice id
   - `subtitle`: text (optional)
   - `sound`: music and sound cues
2. **Assets** in `trailer/assets/` (large files stay out of git):
   - Panels: text cards at first, art later.
   - Gameplay: clips recorded from the real game. A harness scenario sets up the scene. ffmpeg (`gdigrab`) or OBS records it.
   - Voice: text-to-speech for drafts (Piper locally; a cloud service for Czech if Piper is too weak). Real voice actors only for the final cut.
   - Music: a temporary free track.
3. **Build** `uv run python trailer/build.py`:
   - reads the YAML
   - renders each shot (slow zoom on panels, cut-in clips, burned-in subtitles)
   - mixes the voice and the music
   - writes `trailer/out/v<N>.mp4`
   - fails loudly if the total is over 60 seconds or a source file is missing
4. **Review** `uv run python trailer/review.py <video>` writes `trailer/out/v<N>-review/`:
   - `sheet-<k>.png`: contact sheets, 16 frames each, one frame every 1 second (option `--every 2`), each frame with its time stamp
   - `key-<time>.png`: full frames at the shot starts that the YAML marks as `key: true`
   - `transcript.json`: Whisper output with time stamps
   - `timing.md`: total length, length of each shot, lines compared with their slots, shots under 1 second, subtitles shown too briefly to read
   - `audio.md`: loudness (ffmpeg `ebur128`), silences, peaks
   - `summary.md`: the file the agent reads first. It lists the problems found and the files to open.
5. **Agent review:** the agent reads `summary.md`, then the sheets and the reports, and writes notes with time stamps.
   The notes go to `trailer/notes/v<N>.md`.
6. **Human review:** the user watches the mp4. Before release: an unlisted YouTube upload for play testers.
   The final file gets the same review once more.

### Steps in order
1. Version 0: text cards, a TTS voice, no gameplay. It tests the script, the timing and the Czech-to-English switch.
2. Version 1: gameplay clips recorded with the harness.
3. Version 2: real panel art, music and sound.

## Token cost
For a 60-second trailer, the review pack costs about 7,000 tokens:

| Item | Size | Approx. tokens |
| --- | --- | --- |
| Contact sheets | 4 images, 16 frames each | 6,000 |
| Transcript | about 75 words | 300 |
| Timing and audio reports | short text | 600 |

Cost grows with the number of images, not with the video length. `--every 2` halves it.

## Tools and dependencies
- ffmpeg: a new external tool, not a Python package. `build.py` and `review.py` check for it at start and fail with a clear message.
- Python packages, added with `uv add`: a YAML reader, Pillow (contact sheets), a Whisper package (for example `faster-whisper`), a TTS package or CLI (Piper).
- yt-dlp: only to fetch the user's own published video, with its captions, for the final review.

## Open questions
All decisions are TBD. The user decides them before version 0 starts.
1. Piper or a cloud TTS for the Czech lines? **Decision: TBD.**
2. Which scenario sets up the gameplay shots (a raid on a burning village)? Can the harness move the camera, or does the user record those clips by hand? **Decision: TBD.**
3. Where do large assets live: only on the local disk, or in Git LFS? **Decision: TBD.**
4. Does `trailer/` belong in the repo root, or under `design/`? **Decision: TBD.**

## Acceptance criteria
- A1: `build.py` turns a YAML with text-card shots and TTS voice into an mp4 of 60 seconds or less.
- A2: `build.py` fails with a clear message when the total is over 60 seconds or a source is missing.
- A3: `review.py` writes the contact sheets, transcript, timing, audio and summary files for a 60-second video.
- A4: the review pack of a 60-second video costs 8,000 tokens or less for the agent to read (sheets at 1 frame per second).
- A5: the timing report finds a voice line that runs past its slot (tested with a planted error).
- A6: the audio report finds the silence at 0:54 to 0:57 in the version 0 build.
- A7: unit tests cover the YAML checks and the timing report, without ffmpeg.
