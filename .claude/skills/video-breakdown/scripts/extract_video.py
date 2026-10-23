"""Extract a video into material an agent can analyze: video, audio, transcript, frames, shots and a storyboard.

Run with its dependencies (spec: .claude/skills/video-breakdown/spec/README.md):

    uv run --no-project --with yt-dlp --with faster-whisper --with numpy \
        python -I .claude/skills/video-breakdown/scripts/extract_video.py <url-or-file> <out-dir>

Needs ffmpeg and ffprobe on PATH.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

DEFAULT_SCENE_THRESHOLD = 0.15
DEFAULT_MAX_HEIGHT = 720
STORYBOARD_COLUMNS = 6
FRAME_WIDTH = 320
WHISPER_MODEL = "small"


# ---------- pure helpers (unit tested) ----------

def parse_scene_times(showinfo_log):
    """Return the cut times (seconds) that ffmpeg's showinfo filter printed."""
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", showinfo_log)]


def build_shots(cut_times, duration, min_length=0.2):
    """Turn cut times into shots [{id, start, length, mid}], merging cuts closer than min_length."""
    bounds = [0.0]
    for t in sorted(cut_times):
        if min_length <= t <= duration - min_length and t - bounds[-1] >= min_length:
            bounds.append(t)
    bounds.append(duration)
    shots = []
    for i, (start, end) in enumerate(zip(bounds, bounds[1:]), start=1):
        shots.append({
            "id": f"S{i:02d}",
            "start": round(start, 2),
            "length": round(end - start, 2),
            "mid": round((start + end) / 2, 2),
        })
    return shots


def parse_srt(text):
    """Return [{start, end, text}] from SRT text. Repeated lines (auto captions) are dropped."""
    segments = []
    pattern = re.compile(
        r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)[^\n]*\n(.*?)(?:\n\s*\n|\Z)", re.S)
    for m in pattern.finditer(text):
        h1, m1, s1, ms1, h2, m2, s2, ms2, body = m.groups()
        line = " ".join(re.sub(r"<[^>]+>", "", body).split())
        if not line or (segments and segments[-1]["text"] == line):
            continue
        segments.append({
            "start": int(h1) * 3600 + int(m1) * 60 + int(s1) + int(ms1) / 1000,
            "end": int(h2) * 3600 + int(m2) * 60 + int(s2) + int(ms2) / 1000,
            "text": line,
        })
    return segments


def format_transcript(segments):
    """Return one line per segment: '[start-end] text'."""
    return "".join(f"[{s['start']:6.1f}-{s['end']:6.1f}] {s['text']}\n" for s in segments)


