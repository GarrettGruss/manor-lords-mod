"""Generate images with the Gemini API for mod art (UI icons, panels, textures).

Usage:
  uv run python harness/tools/genimage.py --list-models
  uv run python harness/tools/genimage.py --prompt "..." --out mod/<Name>/art/icon.png [--model NAME] [--count N]

The API key comes from the environment variable GEMINI_API_KEY. On Windows the
tool also reads the user-scope value from the registry, because a shell started
before the key was set does not see it. The key is never printed or written.

Every call is appended to runs/genimage/log.jsonl (prompt, model, output, size),
so the spend can be checked. MAX_IMAGES_PER_CALL caps one call.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-3.1-flash-image"
MAX_IMAGES_PER_CALL = 4
REPO = Path(__file__).resolve().parents[2]
LOG_FILE = REPO / "runs" / "genimage" / "log.jsonl"


def api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key and sys.platform == "win32":
        key = _user_scope_key()
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set (environment or Windows user scope).")
    return key


def _user_scope_key() -> str:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env:
            value, _ = winreg.QueryValueEx(env, "GEMINI_API_KEY")
            return str(value).strip()
    except OSError:
        return ""


def call_api(method: str, path: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(
        f"{API_ROOT}/{path}",
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        method=method,
        headers={"x-goog-api-key": api_key(), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:800]
        raise SystemExit(f"Gemini API error {error.code}: {detail}") from None


def list_image_models() -> list[str]:
    names = []
    page = ""
    while True:
        answer = call_api("GET", "models?pageSize=200" + (f"&pageToken={page}" if page else ""))
        for model in answer.get("models", []):
            name = model["name"].removeprefix("models/")
            if "image" in name or "imagen" in name:
                names.append(f"{name}  methods={','.join(model.get('supportedGenerationMethods', []))}")
        page = answer.get("nextPageToken", "")
        if not page:
            return names


def generate_with_gemini(model: str, prompt: str) -> list[bytes]:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }
    answer = call_api("POST", f"models/{model}:generateContent", body)
    images = []
    for candidate in answer.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                images.append(base64.b64decode(inline["data"]))
    if not images:
        raise SystemExit(f"No image in the answer: {json.dumps(answer)[:800]}")
    return images


def generate_with_imagen(model: str, prompt: str, count: int) -> list[bytes]:
    body = {"instances": [{"prompt": prompt}], "parameters": {"sampleCount": count}}
    answer = call_api("POST", f"models/{model}:predict", body)
    images = [base64.b64decode(p["bytesBase64Encoded"]) for p in answer.get("predictions", []) if p.get("bytesBase64Encoded")]
    if not images:
        raise SystemExit(f"No image in the answer: {json.dumps(answer)[:800]}")
    return images


def output_paths(out: Path, count: int) -> list[Path]:
    if count == 1:
        return [out]
    return [out.with_name(f"{out.stem}_{index + 1}{out.suffix}") for index in range(count)]


def log_call(entry: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry) + "\n")


def generate(model: str, prompt: str, out: Path, count: int) -> list[Path]:
    if not 1 <= count <= MAX_IMAGES_PER_CALL:
        raise SystemExit(f"--count must be 1..{MAX_IMAGES_PER_CALL}")
    if model.startswith("imagen"):
        images = generate_with_imagen(model, prompt, count)
    else:
        images = [image for _ in range(count) for image in generate_with_gemini(model, prompt)][:count]
    out.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for path, data in zip(output_paths(out, len(images)), images):
        path.write_bytes(data)
        written.append(path)
    log_call({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": model, "prompt": prompt,
              "outputs": [str(p) for p in written], "bytes": [p.stat().st_size for p in written]})
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list-models", action="store_true", help="list the image models this key can use")
    parser.add_argument("--prompt")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--count", type=int, default=1)
    args = parser.parse_args()
    if args.list_models:
        print("\n".join(list_image_models()))
        return
    if not args.prompt or not args.out:
        parser.error("--prompt and --out are needed")
    for path in generate(args.model, args.prompt, args.out, args.count):
        print(f"wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
