#!/usr/bin/env python3
"""Export a motion story page as an MP4 video.

Added in manor-lords-mod (see UPSTREAM.md). The script serves the project, opens the
page in headless Chromium with ?export=1, steps the story timeline frame by frame
with content/timing.json, captures each frame, and joins the frames with FFmpeg.

Usage:
  uv run python scripts/export_video.py PROJECT_ROOT [--out export/story.mp4] [--audio track.wav]
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import partial
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
# Keep the browser download in the (git-ignored) skill folder, not in the user cache.
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(SKILL_ROOT / ".browsers"))

sys.path.insert(0, str(Path(__file__).resolve().parent))
from serve_project import SafeHandler  # noqa: E402

DEFAULT_TIMING = {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "default_scene_seconds": 4.0,
    "default_connector_seconds": 1.5,
    "seconds": {},
    "head_seconds": 0.0,
    "tail_seconds": 1.0,
}


@dataclass(frozen=True)
class TimedSegment:
    segment_id: str
    start_units: float
    units: float
    start_seconds: float
    seconds: float


def load_timing(root: Path) -> dict[str, Any]:
    path = root / "content" / "timing.json"
    timing = dict(DEFAULT_TIMING)
    if path.exists():
        timing.update(json.loads(path.read_text(encoding="utf-8")))
    for key in ("width", "height", "fps"):
        if int(timing[key]) <= 0:
            raise SystemExit(f"timing.json: {key} must be positive")
    return timing


def build_schedule(segments: list[dict[str, Any]], timing: dict[str, Any]) -> list[TimedSegment]:
    """Give each page segment its video seconds. Unknown ids in timing.json are an error,
    because a typo would silently fall back to the default length."""
    known = {segment["id"] for segment in segments}
    unknown = sorted(set(timing["seconds"]) - known)
    if unknown:
        raise SystemExit(f"timing.json names unknown segments: {', '.join(unknown)}. Known: {', '.join(sorted(known))}")
    schedule: list[TimedSegment] = []
    units = 0.0
    seconds = float(timing["head_seconds"])
    for segment in segments:
        default = timing["default_scene_seconds"] if segment["kind"] == "scene" else timing["default_connector_seconds"]
        length = float(timing["seconds"].get(segment["id"], default))
        if length <= 0:
            raise SystemExit(f"timing.json: {segment['id']} must last more than 0 s")
        schedule.append(TimedSegment(segment["id"], units, float(segment["units"]), seconds, length))
        units += float(segment["units"])
        seconds += length
    return schedule


def total_seconds(schedule: list[TimedSegment], timing: dict[str, Any]) -> float:
    last = schedule[-1]
    return last.start_seconds + last.seconds + float(timing["tail_seconds"])


def route_units_at(schedule: list[TimedSegment], time: float) -> float:
    """Map video time to route units. The head holds the first frame; the tail holds the last."""
    if time <= schedule[0].start_seconds:
        return 0.0
    for segment in schedule:
        if time < segment.start_seconds + segment.seconds:
            fraction = (time - segment.start_seconds) / segment.seconds
            return segment.start_units + fraction * segment.units
    last = schedule[-1]
    # Stop just inside the last segment so its copy stays visible.
    return last.start_units + last.units * 0.999


def story_clips(root: Path) -> list[str]:
    story = json.loads((root / "content" / "story.json").read_text(encoding="utf-8"))
    clips = [chapter.get("clip") for chapter in story.get("chapters", [])]
    clips += story.get("connectors", [])
    return [clip for clip in clips if clip]


def make_export_clips(root: Path) -> None:
    """Write all-intra VP9 copies of the clips. All-intra makes every seek exact."""
    for clip in story_clips(root):
        source = root / clip
        if not source.exists():
            continue
        target = root / "tmp" / "export-clips" / Path(clip).with_suffix(".webm")
        if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        print(f"VP9 copy of {clip}", flush=True)
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", str(source), "-an", "-c:v", "libvpx-vp9",
            "-g", "1", "-crf", "18", "-b:v", "0", "-row-mt", "1", "-deadline", "good", str(target),
        ], check=True)


class QuietHandler(SafeHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass


def start_server(root: Path) -> tuple[ThreadingHTTPServer, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"


def capture_frames(url: str, timing: dict[str, Any], frames_dir: Path, limit_seconds: float | None) -> float:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright is missing. Run: uv add --dev playwright") from None

    fps = int(timing["fps"])
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        except Exception as exc:
            if "Executable doesn't exist" in str(exc):
                raise SystemExit(
                    "Chromium is missing. Run: PLAYWRIGHT_BROWSERS_PATH="
                    f"{os.environ['PLAYWRIGHT_BROWSERS_PATH']} uv run python -m playwright install chromium"
                ) from None
            raise
        page = browser.new_page(viewport={"width": int(timing["width"]), "height": int(timing["height"])})
        page.on("pageerror", lambda error: print(f"page error: {error}", file=sys.stderr))
        page.goto(f"{url}?export=1")
        page.wait_for_function("window.__motionStory !== undefined", timeout=30000)
        loaded = page.evaluate("window.__motionStory.ready()")
        segments = page.evaluate("window.__motionStory.segments()")
        page.wait_for_selector("#boot", state="detached", timeout=10000)
        missing = [segment["id"] for segment, ok in zip(segments, loaded) if segment["hasClip"] and not ok]
        if missing:
            print(f"warning: clips not loaded, posters used: {', '.join(missing)}", file=sys.stderr)

        schedule = build_schedule(segments, timing)
        duration = total_seconds(schedule, timing)
        if limit_seconds is not None:
            duration = min(duration, limit_seconds)
        frame_count = round(duration * fps)
        print(f"capturing {frame_count} frames ({duration:.2f} s at {fps} fps)", flush=True)
        for index in range(frame_count):
            page.evaluate("(units) => window.__motionStory.seek(units)", route_units_at(schedule, index / fps))
            page.screenshot(path=str(frames_dir / f"{index:06d}.png"))
            if index % (fps * 5) == 0:
                print(f"  {index / fps:5.1f} s", flush=True)
        browser.close()
    return duration


def encode(frames_dir: Path, timing: dict[str, Any], duration: float, audio: Path | None, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-v", "error", "-y", "-framerate", str(timing["fps"]), "-i", str(frames_dir / "%06d.png")]
    if audio is not None:
        command += ["-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k",
                    "-af", f"apad,atrim=duration={duration}"]
    command += ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                "-t", f"{duration}", "-movflags", "+faststart", str(out)]
    subprocess.run(command, check=True)


def probe(path: Path) -> dict[str, Any]:
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path),
    ], text=True)
    return json.loads(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--out", type=Path, default=Path("export/story.mp4"), help="Relative to the project root.")
    parser.add_argument("--audio", type=Path, help="Audio track to mux in; padded or cut to the video length.")
    parser.add_argument("--seconds", type=float, help="Export only the first N seconds (for a quick check).")
    parser.add_argument("--keep-frames", action="store_true", help="Keep PNG frames in tmp/export-frames.")
    args = parser.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise SystemExit(f"{tool} is required")
    root = args.project_root.expanduser().resolve()
    if args.audio is not None and not args.audio.exists():
        raise SystemExit(f"audio file not found: {args.audio}")
    out = args.out if args.out.is_absolute() else root / args.out
    timing = load_timing(root)
    make_export_clips(root)

    server, url = start_server(root)
    try:
        if args.keep_frames:
            frames_dir = root / "tmp" / "export-frames"
            shutil.rmtree(frames_dir, ignore_errors=True)
            frames_dir.mkdir(parents=True)
            duration = capture_frames(url, timing, frames_dir, args.seconds)
            encode(frames_dir, timing, duration, args.audio, out)
        else:
            with tempfile.TemporaryDirectory(prefix="motion-export-") as temp:
                duration = capture_frames(url, timing, Path(temp), args.seconds)
                encode(Path(temp), timing, duration, args.audio, out)
    finally:
        server.shutdown()
    print(json.dumps({"output": str(out), **probe(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
