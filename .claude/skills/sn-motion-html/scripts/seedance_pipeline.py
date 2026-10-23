#!/usr/bin/env python3
"""Generate normalized scene and connector clips from a motion-story manifest.

Changed in manor-lords-mod (see UPSTREAM.md): key lookup with SEEDANCE_API_KEY and the
Windows user registry, a paid-request cap (--max-clips, default 0 = no paid request),
a spend log without secrets, no retry on account or billing errors, a free key check
before the first upload, and a second provider: ElevenLabs (`"provider": "elevenlabs"`
in the manifest), which serves Veo 3.1 and Seedance through `/v1/flows/video`.
"""

from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import mimetypes
import os
from pathlib import Path
import shutil
import threading
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


KEY_NAMES = ("SEEDANCE_API_KEY", "ARK_API_KEY", "VOLCENGINE_API_KEY")
ELEVENLABS_KEY_NAMES = ("ELEVENLABS_API_KEY",)
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"
# ElevenLabs failure reasons that the same request cannot fix.
ELEVENLABS_FINAL_FAILURES = {"moderated", "invalid_parameters", "charging_failed"}
FATAL_HTTP_STATUS = {401, 402, 403}
FATAL_ERROR_CODES = (
    '"ModelNotOpen"', '"AccessDenied"', '"InvalidAuthentication"', '"InvalidParameter"',
    '"AuthenticationError"', '"AccountOverdueError"', '"InsufficientBalance"', '"QuotaExceeded"',
)


class NonRetryableArkError(RuntimeError):
    """An account or request error another identical attempt cannot fix."""


class SpendCapReached(RuntimeError):
    """The batch would send more paid requests than --max-clips allows."""


class SpendGuard:
    """Counts paid task creations against a cap and logs each one without secrets."""

    def __init__(self, cap: int, log_path: Path) -> None:
        self.cap = cap
        self.used = 0
        self.log_path = log_path
        self.lock = threading.Lock()

    def reserve(self, clip_id: str) -> None:
        with self.lock:
            if self.used >= self.cap:
                raise SpendCapReached(f"--max-clips {self.cap} reached before {clip_id}")
            self.used += 1

    def release(self) -> None:
        """Give a slot back when the request created no task: the provider charges nothing for it."""
        with self.lock:
            self.used = max(0, self.used - 1)

    def log(self, record: dict[str, Any]) -> None:
        line = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}
        with self.lock:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(line, ensure_ascii=False) + "\n")


def windows_user_variable(name: str) -> str:
    """Read a Windows user-scope variable, also from WSL, because a shell started before
    the variable was set does not see it."""
    exe = shutil.which("powershell.exe")
    if exe is None:
        return ""
    command = f"[Environment]::GetEnvironmentVariable('{name}','User')"
    try:
        result = subprocess.run(
            [exe, "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip()


def find_api_key(names: tuple[str, ...] = KEY_NAMES) -> str:
    for name in names:
        if os.getenv(name, "").strip():
            return os.environ[name].strip()
    for name in names:
        value = windows_user_variable(name)
        if value:
            return value
    raise SystemExit(
        f"No API key found. Set {' or '.join(names)} in the environment, the project .env, "
        "or the Windows user variables."
    )


def base_url() -> str:
    return os.getenv("SEEDANCE_BASE_URL") or os.getenv("ARK_BASE_URL") or DEFAULT_BASE_URL


def load_dotenv(root: Path) -> None:
    path = root / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class ArkClient:
    def __init__(self, key: str, base_url: str) -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "User-Agent": "sn-motion-html/1.0",
            },
        )
        try:
            with urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            fatal = exc.code in FATAL_HTTP_STATUS or any(code in detail for code in FATAL_ERROR_CODES)
            error_type = NonRetryableArkError if fatal else RuntimeError
            raise error_type(f"Ark HTTP {exc.code}: {detail[:800]}") from exc
        except URLError as exc:
            raise RuntimeError(f"Ark network error: {exc.reason}") from exc

    def create(self, payload: dict[str, Any]) -> str:
        result = self.request("POST", "/contents/generations/tasks", payload)
        if not result.get("id"):
            raise RuntimeError(f"Ark response missing task id: {result}")
        return str(result["id"])

    def wait(self, task_id: str, poll_seconds: int, timeout_seconds: int) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            result = self.request("GET", f"/contents/generations/tasks/{task_id}")
            status = str(result.get("status", ""))
            print(f"  {task_id}: {status or 'unknown'}", flush=True)
            if status == "succeeded":
                return result
            if status in {"failed", "cancelled", "expired"}:
                raise RuntimeError(f"Ark task {task_id} ended as {status}: {result}")
            time.sleep(poll_seconds)
        raise TimeoutError(f"Ark task {task_id} timed out after {timeout_seconds}s")

    def check(self) -> None:
        """Free key check before any large upload. An empty task request creates no task: a valid
        key gets HTTP 400 (bad parameters), a bad key gets 401. Without this check, a rejected
        large upload shows only as a TLS error, because the server closes the connection early."""
        try:
            self.request("POST", "/contents/generations/tasks", {})
        except NonRetryableArkError as exc:
            if "Ark HTTP 400" in str(exc) and "AuthenticationError" not in str(exc):
                return
            raise

    def build_payload(self, manifest: dict[str, Any], prompt: str, first: Path, last: Path | None) -> dict[str, Any]:
        return build_payload(manifest, prompt, first, last)

    @staticmethod
    def video_url(result: dict[str, Any]) -> str | None:
        return result.get("content", {}).get("video_url")


