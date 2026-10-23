---
name: video-breakdown
description: Break down a reference video (a trailer, a cinematic, a gameplay reel) into a brief, mood board, beat sheet, two-column script and shot list with a storyboard. Downloads a YouTube or other yt-dlp video, or reads a local file, and extracts frames, scene cuts and a transcript. Use when the user wants to study how a video is built, to reuse its story structure and pacing.
---

# Video breakdown

Turns one video into the planning documents that a trailer team writes before production, reconstructed from the finished cut. The script does the mechanical part (download, transcript, cuts, frames, storyboard). You do the analysis: you look at the frames and write the documents.

This skill is separate from the game harness. Its spec (`spec/README.md`), its script (`scripts/extract_video.py`) and its tests (`tests/`) all live in this folder.

## Copyright: what may be committed

The video, its frames and its narration belong to the rights holder. Follow these rules:

- Download only for private study, or when the user has the rights. Do not reuse the footage, frames or narration in the user's own work.
- Never commit `video.mp4`, `audio.wav`, `transcript.txt`, `frames/`, `storyboard/`, `storyboard.jpg` or any other frame or contact sheet. Put them in a gitignored folder.
- The written analysis (brief, mood board, beat sheet, script, shot list) is the user's own work and may be committed. In the script, paraphrase the voice-over and quote only a few short words. Do not paste the transcript into a committed file.
- Describe frames in words (`S35: the crowned king shouts the charge`). Refer to a frame by its shot id, not by embedding it.

## Step 1: extract

Needs `ffmpeg` and `ffprobe` on PATH. Use a new, empty output folder.

```bash
uv run --no-project --with yt-dlp --with faster-whisper --with numpy \
  python -I .claude/skills/video-breakdown/scripts/extract_video.py "<url-or-file>" <out-dir>
```

Options: `--scene-threshold 0.15` (lower finds more cuts; 0.3 finds only hard cuts), `--max-height 720`, `--whisper auto|always|never` (`auto` uses YouTube captions when they exist, otherwise Whisper).

Output in `<out-dir>`:

| File | What it holds |
| --- | --- |
| `video.mp4`, `audio.wav` | The video, and 16 kHz mono audio. |
| `transcript.txt` | `[start-end] text` lines. Whisper output over loud music is approximate. |
| `frames/f_NNN.jpg` | One frame per second; `f_NNN` is at about NNN s. |
| `storyboard/Snn.jpg`, `storyboard.jpg` | One labeled frame from the middle of each shot, and all of them on one sheet. |
| `shots.json` | Metadata, shots (`id`, `start`, `length`, `mid`) and transcript segments. |
| `shot-list-skeleton.md` | The shot list table with times filled in and the other columns empty. |

The yt-dlp warning about a missing JavaScript runtime is harmless for most videos.

## Step 2: look

1. Read `storyboard.jpg`. Read it again in parts if it is large, or read single `storyboard/Snn.jpg` files.
2. Read `transcript.txt` and place each line against the shots by time.
3. Where a moment matters (a turn, a reveal, the end of a fight), build a dense sheet of that range and read it. Story beats often happen inside one shot, and a mid-shot frame can miss them:

   ```bash
   ffmpeg -loglevel error -y -ss <start> -t <seconds> -i <out-dir>/video.mp4 \
     -vf "fps=2,scale=320:-1,drawtext=text='%{pts\:flt}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black,tile=4x4" \
     -frames:v 1 <out-dir>/detail.jpg
   ```

4. Find out where the narrator or anchor shots take place, not only who is in them. The setting is often part of the story. In the example, the king speaks from the sacked house of one of his subjects, not from a hall. Dark, low-key shots hide this, so look at the wide versions and at the props.
5. Scene detection misses slow dissolves, mostly between dark shots. A shot longer than about 8 s is suspect: read its `frames/` (1 fps) and split it by eye (`S05a`, `S05b`, …).
6. When the transcript comes from Whisper, check names and key words against the picture and any on-screen text. Whisper often gets proper names wrong. Captions, when they exist, are usually more accurate.
7. Check every scene-detection cut by eye. Fast cuts in action can merge or split. Fix the times in the shot list.

## Step 3: write the documents

Write them next to the media, or in a committed folder the user names. Start each with the source (title, channel, URL, length) and a line that says it is a reconstruction from the finished video.

1. **`01-brief.md`**: the brief the video seems to answer. Product, goal, audience, one message, tone, length (story time and branding time), format, voice, music, must-show items, call to action.
2. **`02-mood-board.md`**: the looks (name each one, with its light, color and the shot ids that use it), the camera language for each look, and the recurring motifs.
3. **`03-beat-sheet.md`**: one row per beat, with time range, length, shot ids, average shot length and an energy score (0–5). Add an ASCII pacing curve, and a "rules seen in this cut" list with numbers: share of time per act, shot length per act, where the pauses are.
4. **`04-script.md`**: two columns, picture and audio, one row per beat or per important moment. Mark the look in capitals (`FIRELIGHT.`). Paraphrase the voice-over. End with voice-over notes: word count, where the narrator is silent, how the line length changes.
5. **`05-shot-list.md`**: start from `shot-list-skeleton.md`. Fill in beat, look, shot size (W, M, C, T), camera move and content for every shot. End with counts: shots, average length, shortest and longest, how often an anchor shot returns.

Also write a `README.md` that lists the files and holds the short list of elements to reuse.

**Worked example:** `examples/twtb-alfred-great-trailer/` holds all six documents for the Total War: Thrones of Britannia "Alfred the Great" trailer (110 s, 57 shots). Read it before you write, and match its depth and format. Notable parts:
- `03-beat-sheet.md`: a sub-beat (9b) for a moment that happens inside the battle, the enemy rout. The user found it, which is why step 2 asks for dense sheets at important moments.
- `04-script.md`: the paraphrased voice-over, with only short quotes.
- `05-shot-list.md`: the full column set and the counts at the end.

The example holds no media. Its frames are not committed (see Copyright).

## Step 4: report

Give the user the folder path, the shot count, the beat structure in a few lines and the numbers worth reusing. Say what is approximate (transcript, cut times, camera moves inferred from stills). Ask the user to correct any beat you may have misread, and update all documents that the correction touches.

## Tests

```bash
uv run python -m unittest discover -s .claude/skills/video-breakdown/tests
```

The tests cover the pure helpers (cut parsing, shot building, SRT parsing, formatting). They need no network and no ffmpeg.
