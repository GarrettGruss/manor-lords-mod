"""Make a 3D model with the Meshy API (offline art tool, spec 21).

Usage:
  uv run python harness/tools/genmesh.py balance
  uv run python harness/tools/genmesh.py multi --image a.png --image b.png --out runs/genmesh/ladder [--polycount 2000]

The key comes from MESHY_API_KEY (environment, else Windows user scope). It is never
printed, logged or written. Every task is appended to runs/genmesh/log.jsonl with its
credits. A call is refused when its estimated cost passes MAX_CREDITS_PER_CALL, or when
the credits logged today plus the estimate pass MAX_CREDITS_PER_DAY.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_ROOT = "https://api.meshy.ai/openapi/v1"
MAX_CREDITS_PER_CALL = 60
MAX_CREDITS_PER_DAY = 200
MULTI_IMAGE_TEXTURED_COST = 30  # meshy-6, 2k texture (docs.meshy.ai api/pricing)
POLL_SECONDS = 10
POLL_TIMEOUT_SECONDS = 1200
REPO = Path(__file__).resolve().parents[2]
LOG_FILE = REPO / "runs" / "genmesh" / "log.jsonl"


def api_key() -> str:
    key = os.environ.get("MESHY_API_KEY", "").strip()
    if not key and sys.platform == "win32":
        key = _user_scope_key()
    if not key:
        raise SystemExit("MESHY_API_KEY is not set (environment or Windows user scope).")
    return key


def _user_scope_key() -> str:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env:
            value, _ = winreg.QueryValueEx(env, "MESHY_API_KEY")
            return str(value).strip()
    except OSError:
        return ""


def call_api(method: str, path: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(
        f"{API_ROOT}/{path}",
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:500]
        raise SystemExit(f"Meshy API error {error.code}: {detail}") from None


def download(url: str, target: Path) -> None:
    # Signed asset URLs need no key. Do not send it to another host.
    with urllib.request.urlopen(url, timeout=300) as response:
        target.write_bytes(response.read())


def image_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def credits_used_today(log_file: Path) -> int:
    if not log_file.exists():
        return 0
    today = time.strftime("%Y-%m-%d")
    total = 0
    for line in log_file.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if entry.get("time", "").startswith(today):
            total += int(entry.get("credits", 0))
    return total


def check_caps(estimate: int, log_file: Path) -> None:
    if estimate > MAX_CREDITS_PER_CALL:
        raise SystemExit(f"Refused: estimate {estimate} credits is above the per-call cap {MAX_CREDITS_PER_CALL}.")
    used = credits_used_today(log_file)
    if used + estimate > MAX_CREDITS_PER_DAY:
        raise SystemExit(f"Refused: {used} used today + {estimate} is above the per-day cap {MAX_CREDITS_PER_DAY}.")


def log_call(entry: dict, log_file: Path = LOG_FILE) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry) + "\n")


def build_payload(images: list[str], polycount: int, model: str) -> dict:
    if not 1 <= len(images) <= 4:
        raise SystemExit("Multi-image needs 1 to 4 images.")
    return {
        "image_urls": images,
        "ai_model": model,
        "should_texture": True,
        "enable_pbr": True,
        "texture_resolution": "2k",
        "should_remesh": True,
        "topology": "triangle",
        "target_polycount": polycount,
        "target_formats": ["fbx", "glb"],
        "auto_size": True,
        "origin_at": "bottom",
    }


def wait_for_task(task_id: str, call=call_api, sleep=time.sleep, timeout: int = POLL_TIMEOUT_SECONDS) -> dict:
    waited = 0
    while True:
        task = call("GET", f"multi-image-to-3d/{task_id}")
        if task["status"] in ("SUCCEEDED", "FAILED", "CANCELED"):
            return task
        if waited >= timeout:
            raise SystemExit(f"Timeout after {waited} s. Task {task_id} is {task['status']}.")
        sleep(POLL_SECONDS)
        waited += POLL_SECONDS


def download_results(task: dict, out: Path, fetch=download) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for fmt, url in task.get("model_urls", {}).items():
        if fmt in ("fbx", "glb"):
            target = out / f"model.{fmt}"
            fetch(url, target)
            written.append(target)
    for index, maps in enumerate(task.get("texture_urls", [])):
        for name, url in maps.items():
            target = out / f"tex{index}_{name}.png"
            fetch(url, target)
            written.append(target)
    return written


def run_multi(images: list[Path], out: Path, polycount: int, model: str,
              call=call_api, fetch=download, sleep=time.sleep, log_file: Path = LOG_FILE) -> dict:
    check_caps(MULTI_IMAGE_TEXTURED_COST, log_file)
    payload = build_payload([image_data_uri(path) for path in images], polycount, model)
    task_id = call("POST", "multi-image-to-3d", payload)["result"]
    task = wait_for_task(task_id, call, sleep)
    credits = int(task.get("consumed_credits", 0))
    files = download_results(task, out, fetch) if task["status"] == "SUCCEEDED" else []
    log_call({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "task": task_id, "kind": "multi-image-to-3d",
              "model": model, "polycount": polycount, "images": [str(p) for p in images],
              "status": task["status"], "credits": credits, "outputs": [str(p) for p in files]}, log_file)
    if task["status"] != "SUCCEEDED":
        raise SystemExit(f"Task {task_id} ended {task['status']}: {task.get('task_error')}")
    return task


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("balance")
    multi = sub.add_parser("multi")
    multi.add_argument("--image", type=Path, action="append", required=True)
    multi.add_argument("--out", type=Path, required=True)
    multi.add_argument("--polycount", type=int, default=2000)
    multi.add_argument("--model", default="meshy-6")
    args = parser.parse_args()
    if args.command == "balance":
        print(json.dumps(call_api("GET", "balance")))
        return
    task = run_multi(args.image, args.out, args.polycount, args.model)
    print(f"task {task['id']} credits {task.get('consumed_credits')}")


if __name__ == "__main__":
    main()