def inline_image(path: Path) -> dict[str, str]:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return {"type": "inline_base64", "content_base64": base64.b64encode(path.read_bytes()).decode("ascii"),
            "mime_type": mime}


class ElevenLabsClient:
    """ElevenLabs video API: POST /v1/flows/video, GET /v1/flows/video/{id}. Auth: xi-api-key.
    Failed generations are not charged (ElevenLabs docs)."""

    FATAL_STATUS = {401, 402, 403, 422}

    def __init__(self, key: str, base_url: str = ELEVENLABS_BASE_URL) -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}", data=body, method=method,
            headers={"xi-api-key": self.key, "Content-Type": "application/json", "User-Agent": "sn-motion-html/1.0"},
        )
        try:
            with urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            error_type = NonRetryableArkError if exc.code in self.FATAL_STATUS else RuntimeError
            raise error_type(f"ElevenLabs HTTP {exc.code}: {detail[:800]}") from exc
        except URLError as exc:
            raise RuntimeError(f"ElevenLabs network error: {exc.reason}") from exc

    def check(self) -> None:
        """Free key check: reading the account creates nothing and costs nothing."""
        self.request("GET", "/v1/user")

    def build_payload(self, manifest: dict[str, Any], prompt: str, first: Path, last: Path | None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model_id": manifest["model"],
            "prompt": prompt,
            "duration_secs": int(manifest["duration"]),
            "resolution": manifest["resolution"],
            "aspect_ratio": manifest["ratio"],
            "generate_audio": bool(manifest.get("generate_audio", False)),
            "start_frame": inline_image(first),
        }
        if last is not None:
            payload["end_frame"] = inline_image(last)
        if manifest.get("negative_prompt"):
            payload["negative_prompt"] = manifest["negative_prompt"]
        return payload

    def create(self, payload: dict[str, Any]) -> str:
        result = self.request("POST", "/v1/flows/video", payload)
        if not result.get("id"):
            raise RuntimeError(f"ElevenLabs response missing generation id: {result}")
        return str(result["id"])

    def wait(self, task_id: str, poll_seconds: int, timeout_seconds: int) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            result = self.request("GET", f"/v1/flows/video/{task_id}")
            status = str(result.get("status", ""))
            print(f"  {task_id}: {status or 'unknown'}", flush=True)
            if status == "completed":
                return result
            if status == "failed":
                reason = str(result.get("failure_reason", ""))
                error_type = NonRetryableArkError if reason in ELEVENLABS_FINAL_FAILURES else RuntimeError
                raise error_type(f"ElevenLabs generation {task_id} failed ({reason}): {result.get('error_message', '')}")
            time.sleep(poll_seconds)
        raise TimeoutError(f"ElevenLabs generation {task_id} timed out after {timeout_seconds}s")

    @staticmethod
    def video_url(result: dict[str, Any]) -> str | None:
        return result.get("content_url")


def make_client(manifest: dict[str, Any]) -> ArkClient | ElevenLabsClient:
    provider = manifest.get("provider", "ark")
    if provider == "elevenlabs":
        return ElevenLabsClient(find_api_key(ELEVENLABS_KEY_NAMES), os.getenv("ELEVENLABS_BASE_URL") or ELEVENLABS_BASE_URL)
    if provider == "ark":
        return ArkClient(find_api_key(), base_url())
    raise SystemExit(f"Unknown provider in the manifest: {provider!r} (use 'ark' or 'elevenlabs')")


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "sn-motion-html/1.0"})
    with urlopen(request, timeout=180) as response, path.open("wb") as target:
        shutil.copyfileobj(response, target)


