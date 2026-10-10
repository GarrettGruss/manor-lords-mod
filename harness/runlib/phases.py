"""The real phases: preflight, deploy, launch, boot, scenario, collect and teardown.

`build_real_phases` returns them in order. Each phase is a small function over the PhaseContext.
"""

from __future__ import annotations

import dataclasses
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import fixtures
from .actions import ActionNotPossible
from .environment import gather_environment, hash_mods
from .game import (
    DEFAULT_TELEMETRY_INTERVAL_S,
    DEFAULT_TEST_SAVE,
    GameInstall,
    build_game_environment,
    count_pause_calls,
    ensure_game_alive,
    find_game_processes,
    is_steam_running,
    read_boot_file,
    sleep_until,
    stop_processes,
)
from .runfolder import atomic_write_text, write_config
from .runner import Phase, PhaseContext, PhaseFailed
from .scenario import REPO_ROOT, configure_bridge_client, get_limit_s, get_scenario
from .scenario_context import ScenarioContext
from .screenshot import capture_game_window

BOOT_POLL_S = 1.0
BOOT_DEADLINE_S = 230  # a little under the phase limit, so the message says what happened
LAUNCH_ALIVE_CHECK_S = 3
DEPLOY_TIMEOUT_S = 110
MAX_CRASH_DIR_BYTES = 50 * 1024 * 1024
DEPLOY_SUMMARY = re.compile(r"Summary:.*errors:\s*(\d+)")


# ---- preflight ----

def _stop_stale_game(ctx: PhaseContext) -> None:
    stale = find_game_processes()
    if not stale:
        return
    stop_processes(stale)
    for process in stale:
        ctx.state["notes"].append(f"stale game process PID {process.pid} was stopped")


def _appdata_dir(ctx: PhaseContext) -> Path:
    return ctx.run.path / fixtures.APPDATA_NAME


def _private_install(install: GameInstall, ctx: PhaseContext) -> GameInstall:
    """The install as the game sees it in this run: its saves, config and crash reports are in the run's appdata."""
    return dataclasses.replace(install, saved_dir=fixtures.saved_dir_of(_appdata_dir(ctx)))


def _prepare_appdata(install: GameInstall, ctx: PhaseContext, fixture: str) -> None:
    """Build the private LOCALAPPDATA. Remember the user's save files, so teardown can compare."""
    ctx.state["appdata_dir"] = _appdata_dir(ctx)  # set first: teardown removes the folder even if the copy fails half way
    try:
        result = fixtures.prepare_appdata(install.saved_dir, _appdata_dir(ctx), fixtures.load_manifest(), fixture)
    except fixtures.FixtureError as error:
        raise PhaseFailed(f"fixture {fixture}: {error}") from error
    ctx.state["user_saves_snapshot"] = result.user_snapshot
    ctx.config.setdefault("environment", {})["fixture"] = result.as_dict()


def _preflight(install: GameInstall, test_save: str, fixture: str = fixtures.DEFAULT_FIXTURE):
    def run(ctx: PhaseContext) -> str | None:
        ctx.state["run_started_epoch"] = time.time()
        if not is_steam_running():
            raise PhaseFailed("Steam is not running. Start Steam first.")
        venv_python = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            raise PhaseFailed(f"venv not found: {venv_python}")
        if not install.exe.exists():
            raise PhaseFailed(f"game exe not found: {install.exe}")
        _stop_stale_game(ctx)
        _prepare_appdata(install, ctx, fixture)
        private = _private_install(install, ctx)
        if not private.save_file(test_save).is_file():
            raise PhaseFailed(f"test save not found: {private.save_file(test_save)}")
        ctx.config.setdefault("environment", {}).update(
            gather_environment(private, REPO_ROOT, ctx.run.path, test_save)
        )
        write_config(ctx.run, ctx.config)
        return None

    return run


# ---- deploy ----

def _deploy(install: GameInstall):
    def run(ctx: PhaseContext) -> str | None:
        command = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            str(REPO_ROOT / "harness" / "deploy.ps1"), "-GameDir", str(install.root),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=DEPLOY_TIMEOUT_S)
        except subprocess.TimeoutExpired as error:
            raise PhaseFailed(f"deploy.ps1 did not end in {DEPLOY_TIMEOUT_S} s") from error
        if result.returncode != 0:
            tail = (result.stdout + result.stderr).strip()[-300:]
            raise PhaseFailed(f"deploy.ps1 exit code {result.returncode}: {tail}")
        summary_line = next((line for line in result.stdout.splitlines() if "Summary:" in line), None)
        match = DEPLOY_SUMMARY.search(summary_line or "")
        if not match or int(match.group(1)) != 0:
            raise PhaseFailed(f"deploy.ps1 did not report 0 errors: {summary_line}")
        ctx.config["environment"]["mods"] = hash_mods(REPO_ROOT / "mod")
        write_config(ctx.run, ctx.config)
        return summary_line

    return run


# ---- launch ----

