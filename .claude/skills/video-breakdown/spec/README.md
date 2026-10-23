# Spec: video-breakdown skill

## Purpose

Let an agent turn a reference video into the planning documents of a trailer (brief, mood board, beat sheet, two-column script, shot list with storyboard), so the user can reuse its story structure and pacing. First used on the Total War: Thrones of Britannia "Alfred the Great" trailer (2026-10-22).

## Requirements

### Extraction script

`scripts/extract_video.py <source> <out>` SHALL:

- accept a yt-dlp URL or a local video file;
- write `video.mp4` (at most `--max-height`, default 720), `audio.wav` (16 kHz mono), `transcript.txt`, `frames/` (1 fps), `storyboard/Snn.jpg` (one frame from the middle of each shot), `storyboard.jpg`, `shots.json` and `shot-list-skeleton.md`;
- take the transcript from English YouTube captions when they exist, and otherwise from faster-whisper (`--whisper` overrides this), and record the origin in `shots.json`;
- find cuts with the ffmpeg scene score (`--scene-threshold`, default 0.15), drop cuts within 0.2 s of another cut or of the ends, and make shots that cover the whole video without gaps;
- decode audio itself for Whisper, because the PyAV build that faster-whisper pulls in can fail to open files;
- write text files atomically, and fail with a clear message when ffmpeg or a command fails.

Checked by `tests/test_extract_video.py` (pure helpers) and by a manual end-to-end run on a local file (57 shots on the reference trailer, the same as the manual breakdown).

### Analysis

The agent SHALL check every cut and every important moment by eye, not only through scene detection. It SHALL write the five documents and a README, as described in `SKILL.md`.

### Copyright

- The skill SHALL treat the video, audio, transcript, frames and storyboard as the rights holder's material. They are for private study and are never committed.
- Committed documents SHALL paraphrase narration and quote only short fragments, and SHALL describe frames in words.

### Worked example

`examples/twtb-alfred-great-trailer/` SHALL hold only the written documents of the first breakdown (README and 01–05), and no media. `SKILL.md` points the agent to it as the target depth and format.

## Not in scope

- Editing or cutting a new video.
- Speaker separation, music identification or beat detection in the music track.