def run_ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def normalize_video(source: Path, target: Path, manifest: dict[str, Any]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    width = int(manifest.get("target_width", 1280))
    height = int(manifest.get("target_height", 720))
    fps = int(manifest.get("fps", 24))
    duration = float(manifest.get("duration", 4))
    filters = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},fps={fps},"
        f"tpad=stop_mode=clone:stop_duration={duration},trim=duration={duration},"
        "setpts=PTS-STARTPTS"
    )
    if manifest.get("generate_audio", False):
        audio_args = ["-af", f"apad,atrim=duration={duration}", "-c:a", "aac", "-b:a", "192k"]
    else:
        audio_args = ["-an"]
    run_ffmpeg([
        "-i", str(source), *audio_args, "-vf", filters,
        "-c:v", "libx264", "-preset", "slow", "-crf", str(manifest.get("crf", 20)),
        "-pix_fmt", "yuv420p", "-g", str(manifest.get("gop", 8)),
        "-keyint_min", str(manifest.get("gop", 8)), "-sc_threshold", "0",
        "-movflags", "+faststart", str(target),
    ])


def extract_frames(video: Path, first: Path, last: Path) -> None:
    first.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(["-i", str(video), "-vf", "select=eq(n\\,0)", "-frames:v", "1", str(first)])
    run_ffmpeg(["-sseof", "-0.05", "-i", str(video), "-frames:v", "1", str(last)])


def build_payload(
    manifest: dict[str, Any], prompt: str, first: Path, last: Path | None
) -> dict[str, Any]:
    mode = manifest.get("conditioning_mode", "reference_images")
    first_role = "reference_image" if mode == "reference_images" else "first_frame"
    content: list[dict[str, Any]] = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": data_uri(first)}, "role": first_role},
    ]
    if last is not None:
        last_role = "reference_image" if mode == "reference_images" else "last_frame"
        content.append({"type": "image_url", "image_url": {"url": data_uri(last)}, "role": last_role})
    payload: dict[str, Any] = {
        "model": os.getenv("SEEDANCE_MODEL") or manifest["model"],
        "content": content,
        "duration": int(manifest["duration"]),
        "resolution": manifest["resolution"],
        "ratio": manifest["ratio"],
        "generate_audio": bool(manifest.get("generate_audio", False)),
        "watermark": bool(manifest.get("watermark", False)),
    }
    if manifest.get("output_format"):
        payload["output_format"] = manifest["output_format"]
    return payload


def model_name(manifest: dict[str, Any]) -> str:
    """SEEDANCE_MODEL overrides only the Ark model; an ElevenLabs manifest names its own model."""
    if manifest.get("provider", "ark") == "elevenlabs":
        return manifest["model"]
    return os.getenv("SEEDANCE_MODEL") or manifest["model"]