def _launch(install: GameInstall, test_save: str, telemetry_interval_s: float):
    def run(ctx: PhaseContext) -> str | None:
        env = build_game_environment(ctx.run.path, test_save, telemetry_interval_s=telemetry_interval_s,
                                     appdata_dir=ctx.state.get("appdata_dir"))
        # The working folder must be Win64, or UE4SS does not find its files.
        popen = subprocess.Popen(
            [str(install.exe)], cwd=install.win64, env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        ctx.state["game_popen"] = popen
        ctx.state["game_pid"] = popen.pid
        ctx.state["launch_monotonic"] = time.monotonic()
        time.sleep(LAUNCH_ALIVE_CHECK_S)
        ensure_game_alive(ctx, "launch")
        return f"game started, PID {popen.pid}"

    return run


# ---- boot ----

def _boot_result(boot_file: dict, seconds: float, pause_calls: int) -> dict:
    return {
        "state": boot_file["state"],
        "seconds": round(seconds, 1),
        "pause_calls": pause_calls,
        "reason": boot_file.get("reason"),
    }


def _boot(ctx: PhaseContext) -> str | None:
    started = ctx.state["launch_monotonic"]
    deadline = time.monotonic() + BOOT_DEADLINE_S
    last_state = "no boot.json yet"
    while time.monotonic() < deadline:
        ensure_game_alive(ctx, "boot")
        boot_file = read_boot_file(ctx.run.boot_path)
        if boot_file:
            last_state = str(boot_file.get("state"))
            seconds = time.monotonic() - started
            if last_state in ("READY", "FAILED"):
                ctx.state["boot"] = _boot_result(boot_file, seconds, count_pause_calls(ctx.run.path / "mod.log"))
            if last_state == "FAILED":
                raise PhaseFailed(f"HarnessBoot FAILED: {boot_file.get('reason')}")
            if last_state == "READY":
                return f"READY after {seconds:.0f} s"
        sleep_until(deadline, BOOT_POLL_S)
    raise PhaseFailed(f"boot did not finish in {BOOT_DEADLINE_S} s. Last state: {last_state}")


# ---- screenshots ----

def take_screenshot(ctx: PhaseContext, name: str) -> str | None:
    """Save screenshots/<name>.png of the game window. A failure adds a note and the run goes on."""
    pids = {process.pid for process in find_game_processes()}
    if ctx.state.get("game_pid"):
        pids.add(ctx.state["game_pid"])
    path = ctx.run.screenshots_dir / f"{name}.png"
    problem = capture_game_window(path, pids)
    if problem:
        ctx.state["notes"].append(f"screenshot {name} failed: {problem}")
        return None
    return path.name


# ---- scenario ----

def _scenario(install: GameInstall, scenario_name: str):
    def run(ctx: PhaseContext) -> str | None:
        scenario = get_scenario(scenario_name)
        bridge = configure_bridge_client(ctx, install)
        scenario_ctx = ScenarioContext(ctx, bridge, screenshot_fn=take_screenshot)
        take_screenshot(ctx, "start")
        try:
            result = scenario(scenario_ctx)
        except ActionNotPossible as error:
            # A real result, not a harness bug: the scenario asked for something the kit cannot do.
            result = scenario_ctx.fail("action is possible", str(error))
        except Exception:
            ensure_game_alive(ctx, "scenario")  # a dead game explains the error: it is a crash
            raise
        ctx.state["scenario_result"] = result
        atomic_write_text(ctx.run.path / "scenario.json", json.dumps(result, indent=2))
        return None

    return run


# ---- collect ----

def _folder_size(folder: Path) -> int:
    return sum(path.stat().st_size for path in folder.rglob("*") if path.is_file())


def copy_ue4ss_log(install: GameInstall, run_path: Path) -> bool:
    if not install.ue4ss_log.is_file():
        return False
    shutil.copy2(install.ue4ss_log, run_path / "UE4SS.log")
    return True


def copy_new_crash_dirs(install: GameInstall, crash_dir: Path, since_epoch: float, notes: list[str]) -> list[str]:
    """Copy crash report folders newer than `since_epoch`. Return their paths relative to the run folder."""
    if not install.crashes_dir.is_dir():
        return []
    copied = []
    for folder in sorted(p for p in install.crashes_dir.iterdir() if p.is_dir()):
        if folder.stat().st_mtime <= since_epoch:
            continue
        if _folder_size(folder) > MAX_CRASH_DIR_BYTES:
            notes.append(f"crash report {folder.name} is over 50 MB and was not copied")
            continue
        shutil.copytree(folder, crash_dir / folder.name)
        copied.append(f"{crash_dir.name}/{folder.name}")
    return copied


def copy_new_dumps(install: GameInstall, crash_dir: Path, since_epoch: float) -> list[str]:
    """Copy UE4SS crash dumps (*.dmp in the ue4ss folder) that are newer than `since_epoch`."""
    ue4ss_dir = install.win64 / "ue4ss"
    if not ue4ss_dir.is_dir():
        return []
    copied = []
    for dump in sorted(ue4ss_dir.glob("*.dmp")):
        if dump.stat().st_mtime > since_epoch:
            shutil.copy2(dump, crash_dir / dump.name)
            copied.append(f"{crash_dir.name}/{dump.name}")
    return copied


def describe_telemetry(run_path: Path) -> str | None:
    """Name and sample count of telemetry.jsonl, or None if the mod wrote none (telemetry off, or a crash)."""
    path = run_path / "telemetry.jsonl"
    if not path.is_file():
        return None
    return f"{path.name} ({len(path.read_text(encoding='utf-8').splitlines())} samples)"


def list_logs(run_path: Path) -> list[str]:
    return sorted(path.name for path in run_path.glob("*.log"))


def _collect(install: GameInstall):
    def run(ctx: PhaseContext) -> str | None:
        # The game is still running here (teardown comes later), so this is the end screenshot.
        # After a crash the game is gone, and the screenshot adds a note.
        take_screenshot(ctx, "end")
        since = ctx.state.get("run_started_epoch", 0.0)
        copy_ue4ss_log(install, ctx.run.path)
        # UE writes crash reports under the LOCALAPPDATA it sees: the run's appdata, when the run used one.
        crash_install = _private_install(install, ctx) if ctx.state.get("appdata_dir") else install
        crash_dirs = copy_new_crash_dirs(crash_install, ctx.run.crash_dir, since, ctx.state["notes"])
        if crash_dirs:
            ctx.state["notes"].append(f"{len(crash_dirs)} new UE crash report(s) were copied")
        dumps = copy_new_dumps(install, ctx.run.crash_dir, since)
        if dumps:
            ctx.state["notes"].append(f"{len(dumps)} new UE4SS crash dump(s) were copied")
        screenshots = sorted(p.relative_to(ctx.run.path).as_posix() for p in ctx.run.screenshots_dir.iterdir())
        ctx.state["artifacts"] = {
            "logs": list_logs(ctx.run.path), "crash": crash_dirs + dumps, "screenshots": screenshots,
            "telemetry": describe_telemetry(ctx.run.path),
        }
        return None

    return run


# ---- teardown ----

def _finish_appdata(install: GameInstall, ctx: PhaseContext) -> str | None:
    """Compare the user's save files with the snapshot of preflight, then delete the run's appdata copy."""
    appdata = ctx.state.get("appdata_dir")
    if not appdata:
        return None
    problems = fixtures.describe_difference(
        ctx.state.get("user_saves_snapshot", {}), fixtures.snapshot_user_files(install.saved_dir / "SaveGames"))
    removed = fixtures.remove_appdata(appdata)
    if problems:
        raise PhaseFailed(f"the user's save files changed during the run: {'; '.join(problems[:10])}")
    ctx.state["notes"].append(f"private appdata removed ({removed} files); the user's save files did not change")
    return f"appdata removed ({removed} files), user saves unchanged"


def _teardown(install: GameInstall, keep_open: bool):
    def run(ctx: PhaseContext) -> str | None:
        # Set first, so the end of the process is not read as a crash.
        ctx.state["game_stop_requested"] = True
        if keep_open:
            ctx.state["notes"].append("--keep-open: the game was left running")
            if ctx.state.get("appdata_dir"):
                ctx.state["notes"].append(f"private appdata is still in place: {ctx.state['appdata_dir']}")
            return "teardown: game left running (--keep-open)"
        running = find_game_processes()
        stop_processes(running)
        remaining = find_game_processes()
        if remaining:
            raise PhaseFailed(f"game process remains after teardown: PID {[p.pid for p in remaining]}")
        # UE4SS.log is buffered, so the copy from collect can be short. Copy again after the game ended.
        if copy_ue4ss_log(install, ctx.run.path):
            ctx.state["artifacts"]["logs"] = list_logs(ctx.run.path)
        pids = [process.pid for process in running]
        stopped = f"teardown: game stopped (PID {pids})" if pids else "teardown: game stopped (none was running)"
        appdata_detail = _finish_appdata(install, ctx)
        return f"{stopped}; {appdata_detail}" if appdata_detail else stopped

    return run


def build_real_phases(
    scenario_name: str, keep_open: bool = False, install: GameInstall | None = None, test_save: str = DEFAULT_TEST_SAVE,
    telemetry_interval_s: float = DEFAULT_TELEMETRY_INTERVAL_S, fixture: str | None = None,
) -> list[Phase]:
    get_scenario(scenario_name)  # fail before any game starts if the name is wrong
    install = install or GameInstall()
    fixture = fixtures.check_name(fixture or fixtures.DEFAULT_FIXTURE)  # a bad name fails before any game starts
    return [
        Phase("preflight", _preflight(install, test_save, fixture), 60),
        Phase("deploy", _deploy(install), 120),
        Phase("launch", _launch(install, test_save, telemetry_interval_s), 60),
        Phase("boot", _boot, 240),
        Phase("scenario", _scenario(install, scenario_name), get_limit_s(scenario_name)),
        Phase("collect", _collect(install), 60, always_run=True),
        Phase("teardown", _teardown(install, keep_open), 30, always_run=True),
    ]
