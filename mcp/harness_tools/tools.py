"""Tool functions for the harness MCP server. Plain Python, no MCP import, so tests are simple.

Every function takes `runs_root` (the runs/ folder) and `repo_root`.
Rules that hold for all of them:
- Run ids and names pass a strict pattern. No path part can get through.
- Every path is resolved and checked to be inside `runs_root`.
- Text from logs is returned as a JSON string field. It is data. Nothing here runs it.
- A result serializes to less than MAX_RESULT_BYTES. A cut is marked.
- Nothing writes outside `runs_root`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

import psutil

from runlib import game, gameslots
from runlib.runfolder import DEFAULT_MAX_RUNS, default_max_runs, new_run_id, run_lock_name

MAX_RESULT_BYTES = 20_000
MAX_TEXT_CHARS = 15_000  # leaves room for the JSON frame around one text field
MAX_WAIT_S = 50  # a client may time out on a long MCP call, so one wait stays short
POLL_STEP_S = 0.5
READ_WINDOW_BYTES = 200_000  # a huge log is never read whole
MAX_SCREENSHOTS = 200
TRUNCATED_MARKER = "[... cut: older text removed ...]"

NAME_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,64}")
# Names the agent may read. Each is a file in the run folder, except launcher.log.
LOG_NAMES = ("mod.log", "UE4SS.log", "boot.json", "scenario.log", "scenario.json", "launcher.log", "config.json")

LauncherCommand = Callable[[str, str, Path], list[str]]  # (scenario, run_id, runs_root) -> argv


class ToolError(ValueError):
    """The request is not valid. The message tells the agent what to fix."""


def failure(message: str, **extra) -> dict:
    return {"ok": False, "error": message, **extra}


def run_tool(function: Callable[[], dict]) -> dict:
    """Turn a ToolError into an error result and cap the size of any result."""
    try:
        return cap_result(function())
    except ToolError as error:
        return failure(str(error))


# --- validation and paths ---------------------------------------------------------------------

def check_name(value: str, what: str) -> str:
    if not isinstance(value, str) or not NAME_PATTERN.fullmatch(value):
        raise ToolError(f"Invalid {what} {value!r}. Use 1 to 64 letters, digits, '_' or '-'. No paths.")
    return value


def inside(runs_root: Path, path: Path) -> Path:
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(Path(runs_root).resolve()):
        raise ToolError(f"Path {path} is outside the runs folder.")
    return resolved


def launcher_log_path(runs_root: Path, run_id: str) -> Path:
    # The run folder does not exist yet when the launcher starts, so its log sits beside it.
    check_name(run_id, "run id")
    return inside(runs_root, Path(runs_root) / f".launcher-{run_id}.log")


def run_folder_of(runs_root: Path, run_id: str) -> Path:
    check_name(run_id, "run id")
    return inside(runs_root, Path(runs_root) / run_id)


def existing_run_folder(runs_root: Path, run_id: str) -> Path:
    folder = run_folder_of(runs_root, run_id)
    if not folder.is_dir():
        raise ToolError(f"Run {run_id!r} not found. Use list_runs to see run ids.")
    return folder


def list_run_folders(runs_root: Path) -> list[Path]:
    """Run folders, newest first."""
    runs_root = Path(runs_root)
    if not runs_root.is_dir():
        return []
    folders = [p for p in runs_root.iterdir() if p.is_dir() and NAME_PATTERN.fullmatch(p.name)]
    return sorted(folders, key=lambda p: (p.stat().st_mtime, p.name), reverse=True)


def resolve_run_id(runs_root: Path, run_id: str) -> str:
    if run_id != "latest":
        return check_name(run_id, "run id")
    folders = list_run_folders(runs_root)
    if not folders:
        raise ToolError("There are no runs yet.")
    return folders[0].name


# --- size limits and file reading -------------------------------------------------------------

def cap_result(result: dict) -> dict:
    text = json.dumps(result)
    if len(text.encode("utf-8")) <= MAX_RESULT_BYTES:
        return result
    return {
        "ok": result.get("ok", True),
        "truncated": True,
        "note": f"Result was over {MAX_RESULT_BYTES} bytes. Only the start is kept.",
        "partial_json": text[:MAX_TEXT_CHARS],
    }


def cut_from_start(text: str, limit: int = MAX_TEXT_CHARS) -> tuple[str, bool]:
    """Keep the end of the text, because the newest lines matter most."""
    if len(text) <= limit:
        return text, False
    return TRUNCATED_MARKER + "\n" + text[-limit:], True


def read_tail_lines(path: Path, lines: int) -> tuple[list[str], bool]:
    """Return the last `lines` lines. The bool is True if the file or the window was cut."""
    size = path.stat().st_size
    with path.open("rb") as handle:
        handle.seek(max(0, size - READ_WINDOW_BYTES))
        raw = handle.read()
    all_lines = raw.decode("utf-8", errors="replace").splitlines()
    return all_lines[-lines:], size > READ_WINDOW_BYTES or len(all_lines) > lines


def read_json_file(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


# --- lock and game state ----------------------------------------------------------------------

def lock_holder_pid(runs_root: Path, slot: int = 0) -> int | None:
    """PID of a live process that holds the run lock of `slot` (runs/.lock or runs/.lock-<n>), or None. Read only."""
    try:
        pid = int((Path(runs_root) / run_lock_name(slot)).read_text().strip())
    except (FileNotFoundError, ValueError):
        return None
    return pid if psutil.pid_exists(pid) else None


# --- start claim ------------------------------------------------------------------------------
# run.py takes runs/.lock only after it has started. The claim closes that gap, so two quick
# run_scenario calls cannot both start a launcher. run.py does not release the claim.
# A claim is released by its launcher process ending: a dead launcher means a stale claim.

CLAIM_NAME = ".active-launcher.json"
CLAIM_GRACE_S = 10  # time a claim counts as live while the launcher pid is not known yet


def claim_path(runs_root: Path, slot: int = 0) -> Path:
    """One start claim per game slot (spec 11). Slot 0 keeps the old name."""
    return Path(runs_root) / (CLAIM_NAME if slot == 0 else f".active-launcher-{slot}.json")


def claim_is_live(path: Path, claim: dict | None) -> bool:
    if claim is None:  # unreadable: the writer may be half way through, so judge by file age
        try:
            return time.time() - path.stat().st_mtime < CLAIM_GRACE_S
        except FileNotFoundError:
            return False
    if claim.get("launcher_known"):
        return psutil.pid_exists(int(claim["pid"]))
    return time.time() - float(claim.get("started", 0)) < CLAIM_GRACE_S


def active_claim(runs_root: Path, slot: int = 0) -> dict | None:
    """The live claim of `slot`, or None. Read only: a stale claim is not removed."""
    path = claim_path(runs_root, slot)
    claim = read_json_file(path)
    if path.exists() and claim_is_live(path, claim):
        return claim or {"run_id": None}
    return None


def write_claim(path: Path, claim: dict) -> None:
    """Replace the claim file in one step, so a reader never sees a half-written file."""
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(claim), encoding="utf-8")
    os.replace(temp, path)


def try_create_claim(path: Path, run_id: str) -> bool:
    claim = {"run_id": run_id, "pid": os.getpid(), "started": time.time(), "launcher_known": False}
    try:
        with path.open("x", encoding="utf-8") as handle:  # mode 'x' fails if the file exists: the atomic step
            json.dump(claim, handle)
    except FileExistsError:
        return False
    return True


def claim_start_slot(runs_root: Path, run_id: str, slot: int = 0) -> Path:
    """Take the start claim of a game slot or raise ToolError that names the active run."""
    path = claim_path(runs_root, slot)
    for _ in range(2):
        if try_create_claim(path, run_id):
            return path
        claim = read_json_file(path)
        if claim_is_live(path, claim):
            active = (claim or {}).get("run_id") or "unknown"
            raise ToolError(f"A launcher is already starting or running in slot {slot} (run {active}). "
                            f"Use wait_for_run with run_id {active}, or start in another slot (slot='auto').")
        path.unlink(missing_ok=True)  # stale: its launcher is gone
    raise ToolError("Could not take the start slot. Another call took it first. Try again.")


def release_claim(path: Path) -> None:
    path.unlink(missing_ok=True)


def read_iteration_state(runs_root: Path) -> dict:
    try:
        used = int((Path(runs_root) / ".iterations").read_text().strip())
    except (FileNotFoundError, ValueError):
        used = 0
    folders = list_run_folders(runs_root)
    config = read_json_file(folders[0] / "config.json") if folders else None
    # A config.json of a run overrides the default. Else the same default as run.py (HARNESS_MAX_RUNS or 400).
    try:
        fallback = default_max_runs()
    except ValueError:
        fallback = DEFAULT_MAX_RUNS
    max_runs = (config or {}).get("max_runs", fallback)
    return {"runs_used": used, "max_runs": max_runs, "runs_left": max(0, max_runs - used)}


def slot_status(runs_root: Path, slot: gameslots.GameSlot) -> dict:
    return {
        "slot": slot.number,
        "game_pids": [p.pid for p in game.find_game_processes(slot.root)],
        "lock_holder_pid": lock_holder_pid(runs_root, slot.number),
        "active_run_id": (active_claim(runs_root, slot.number) or {}).get("run_id"),
    }


def any_slot_locked(runs_root: Path) -> bool:
    return any(lock_holder_pid(runs_root, slot.number) is not None for slot in gameslots.installed_slots())


def game_status(runs_root: Path, repo_root: Path) -> dict:
    def build() -> dict:
        pids = [p.pid for p in game.find_game_processes()]
        slots = [slot_status(runs_root, slot) for slot in gameslots.installed_slots()]
        return {
            "ok": True,
            "game_running": bool(pids),
            "game_pids": pids,
            "lock_holder_pid": lock_holder_pid(runs_root),
            "active_run_id": (active_claim(runs_root) or {}).get("run_id"),
            "slots": slots,
            "free_slots": [s["slot"] for s in slots if s["lock_holder_pid"] is None and s["active_run_id"] is None],
            **read_iteration_state(runs_root),
        }

    return run_tool(build)


def stop_game(runs_root: Path, repo_root: Path, slot: int = 0) -> dict:
    def build() -> dict:
        game_slot = gameslots.get_slot(slot)
        holder = lock_holder_pid(runs_root, slot)
        if holder is not None:
            raise ToolError(f"A run holds the lock of slot {slot} (process {holder}). Stopping the game now would break it.")
        claim = active_claim(runs_root, slot)
        if claim is not None:
            raise ToolError(f"A launcher is active in slot {slot} (run {claim.get('run_id')}). Stopping the game now would break it.")
        processes = game.find_game_processes(game_slot.root)
        pids = [p.pid for p in processes]
        if not processes:
            return {"ok": True, "stopped_pids": [], "note": "No game process was running."}
        game.stop_processes(processes)
        return {"ok": True, "stopped_pids": pids}

    try:
        return run_tool(build)
    except RuntimeError as error:  # stop_processes: a process stayed alive
        return failure(str(error))


# --- scenarios and runs -----------------------------------------------------------------------

def load_scenarios() -> dict[str, str]:
    """Registered scenarios: name -> description. Empty if the registry is missing.

    Hidden scenarios (self tests that fail, crash or time out on purpose, and probes) are left out,
    so an agent cannot start them by mistake.
    """
    try:
        from runlib.scenario import list_scenarios as registry
    except ImportError:
        return {}
    return {name: info.summary or "(no description)" for name, info in registry(include_hidden=False).items()}


def list_scenarios(runs_root: Path, repo_root: Path) -> dict:
    def build() -> dict:
        scenarios = load_scenarios()
        return {"ok": True, "scenarios": [{"name": n, "description": d} for n, d in scenarios.items()]}

    return run_tool(build)


def default_launcher_command(repo_root: Path) -> LauncherCommand:
    def command(scenario: str, run_id: str, runs_root: Path) -> list[str]:
        return [
            sys.executable,
            str(Path(repo_root) / "harness" / "run.py"),
            "--scenario", scenario,
            "--run-id", run_id,
            "--runs-root", str(runs_root),
        ]

    return command


def spawn_detached(argv: list[str], log_path: Path) -> int:
    """Start a process that outlives this call and has no console window. Return its PID."""
    options: dict = {}
    if os.name == "nt":
        # A new process group keeps Ctrl+C of the server away from the run.
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    else:
        options["start_new_session"] = True
    with log_path.open("wb") as log:
        process = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, close_fds=True, **options
        )
    return process.pid


def run_scenario(
    runs_root: Path,
    repo_root: Path,
    name: str,
    launcher_command: LauncherCommand | None = None,
    slot: str = "0",
) -> dict:
    def build() -> dict:
        check_name(name, "scenario name")
        known = load_scenarios()
        if name not in known:
            raise ToolError(f"Unknown scenario {name!r}. Known scenarios: {sorted(known)}.")
        Path(runs_root).mkdir(parents=True, exist_ok=True)
        run_id = new_run_id()
        make_argv = launcher_command or default_launcher_command(repo_root)
        number, claim = claim_game_slot(runs_root, run_id, slot)
        try:
            argv = make_argv(name, run_id, Path(runs_root)) + ["--slot", str(number)]
            pid = spawn_detached(argv, launcher_log_path(runs_root, run_id))
        except BaseException:
            release_claim(claim)
            raise
        write_claim(claim, {"run_id": run_id, "pid": pid, "started": time.time(), "launcher_known": True})
        return {"ok": True, "status": "started", "run_id": run_id, "launcher_pid": pid, "slot": number,
                "next": "Call wait_for_run with this run_id."}

    return run_tool(build)


def claim_game_slot(runs_root: Path, run_id: str, slot: str) -> tuple[int, Path]:
    """Claim the asked slot ("0" to "3"), or with "auto" the first installed slot without a run. Raise ToolError if none is free."""
    if slot != "auto" and not slot.isdigit():
        raise ToolError(f"slot must be a number 0 to {gameslots.MAX_SLOT} or 'auto', not {slot!r}")
    try:
        candidates = gameslots.installed_slots() if slot == "auto" else [gameslots.get_slot(int(slot))]
    except gameslots.SlotError as error:
        raise ToolError(str(error)) from error
    for candidate in candidates:
        holder = lock_holder_pid(runs_root, candidate.number)
        if holder is not None:
            if slot != "auto":
                raise ToolError(f"A run is active in slot {candidate.number} (process {holder} holds the lock). "
                                "Use wait_for_run on it, or start with slot='auto'.")
            continue
        try:
            return candidate.number, claim_start_slot(runs_root, run_id, candidate.number)
        except ToolError:
            if slot != "auto":
                raise
    raise ToolError(f"All {len(candidates)} game slots are busy. Wait for a run to end (wait_for_run), then try again.")


def guess_phase(folder: Path) -> str | None:
    """A hint from the files that exist. The launcher writes no live phase file."""
    if not folder.is_dir():
        return None
    if (folder / "scenario.json").exists():
        return "collect"
    if read_json_file(folder / "boot.json") is not None:
        return "scenario" if (folder / "ready.marker").exists() else "boot"
    return "launch" if (folder / "config.json").exists() else "preflight"


def running_result(runs_root: Path, run_id: str, started: float) -> dict:
    folder = run_folder_of(runs_root, run_id)
    log = launcher_log_path(runs_root, run_id)
    if not folder.is_dir() and log.is_file() and log.stat().st_size > 0 and not any_slot_locked(runs_root):
        # The launcher printed something and made no run folder: it refused or crashed.
        text, _ = cut_from_start(log.read_text(encoding="utf-8", errors="replace"))
        return {"ok": False, "status": "failed_to_start", "run_id": run_id, "launcher_log": text}
    result = {"ok": True, "status": "running", "run_id": run_id, "phase": guess_phase(folder),
              "elapsed_s": round(time.monotonic() - started, 1)}
    limit = scenario_limit_s(folder)
    if limit:
        # A long scenario (a soak) runs up to this long. The agent keeps calling wait_for_run until the summary appears.
        result["scenario_limit_s"] = limit
    return result


def scenario_limit_s(folder: Path) -> float | None:
    config = read_json_file(folder / "config.json") or {}
    limit = (config.get("limits_s") or {}).get("scenario")
    return limit if isinstance(limit, (int, float)) and not isinstance(limit, bool) else None


def wait_for_run(runs_root: Path, repo_root: Path, run_id: str, seconds: int = 45) -> dict:
    def build() -> dict:
        folder = run_folder_of(runs_root, run_id)
        started = time.monotonic()
        deadline = started + clamp(seconds, 0, MAX_WAIT_S)
        while True:
            summary = read_json_file(folder / "summary.json")
            if summary is not None:
                return {"ok": True, "status": "done", "summary": summary}
            if time.monotonic() >= deadline:
                return running_result(runs_root, run_id, started)
            time.sleep(POLL_STEP_S)

    return run_tool(build)


def read_summary(runs_root: Path, repo_root: Path, run_id: str = "latest") -> dict:
    def build() -> dict:
        resolved = resolve_run_id(runs_root, run_id)
        summary = read_json_file(existing_run_folder(runs_root, resolved) / "summary.json")
        if summary is None:
            return {"ok": True, "run_id": resolved, "status": "no_summary",
                    "note": "The run has no summary.json yet. It may still run. Use wait_for_run."}
        return {"ok": True, "run_id": resolved, "summary": summary}

    return run_tool(build)


def summarize_run(folder: Path) -> dict:
    summary = read_json_file(folder / "summary.json")
    if summary is None:
        return {"run_id": folder.name, "verdict": None, "status": "no_summary"}
    return {"run_id": folder.name, "verdict": summary.get("verdict"), "scenario": summary.get("scenario"),
            "duration_s": summary.get("duration_s"), "started": summary.get("started")}


def list_runs(runs_root: Path, repo_root: Path, limit: int = 10) -> dict:
    def build() -> dict:
        folders = list_run_folders(runs_root)[: clamp(limit, 1, 50)]
        return {"ok": True, "runs": [summarize_run(f) for f in folders]}

    return run_tool(build)


def log_path_of(runs_root: Path, run_id: str, name: str) -> Path:
    if name not in LOG_NAMES:
        raise ToolError(f"Unknown log name {name!r}. Allowed: {list(LOG_NAMES)}.")
    if name == "launcher.log":
        return launcher_log_path(runs_root, run_id)
    return inside(runs_root, existing_run_folder(runs_root, run_id) / name)


def text_result(path: Path, extra: dict, lines: int, label: str) -> dict:
    if not path.is_file():
        return {"ok": False, **extra, "error": f"{label} is not available for this run."}
    tail_lines, cut = read_tail_lines(path, lines)
    text, text_cut = cut_from_start("\n".join(tail_lines))
    return {"ok": True, **extra, "truncated": cut or text_cut, "text": text}


def read_log(runs_root: Path, repo_root: Path, run_id: str, name: str, tail: int = 100) -> dict:
    def build() -> dict:
        resolved = resolve_run_id(runs_root, run_id)
        path = log_path_of(runs_root, resolved, name)
        return text_result(path, {"run_id": resolved, "name": name}, clamp(tail, 1, 1000), name)

    return run_tool(build)


def read_telemetry(runs_root: Path, repo_root: Path, run_id: str, last: int = 20) -> dict:
    def build() -> dict:
        resolved = resolve_run_id(runs_root, run_id)
        path = inside(runs_root, existing_run_folder(runs_root, resolved) / "telemetry.jsonl")
        return text_result(path, {"run_id": resolved}, clamp(last, 1, 200), "telemetry.jsonl")

    return run_tool(build)


def list_screenshots(runs_root: Path, repo_root: Path, run_id: str) -> dict:
    def build() -> dict:
        resolved = resolve_run_id(runs_root, run_id)
        folder = existing_run_folder(runs_root, resolved)
        shots_dir = inside(runs_root, folder / "screenshots")
        files = sorted(p for p in shots_dir.rglob("*") if p.is_file()) if shots_dir.is_dir() else []
        return {"ok": True, "run_id": resolved, "run_folder": str(folder),
                "screenshots": [p.relative_to(shots_dir.parent).as_posix() for p in files[:MAX_SCREENSHOTS]],
                "truncated": len(files) > MAX_SCREENSHOTS}

    return run_tool(build)