def shot_list_markdown(shots):
    """Return a Markdown table skeleton of the shots, for the agent to fill in."""
    rows = ["| Shot | Start (s) | Length (s) | Beat | Look | Size | Camera | Content |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    rows += [f"| {s['id']} | {s['start']:.1f} | {s['length']:.1f} |  |  |  |  |  |" for s in shots]
    return "\n".join(rows) + "\n"


# ---------- steps with side effects ----------

def run(cmd):
    """Run a command and fail loudly with its output."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(map(str, cmd))}\n{result.stderr[-2000:]}")
    return result


def require_tools():
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        raise RuntimeError(f"Missing tools on PATH: {', '.join(missing)}. Install ffmpeg.")


COOKIE_ARGS = []


def yt_dlp(*args):
    return run([sys.executable, "-m", "yt_dlp", "--no-warnings", *COOKIE_ARGS, *args])


def fetch_video(source, out, max_height):
    """Download the video (or copy a local file) to out/video.mp4. Returns the metadata."""
    video = out / "video.mp4"
    if Path(source).is_file():
        shutil.copyfile(source, video)
        return {"source": str(source)}
    info = json.loads(yt_dlp("--skip-download", "--dump-single-json", source).stdout)
    if not video.exists():
        yt_dlp("-f", f"bv*[height<={max_height}]+ba/b[height<={max_height}]/b",
               "--merge-output-format", "mp4", "-o", str(video), source)
    return {"source": source, "title": info.get("title"), "uploader": info.get("uploader"),
            "duration": info.get("duration"), "upload_date": info.get("upload_date")}


def fetch_captions(source, out):
    """Download English captions as SRT. Returns the segments, or [] when there are none."""
    if Path(source).is_file():
        return []
    try:
        yt_dlp("--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "en.*",
               "--convert-subs", "srt", "-o", str(out / "captions"), source)
    except RuntimeError as error:
        # YouTube often rate-limits caption requests (HTTP 429). Whisper is the fallback.
        print(f"Captions failed, using Whisper instead: {str(error).splitlines()[0]}")
        return []
    files = sorted(out.glob("captions*.srt"))
    return parse_srt(files[0].read_text(encoding="utf-8")) if files else []


def extract_audio(video, out):
    audio = out / "audio.wav"
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
    return audio


def transcribe(audio):
    """Transcribe 16 kHz mono WAV with faster-whisper. Audio is decoded here, not by PyAV."""
    import numpy as np
    from faster_whisper import WhisperModel
    with wave.open(str(audio)) as w:
        samples = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    model = WhisperModel(WHISPER_MODEL, compute_type="int8")
    segments, _ = model.transcribe(samples)
    return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]


def video_duration(video):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)])
    return float(out.stdout.strip())


def detect_cuts(video, threshold):
    result = run(["ffmpeg", "-i", str(video), "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    return parse_scene_times(result.stderr)


def extract_frames(video, out):
    """One frame per second: frames/f_001.jpg is at about 1 s."""
    frames = out / "frames"
    frames.mkdir(exist_ok=True)
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-vf", f"fps=1,scale={FRAME_WIDTH * 3 // 2}:-1",
         str(frames / "f_%03d.jpg")])


def extract_storyboard(video, out, shots):
    """One labeled frame from the middle of each shot, and one sheet with all of them."""
    board = out / "storyboard"
    board.mkdir(exist_ok=True)
    for s in shots:
        label = f"{s['id']}  {s['start']:.1f}s"
        run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(s["mid"]), "-i", str(video), "-frames:v", "1",
             "-vf", f"scale={FRAME_WIDTH}:-1,drawtext=text='{label}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black",
             str(board / f"{s['id']}.jpg")])
    rows = -(-len(shots) // STORYBOARD_COLUMNS)
    run(["ffmpeg", "-loglevel", "error", "-y", "-pattern_type", "glob", "-i", str(board / "S*.jpg"),
         "-vf", f"tile={STORYBOARD_COLUMNS}x{rows}:padding=2", "-frames:v", "1", str(out / "storyboard.jpg")])


def write_text(path, text):
    """Write atomically: .tmp, then rename."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", help="A video URL (YouTube or any yt-dlp site) or a local video file.")
    parser.add_argument("out", type=Path, help="Output folder. Use a new, empty folder.")
    parser.add_argument("--scene-threshold", type=float, default=DEFAULT_SCENE_THRESHOLD,
                        help="ffmpeg scene score for a cut. Lower finds more cuts.")
    parser.add_argument("--max-height", type=int, default=DEFAULT_MAX_HEIGHT)
    parser.add_argument("--whisper", choices=("auto", "always", "never"), default="auto",
                        help="auto: transcribe only when there are no captions.")
    parser.add_argument("--cookies", type=Path,
                        help="A Netscape cookies.txt file, for age-restricted videos. Keep it out of git.")
    args = parser.parse_args(argv)

    if args.cookies:
        if not args.cookies.is_file():
            raise SystemExit(f"Cookies file not found: {args.cookies}")
        COOKIE_ARGS[:] = ["--cookies", str(args.cookies)]
    require_tools()
    args.out.mkdir(parents=True, exist_ok=True)
    print("1/6 video"); meta = fetch_video(args.source, args.out, args.max_height)
    video = args.out / "video.mp4"
    meta["duration"] = video_duration(video)

    print("2/6 transcript")
    segments, origin = [], "none"
    if args.whisper != "always":
        segments = fetch_captions(args.source, args.out)
        origin = "captions" if segments else origin
    audio = extract_audio(video, args.out)
    if args.whisper == "always" or (args.whisper == "auto" and not segments):
        segments, origin = transcribe(audio), f"whisper-{WHISPER_MODEL}"
    write_text(args.out / "transcript.txt", format_transcript(segments))

    print("3/6 cuts"); shots = build_shots(detect_cuts(video, args.scene_threshold), meta["duration"])
    print("4/6 frames"); extract_frames(video, args.out)
    print("5/6 storyboard"); extract_storyboard(video, args.out, shots)

    print("6/6 index")
    meta.update({"transcript_origin": origin, "scene_threshold": args.scene_threshold, "shot_count": len(shots)})
    write_text(args.out / "shots.json", json.dumps({"meta": meta, "shots": shots, "transcript": segments}, indent=2))
    write_text(args.out / "shot-list-skeleton.md", shot_list_markdown(shots))
    print(f"Done: {len(shots)} shots, transcript from {origin}, in {args.out}")


if __name__ == "__main__":
    main()
