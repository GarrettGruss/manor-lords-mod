"""Deploy the mods and reload the changed ones in the running game, without a game restart (spec 06, part A).

    .venv\\Scripts\\python.exe harness\\tools\\reload_mods.py [--mod Name ...] [--run-dir DIR] [--no-deploy]

Steps: deploy.ps1, then for each mod a request file `reload.json` in the run folder of the game.
The Lua mod `HarnessReload` calls RestartMod and writes `reload.result.json` with the version line of the new code.
This tool compares that version with `local VERSION = "..."` in the repository file of the mod.
Exit code: 0 all mods reloaded, 1 a reload failed, 2 harness error (no game, no deploy, bad arguments).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "harness"))

REQUEST_NAME = "reload.json"
RESULT_NAME = "reload.result.json"
SELF_MOD = "HarnessReload"
# Restarting HarnessBoot in a running game would load the save again, so it needs an explicit --mod.
NOT_BY_DEFAULT = {SELF_MOD, "HarnessBoot"}
DEPLOY_TIMEOUT_S = 110
RESULT_TIMEOUT_S = 40
POLL_S = 0.2
VERSION_LINE = re.compile(r'^\s*local\s+VERSION\s*=\s*"([^"]+)"', re.MULTILINE)
COPIED_LINE = re.compile(r"^copied\s+(\S+)", re.MULTILINE)
MOD_NAME = re.compile(r"^[A-Za-z0-9_]+$")


class ReloadError(RuntimeError):
    """A harness error: the reload could not be tried (exit code 2)."""


def repo_mod_names(mod_dir: Path) -> list[str]:
    return sorted(p.name for p in mod_dir.iterdir() if p.is_dir() and p.name != "shared")


def read_repo_version(mod_dir: Path, mod: str) -> str | None:
    """The version the repository file will report, or None when the mod has no VERSION line."""
    for script_dir in ("Scripts", "scripts"):
        script = mod_dir / mod / script_dir / "main.lua"
        if script.is_file():
            match = VERSION_LINE.search(script.read_text(encoding="utf-8"))
            return match.group(1) if match else None
    return None


def parse_copied_files(deploy_output: str) -> list[str]:
    return COPIED_LINE.findall(deploy_output)


def mods_that_use_shared(mod_dir: Path, shared_name: str) -> list[str]:
    """Mods whose Lua files call require("<shared_name>"). A changed shared module needs these restarted."""
    pattern = re.compile(r'require\s*\(?\s*["\']' + re.escape(shared_name) + r'["\']')
    found = []
    for mod in repo_mod_names(mod_dir):
        files = (mod_dir / mod).rglob("*.lua")
        if any(pattern.search(path.read_text(encoding="utf-8", errors="replace")) for path in files):
            found.append(mod)
    return found


def mods_to_reload(copied: list[str], mod_dir: Path) -> tuple[list[str], list[str]]:
    """Return (mods to restart, notes) for the files deploy.ps1 copied."""
    notes: list[str] = []
    wanted: list[str] = []
    for relative in copied:
        top, _, rest = relative.replace("/", "\\").partition("\\")
        if top == "shared":
            shared_name = rest.split("\\")[0]
            users = mods_that_use_shared(mod_dir, shared_name)
            notes.append(f"shared module {shared_name} changed: restart {users or 'no mod'}")
            wanted.extend(users)
        else:
            wanted.append(top)
    unique = list(dict.fromkeys(wanted))
    skipped = [mod for mod in unique if mod in NOT_BY_DEFAULT]
    for mod in skipped:
        notes.append(f"{mod} is not restarted by default. Use --mod {mod} (HarnessReload: restart the game)")
    return [mod for mod in unique if mod not in NOT_BY_DEFAULT], notes


def write_request(run_dir: Path, mod: str, request_id: str) -> None:
    """Write reload.json atomically. A stale result file is removed first, so the next one is ours."""
    (run_dir / RESULT_NAME).unlink(missing_ok=True)
    tmp = run_dir / (REQUEST_NAME + ".tmp")
    tmp.write_text(json.dumps({"mod": mod, "id": request_id}), encoding="utf-8")
    os.replace(tmp, run_dir / REQUEST_NAME)


def read_result(run_dir: Path, request_id: str) -> dict | None:
    try:
        data = json.loads((run_dir / RESULT_NAME).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) and data.get("id") == request_id else None


def reload_one(run_dir: Path, mod: str, expected_version: str | None, timeout_s: float = RESULT_TIMEOUT_S,
               sleep=time.sleep, clock=time.monotonic) -> dict:
    """Ask HarnessReload to restart `mod` and wait for the result. Never raises for a failed reload."""
    request_id = uuid.uuid4().hex[:12]
    started = clock()
    write_request(run_dir, mod, request_id)
    while clock() - started < timeout_s:
        result = read_result(run_dir, request_id)
        if result is not None:
            return judge(mod, expected_version, result, clock() - started)
        sleep(POLL_S)
    return {"mod": mod, "ok": False, "seconds": round(clock() - started, 1),
            "error": f"no answer from HarnessReload in {timeout_s:g} s. Is the mod loaded? Is the game paused in a pop-up?"}


def judge(mod: str, expected: str | None, result: dict, seconds: float) -> dict:
    report = {"mod": mod, "ok": bool(result.get("ok")), "version": result.get("version"), "expected": expected,
              "seconds": round(seconds, 1)}
    if not result.get("ok"):
        report["error"] = result.get("error")
    elif expected is not None and result.get("version") != expected:
        report["ok"] = False
        report["error"] = f"the game runs version {result.get('version')}, the repository has {expected}"
    return report


def run_deploy(game_dir: str | None) -> str:
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(REPO_ROOT / "harness" / "deploy.ps1"), "-NoPak"]
    if game_dir:
        command += ["-GameDir", game_dir]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=DEPLOY_TIMEOUT_S)
    except subprocess.TimeoutExpired as error:
        raise ReloadError(f"deploy.ps1 did not end in {DEPLOY_TIMEOUT_S} s") from error
    if result.returncode != 0 or not re.search(r"errors:\s*0\b", result.stdout):
        raise ReloadError(f"deploy.ps1 failed (exit {result.returncode}): {(result.stdout + result.stderr)[-300:]}")
    return result.stdout


def find_run_dir() -> Path:
    """The HARNESS_RUN_DIR of the running game process."""
    from runlib.game import find_game_processes

    for process in find_game_processes():
        try:
            value = process.environ().get("HARNESS_RUN_DIR")
        except Exception:  # access denied or process gone: try the next one
            continue
        if value:
            return Path(value)
    raise ReloadError("no running game with HARNESS_RUN_DIR found. Start the game with the launcher, or pass --run-dir.")


def check_args(mods: list[str], mod_dir: Path) -> None:
    for mod in mods:
        if not MOD_NAME.match(mod):
            raise ReloadError(f"bad mod name: {mod!r}")
        if mod not in repo_mod_names(mod_dir):
            raise ReloadError(f"no folder mod/{mod} in the repository")


def reload_mods(mods: list[str], run_dir: Path, mod_dir: Path = REPO_ROOT / "mod", timeout_s: float = RESULT_TIMEOUT_S) -> list[dict]:
    if not (run_dir / "mod.log").is_file():
        raise ReloadError(f"{run_dir} has no mod.log: it is not the run folder of a running game")
    return [reload_one(run_dir, mod, read_repo_version(mod_dir, mod), timeout_s) for mod in mods]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy the mods and reload the changed ones in the running game.")
    parser.add_argument("--mod", action="append", default=[], help="mod to restart (repeatable). Default: the mods that deploy changed")
    parser.add_argument("--run-dir", type=Path, help="run folder of the game (default: read from the game process)")
    parser.add_argument("--no-deploy", action="store_true", help="do not run deploy.ps1 first")
    parser.add_argument("--game-dir", help="game install folder for deploy.ps1")
    parser.add_argument("--timeout", type=float, default=RESULT_TIMEOUT_S, help="seconds to wait for each mod (default %(default)s)")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    started = time.monotonic()
    mod_dir = REPO_ROOT / "mod"
    try:
        check_args(args.mod, mod_dir)
        run_dir = args.run_dir or find_run_dir()
        notes: list[str] = []
        mods = list(args.mod)
        if not args.no_deploy:
            copied = parse_copied_files(run_deploy(args.game_dir))
            if not mods:
                mods, notes = mods_to_reload(copied, mod_dir)
        elif not mods:
            raise ReloadError("--no-deploy needs --mod")
        results = reload_mods(mods, run_dir, mod_dir, args.timeout)
    except ReloadError as error:
        print(f"harness_error: {error}", file=sys.stderr)
        return 2
    report = {"ok": all(r["ok"] for r in results), "seconds": round(time.monotonic() - started, 1),
              "mods": results, "notes": notes}
    if not mods:
        report["notes"].append("deploy changed no mod: nothing to reload")
    print(json.dumps(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