def generate_clip(
    root: Path,
    client: ArkClient,
    guard: SpendGuard,
    manifest: dict[str, Any],
    kind: str,
    item: dict[str, Any],
    first: Path,
    last: Path | None,
    args: argparse.Namespace,
) -> None:
    clip_id = item["id"]
    output = root / item["output"]
    if output.exists() and output.stat().st_size > 0 and not args.force:
        print(f"skip {kind} {clip_id} (already exists)")
        return
    if not first.exists() or (last is not None and not last.exists()):
        raise FileNotFoundError(f"Missing conditioning frame for {clip_id}")

    prompt_path = root / item["prompt"]
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    style_motion_path = root / "prompts" / "style-motion.txt"
    if style_motion_path.exists():
        style_motion = style_motion_path.read_text(encoding="utf-8").strip()
        if style_motion:
            prompt = f"{style_motion}\n\n{prompt}"
    raw = root / "tmp" / "seedance" / "raw" / kind / f"{clip_id}.mp4"
    tasks = root / "tmp" / "seedance" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    safe = {
        "model": model_name(manifest),
        "kind": kind,
        "clip_id": clip_id,
        "prompt_file": item["prompt"],
        "first_frame": str(first.relative_to(root)),
        "last_frame": str(last.relative_to(root)) if last else None,
    }

    last_error: Exception | None = None
    for attempt in range(1, args.attempts + 1):
        print(f"{kind} {clip_id} attempt {attempt}/{args.attempts}", flush=True)
        guard.reserve(clip_id)
        task_id = None
        try:
            if hasattr(client, "build_payload"):
                payload = client.build_payload(manifest, prompt, first, last)
            else:
                payload = build_payload(manifest, prompt, first, last)
            task_id = client.create(payload)
            safe.update({"attempt": attempt, "task_id": task_id})
            (tasks / f"{kind}-{clip_id}-request.json").write_text(
                json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            result = client.wait(task_id, args.poll_seconds, args.timeout_seconds)
            (tasks / f"{kind}-{clip_id}-result.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            read_url = getattr(client, "video_url", None) or ArkClient.video_url
            video_url = read_url(result)
            if not video_url:
                raise RuntimeError(f"Finished task has no video URL: {task_id}")
            guard.log({**safe, "duration": manifest["duration"], "status": "succeeded",
                       "usage": result.get("usage")})
            download(str(video_url), raw)
            normalize_video(raw, output, manifest)
            print(f"saved {output.relative_to(root)}", flush=True)
            return
        except Exception as exc:
            last_error = exc
            if task_id is None and not isinstance(exc, SpendCapReached):
                guard.release()
            if task_id is not None or not isinstance(exc, SpendCapReached):
                guard.log({**safe, "attempt": attempt, "task_id": task_id,
                           "duration": manifest["duration"], "status": "error",
                           "error": type(exc).__name__})
            print(f"  failed: {exc}", file=sys.stderr, flush=True)
            if isinstance(exc, (NonRetryableArkError, SpendCapReached)):
                raise
    raise RuntimeError(f"{kind} {clip_id} failed after {args.attempts} attempts") from last_error


def run_dives(root: Path, client: ArkClient, guard: SpendGuard, manifest: dict[str, Any], args: argparse.Namespace) -> None:
    items = manifest.get("dives", [])[: args.limit or None]
    frames = root / "assets" / "video" / "frames"

    def run_one(item: dict[str, Any]) -> None:
        generate_clip(root, client, guard, manifest, "dives", item, root / item["still"], None, args)
        output = root / item["output"]
        extract_frames(output, frames / f"{item['id']}-first.png", frames / f"{item['id']}-last.png")

    if items:
        with ThreadPoolExecutor(max_workers=min(args.workers, len(items))) as executor:
            list(executor.map(run_one, items))


def run_connectors(root: Path, client: ArkClient, guard: SpendGuard, manifest: dict[str, Any], args: argparse.Namespace) -> None:
    items = manifest.get("connectors", [])[: args.limit or None]
    frames = root / "assets" / "video" / "frames"

    def run_one(item: dict[str, Any]) -> None:
        generate_clip(
            root, client, guard, manifest, "connectors", item,
            frames / f"{item['from']}-last.png", frames / f"{item['to']}-first.png", args,
        )

    if items:
        with ThreadPoolExecutor(max_workers=min(args.workers, len(items))) as executor:
            list(executor.map(run_one, items))


def pending_clips(root: Path, manifest: dict[str, Any], args: argparse.Namespace) -> int:
    """Count the clips of the chosen phase that do not exist yet (all of them with --force)."""
    groups = {"plan": ("dives", "connectors"), "all": ("dives", "connectors")}.get(
        args.phase, (args.phase,)
    )
    count = 0
    for group in groups:
        for item in manifest.get(group, [])[: args.limit or None]:
            output = root / item["output"]
            if args.force or not (output.exists() and output.stat().st_size > 0):
                count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("phase", choices=["plan", "dives", "connectors", "all"], nargs="?", default="plan")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--max-clips", type=int, default=0,
        help="Most paid task creations this run may send, retries included. 0 = none.",
    )
    parser.add_argument("--poll-seconds", type=int, default=8)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()
    if args.workers < 1 or args.attempts < 1:
        parser.error("--workers and --attempts must be at least 1")

    root = args.project_root.expanduser().resolve()
    load_dotenv(root)
    manifest = json.loads((root / "prompts" / "video-manifest.json").read_text(encoding="utf-8"))
    provider = manifest.get("provider", "ark")
    plan = {
        "provider": provider,
        "model": model_name(manifest),
        "duration": manifest["duration"],
        "resolution": manifest["resolution"],
        "ratio": manifest["ratio"],
        "dives": len(manifest.get("dives", [])),
        "connectors": len(manifest.get("connectors", [])),
        "workers": args.workers,
        "conditioning_mode": manifest.get("conditioning_mode", "reference_images"),
        "base_url": (os.getenv("ELEVENLABS_BASE_URL") or ELEVENLABS_BASE_URL) if provider == "elevenlabs" else base_url(),
        "pending_clips": pending_clips(root, manifest, args),
        "max_clips": args.max_clips,
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if args.phase == "plan":
        return 0
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required")
    pending = plan["pending_clips"]
    if pending > args.max_clips:
        raise SystemExit(
            f"{pending} clips are pending but --max-clips is {args.max_clips}. "
            "Get cost approval, then raise --max-clips."
        )
    client = make_client(manifest)
    try:
        client.check()
    except NonRetryableArkError as exc:
        raise SystemExit(f"Key check failed, no clip was requested: {exc}") from exc
    print("key check: ok", flush=True)
    guard = SpendGuard(args.max_clips, root / "logs" / "spend.jsonl")
    if args.phase in {"dives", "all"}:
        run_dives(root, client, guard, manifest, args)
    if args.phase in {"connectors", "all"}:
        run_connectors(root, client, guard, manifest, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
