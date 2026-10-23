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

from . import fixtures, gameslots, saveslots
from .actions import ActionNotPossible
from .environment import MOD_FILES_NAME, gather_environment, hash_mod_files, hash_mods
from .pak_phases import install_paks, keep_paks_phase, remove_paks_phase
from .game import (
    DEFAULT_TELEMETRY_INTERVAL_S,
    DEFAULT_TEST_SAVE,
    GameInstall,
    game_launch_args,
    build_game_environment,
    count_pause_calls,
    ensure_game_alive,
    find_crash_reporters,
    find_game_processes,
    is_steam_running,
    read_boot_file,
    sleep_until,
    stop_processes,
)
from .runfolder import atomic_write_text, write_config
from .runner import Phase, PhaseContext, PhaseFailed
from .waiting import ScenarioFailure
from .scenario import REPO_ROOT, configure_bridge_client, get_limit_s, get_scenario
from .scenario_context import ScenarioContext
from .screenshot import capture_game_window
from .windows import list_windows, move_window, pick_game_window

BOOT_POLL_S = 1.0
BOOT_DEADLINE_S = 230  # a little under the phase limit, so the message says what happened
LAUNCH_ALIVE_CHECK_S = 3
DEPLOY_TIMEOUT_S = 110
MAX_CRASH_DIR_BYTES = 50 * 1024 * 1024
DEPLOY_SUMMARY = re.compile(r"Summary:.*errors:\s*(\d+)")
CRASH_CONTEXT_FILE = "CrashContext.runtime-xml"
CRASH_PROCESS_ID = re.compile(r"<ProcessId>(\d+)</ProcessId>")


# ---- preflight ----

def _stop_stale_game(install: GameInstall, ctx: PhaseContext) -> None:
    """Stop a game left from this slot's folder. A game of another slot belongs to a parallel run and stays (spec 11)."""
    stale = find_game_processes(install.root)
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


def _prepare_appdata(install: GameInstall, ctx: PhaseContext, fixture: str | None) -> fixtures.AppdataResult:
    """Build the private LOCALAPPDATA. Remember the user's save files, so teardown can compare."""
    ctx.state["appdata_dir"] = _appdata_dir(ctx)  # set first: teardown removes the folder even if the copy fails half way
    try:
        result = fixtures.prepare_appdata(install.saved_dir, _appdata_dir(ctx), fixtures.load_manifest(), fixture)
    except fixtures.FixtureError as error:
        raise PhaseFailed(f"fixture {fixture}: {error}") from error
    ctx.state["user_saves_snapshot"] = user_files(install)
    ctx.state["ledger_names_at_start"] = _ledger_names(install)
    ctx.state["user_save_dir"] = str(install.saved_dir / "SaveGames")  # the real folder, for the guarded save_game (spec 24)
    ctx.config.setdefault("environment", {})["fixture"] = result.as_dict()
    return result


def user_files(install: GameInstall, also_ignore: frozenset[str] = frozenset()) -> dict[str, str]:
    """The user's save files: the save folder without the files of harness saves, which parallel runs add and remove (spec 11),
    and without the settings file that the game rewrites at any time (`rtsSettings.sav`, #393).

    `also_ignore` holds names that the ledger listed earlier in this run (fixture saves of other slots, #353). A file is
    ignored only if a ledger entry named it: a file of the user is never in the ledger.

    Call it while holding saveslots.saves_lock(), so no other run changes the folder or the ledger in between.
    """
    save_dir = install.saved_dir / "SaveGames"
    harness_files = saveslots.harness_file_names(save_dir) | gameslots.GAME_REWRITTEN_SAVE_FILES | also_ignore
    return {name: digest for name, digest in fixtures.snapshot_user_files(save_dir).items() if name not in harness_files}


def _ledger_names(install: GameInstall) -> frozenset[str]:
    return frozenset(saveslots.harness_file_names(install.saved_dir / "SaveGames"))


def _game_slot(ctx: PhaseContext) -> int:
    return ctx.config.get("slot") or 0  # a fake run and the Steam folder use slot 0


def _remove_stale_slots(install: GameInstall, ctx: PhaseContext) -> None:
    """Remove slots that an earlier run installed and left (for example a --keep-open run). The game is stopped here."""
    for result in saveslots.uninstall_all(install.saved_dir / "SaveGames", game_slot=_game_slot(ctx)):
        ctx.state["notes"].append(f"removed the slot {result['slot']} of an earlier run: {len(result['removed'])} files"
                                  + (f"; kept {result['kept']}" if result["kept"] else ""))


def _choose_slot(install: GameInstall, ctx: PhaseContext, appdata: fixtures.AppdataResult, save_path: Path | None) -> str:
    """The slot the game loads. A stored fixture or a --save file is installed under a free name; an old fixture uses its source slot."""
    if save_path is not None:
        try:
            sources, label = fixtures.files_of_save(save_path), save_path.stem
        except fixtures.FixtureError as error:
            raise PhaseFailed(f"--save {save_path}: {error}") from error
    elif appdata.stored:
        sources, label = appdata.sources, appdata.fixture
    else:
        return appdata.source_slot
    try:
        installed = saveslots.install(install.saved_dir / "SaveGames", sources, label,
                                       game_slot=_game_slot(ctx), game_root=install.root)
    except saveslots.SlotError as error:
        raise PhaseFailed(f"install of the save failed: {error}") from error
    ctx.state["installed_slot"] = installed.slot
    ctx.config.setdefault("environment", {})["installed_slot"] = {"slot": installed.slot, "label": label,
                                                                  "files": len(installed.files)}
    return installed.slot


def _preflight(install: GameInstall, test_save: str, fixture: str = fixtures.DEFAULT_FIXTURE,
               pak_names: list[str] | None = None, pak_work_dir: Path | None = None, save_path: Path | None = None,
               new_game: bool = False):
    def run(ctx: PhaseContext) -> str | None:
        ctx.state["run_started_epoch"] = time.time()
        if not is_steam_running():
            # Not an error: a direct launch works without Steam (tested 2026-10-10: READY after 32 s, the game does not start
            # Steam). The note tells the reader that this run had no Steam.
            ctx.state["notes"].append("Steam was not running; the game was started directly without it")
        venv_python = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            raise PhaseFailed(f"venv not found: {venv_python}")
        if not install.exe.exists():
            raise PhaseFailed(f"game exe not found: {install.exe}")
        _stop_stale_game(install, ctx)
        # One run at a time changes the user's save folder: the slot number and the snapshot must not race.
        with saveslots.saves_lock():
            _remove_stale_slots(install, ctx)
            appdata = _prepare_appdata(install, ctx, None if new_game else fixture)
            slot = "" if new_game else _choose_slot(install, ctx, appdata, save_path)  # a fresh start loads no slot
        ctx.state["test_save"] = slot
        ctx.config["test_save"] = slot
        if slot and not install.save_file(slot).is_file():  # the game loads from the user's real save folder
            raise PhaseFailed(f"test save not found: {install.save_file(slot)}")
        ctx.config.setdefault("environment", {}).update(
            gather_environment(install, REPO_ROOT, ctx.run.path, slot)  # the save that the game loads is in the real folder
        )
        write_config(ctx.run, ctx.config)
        if pak_names:
            install_paks(install, ctx, pak_names, pak_work_dir)
        return None

    return run


# ---- deploy ----

def _record_mod_files(ctx: PhaseContext) -> None:
    """Write the hash of every mod file next to the summary. The release gate reads it (spec 19)."""
    files = hash_mod_files(REPO_ROOT / "mod")
    (ctx.run.path / MOD_FILES_NAME).write_text(json.dumps(files, indent=1, sort_keys=True), encoding="utf-8")
    ctx.config["environment"]["mod_files"] = MOD_FILES_NAME


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
        _record_mod_files(ctx)
        write_config(ctx.run, ctx.config)
        return summary_line

    return run


# ---- launch ----

def _launch(install: GameInstall, test_save: str, telemetry_interval_s: float, extra_env: dict[str, str] | None = None,
            new_game_map: str | None = None):
    def run(ctx: PhaseContext) -> str | None:
        env = build_game_environment(ctx.run.path, ctx.state.get("test_save", test_save), telemetry_interval_s=telemetry_interval_s,
                                     appdata_dir=ctx.state.get("appdata_dir"), extra_env=extra_env,
                                     new_game_map=new_game_map)
        # A game that reads the save list at the same time as another game, or while a run changes the save folder,
        # sees only part of the list (spec 11, step 4). The boot releases the lock after the menu.
        hold_save_scan_lock(ctx)
        # The working folder must be Win64, or UE4SS does not find its files.
        popen = subprocess.Popen(
            [str(install.exe), *game_launch_args(env)], cwd=install.win64, env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        ctx.state["game_popen"] = popen
        ctx.state["game_pid"] = popen.pid
        ctx.state["launch_monotonic"] = time.monotonic()
        time.sleep(LAUNCH_ALIVE_CHECK_S)
        ensure_game_alive(ctx, "launch")
        return f"game started, PID {popen.pid}"

    return run


# The boot states in which the game may still read the save list. After them the lock is free for the next game.
SAVE_SCAN_STATES = ("no boot.json yet", "WAITING_FOR_MENU")
SAVE_SCAN_LOCK_MAX_S = 90.0  # a game stuck in the menu must not block the other slots longer
# Preflight, launch and teardown wait for runs/.saves.lock while other slots use it. The wait must not use up the phase limit.
LOCK_WAIT_S = saveslots.SAVES_LOCK_TIMEOUT_S


def hold_save_scan_lock(ctx: PhaseContext) -> None:
    lock = saveslots.saves_lock()
    lock.acquire()
    ctx.state["save_scan_lock"] = lock


def release_save_scan_lock(ctx: PhaseContext) -> None:
    lock = ctx.state.pop("save_scan_lock", None)
    if lock is not None:
        lock.release()


GAME_RECORD_FILE = "game.json"


def write_game_record(ctx: PhaseContext) -> None:
    # Why: a kept-open game can crash after the run ended. collect_crash.py needs the pid and start time to find its report.
    record = {"pid": ctx.state["game_pid"], "run_started_epoch": ctx.state.get("run_started_epoch", 0.0),
              "appdata_dir": ctx.state.get("appdata_dir")}
    atomic_write_text(ctx.run.path / GAME_RECORD_FILE, json.dumps(record, default=str))


# ---- boot ----

def _boot_result(boot_file: dict, seconds: float, pause_calls: int) -> dict:
    return {
        "state": boot_file["state"],
        "seconds": round(seconds, 1),
        "pause_calls": pause_calls,
        "reason": boot_file.get("reason"),
    }


def place_window_in_tile(ctx: PhaseContext, slot: gameslots.GameSlot) -> None:
    """Move the game window to the slot's screen tile, so parallel games do not cover each other. A failure is a note."""
    if not gameslots.settings_installed():
        return  # without the harness settings the window is full size, and a tile does not help
    try:
        window = pick_game_window(list_windows(), {ctx.state["game_pid"]})
        move_window(window["hwnd"], *slot.tile)
    except Exception as error:  # noqa: BLE001 - a window problem must not fail the run
        ctx.state["notes"].append(f"window not moved to the tile of slot {slot.number}: {error}")


def _boot_phase(slot: gameslots.GameSlot | None):
    def run(ctx: PhaseContext) -> str | None:
        message = _boot(ctx)
        if slot is not None:
            place_window_in_tile(ctx, slot)
        return message

    return run


def _boot(ctx: PhaseContext) -> str | None:
    try:
        return _wait_for_boot(ctx)
    finally:
        release_save_scan_lock(ctx)


def _wait_for_boot(ctx: PhaseContext) -> str | None:
    started = ctx.state["launch_monotonic"]
    deadline = time.monotonic() + BOOT_DEADLINE_S
    last_state = "no boot.json yet"
    while time.monotonic() < deadline:
        ensure_game_alive(ctx, "boot")
        boot_file = read_boot_file(ctx.run.boot_path)
        if boot_file:
            last_state = str(boot_file.get("state"))
        seconds = time.monotonic() - started
        if last_state not in SAVE_SCAN_STATES or seconds > SAVE_SCAN_LOCK_MAX_S:
            release_save_scan_lock(ctx)
        if boot_file:
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
    # Only this run's game: another slot may run a game at the same time (spec 11).
    pids = {ctx.state["game_pid"]} if ctx.state.get("game_pid") else {process.pid for process in find_game_processes()}
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
        except ScenarioFailure as error:
            # A real result too: the game stalled, a pop-up held it, or a wait ran out. A dead game is a crash first.
            ensure_game_alive(ctx, "scenario")
            result = scenario_ctx.fail(type(error).__name__, str(error))
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


def read_crash_process_id(folder: Path) -> int | None:
    """The process id that UE wrote into the crash report, or None if the report has no readable id."""
    try:
        text = (folder / CRASH_CONTEXT_FILE).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = CRASH_PROCESS_ID.search(text)
    return int(match.group(1)) if match else None


def is_crash_of_process(folder: Path, game_pid: int | None) -> bool:
    """True if the report may belong to the game process. A report without an id counts as a match."""
    if game_pid is None:
        return True
    report_pid = read_crash_process_id(folder)
    return report_pid is None or report_pid == game_pid


def copy_new_crash_dirs(install: GameInstall, crash_dir: Path, since_epoch: float, notes: list[str],
                        game_pid: int | None = None) -> list[str]:
    """Copy crash report folders newer than `since_epoch` that belong to `game_pid`.

    Return their paths relative to the run folder. The pid check keeps a crash of another game
    process (for example one the user started) out of the run.
    """
    if not install.crashes_dir.is_dir():
        return []
    copied = []
    for folder in sorted(p for p in install.crashes_dir.iterdir() if p.is_dir()):
        if folder.stat().st_mtime <= since_epoch or not is_crash_of_process(folder, game_pid):
            continue
        if (crash_dir / folder.name).exists():
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
        if dump.stat().st_mtime > since_epoch and not (crash_dir / dump.name).exists():
            shutil.copy2(dump, crash_dir / dump.name)
            copied.append(f"{crash_dir.name}/{dump.name}")
    return copied


def copy_crash_reports(install: GameInstall, ctx: PhaseContext, since_epoch: float) -> list[str]:
    """Copy the crash reports of this run's game.

    The crash handler of UE writes into the user's REAL `Crashes` folder, not into the private appdata
    (seen in a real crash, see real-crash-report.md). So the real folder is searched, and the private one too.
    """
    searched = [install]
    if ctx.state.get("appdata_dir"):
        searched.insert(0, _private_install(install, ctx))
    copied: list[str] = []
    for where in searched:
        copied += copy_new_crash_dirs(where, ctx.run.crash_dir, since_epoch, ctx.state["notes"], ctx.state.get("game_pid"))
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
        crash_dirs = copy_crash_reports(install, ctx, since)
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

def _remove_installed_slot(ctx: PhaseContext) -> None:
    """Delete the slot this run installed, before the user's save folder is compared with the preflight snapshot."""
    slot = ctx.state.pop("installed_slot", None)
    if slot is None:
        return
    result = saveslots.uninstall_slot(slot)
    ctx.state["notes"].append(f"installed slot {slot} removed ({len(result['removed'])} files)"
                              + (f"; kept {result['kept']}" if result["kept"] else ""))


def _remove_harness_saves(install: GameInstall, ctx: PhaseContext) -> None:
    """Delete the files of harness saves (spec 24) that the ledger lists. Saves that a scenario keeps are not in the ledger."""
    for result in saveslots.uninstall_all(install.saved_dir / "SaveGames", game_slot=_game_slot(ctx)):
        ctx.state["notes"].append(f"harness save {result['slot']} removed ({len(result['removed'])} files)"
                                  + (f"; kept {result['kept']}" if result["kept"] else ""))


def _expected_user_files(ctx: PhaseContext) -> dict[str, str]:
    """The preflight snapshot plus the files of harness saves that the scenario asked to keep."""
    return {**ctx.state.get("user_saves_snapshot", {}), **ctx.state.get("kept_save_files", {})}


def _finish_appdata(install: GameInstall, ctx: PhaseContext) -> str | None:
    """Remove the installed slot, compare the user's save files with the snapshot of preflight, then delete the run's appdata."""
    appdata = ctx.state.get("appdata_dir")
    if not appdata:
        return None
    with saveslots.saves_lock():
        _remove_installed_slot(ctx)
        _remove_harness_saves(install, ctx)
        # A fixture save of another slot can be listed at the start only, or at the end only (#353): ignore both.
        ignore = ctx.state.get("ledger_names_at_start", frozenset()) | _ledger_names(install)
        expected = {name: digest for name, digest in _expected_user_files(ctx).items() if name not in ignore}
        problems = fixtures.describe_difference(expected, user_files(install, ignore))
    removed = fixtures.remove_appdata(appdata)
    if problems:
        raise PhaseFailed(f"the user's save files changed during the run: {'; '.join(problems[:10])}")
    ctx.state["notes"].append(f"private appdata removed ({removed} files); the user's save files did not change")
    return f"appdata removed ({removed} files), user saves unchanged"


def stop_orphan_crash_reporters(ctx: PhaseContext) -> None:
    """After a crash, CrashReportClient.exe stays open and waits for a click. Stop the ones of this run's game."""
    game_pid = ctx.state.get("game_pid")
    if game_pid is None:
        return
    orphans = [process for process in find_crash_reporters() if process.ppid() == game_pid]
    if not orphans:
        return
    stop_processes(orphans)
    ctx.state["notes"].append(f"{len(orphans)} CrashReportClient process(es) of the crashed game were stopped")


def _teardown(install: GameInstall, keep_open: bool):
    def run(ctx: PhaseContext) -> str | None:
        # Set first, so the end of the process is not read as a crash.
        ctx.state["game_stop_requested"] = True
        release_save_scan_lock(ctx)  # the launch held it, and the boot phase did not run
        if keep_open:
            ctx.state["notes"].append("--keep-open: the game was left running")
            if ctx.state.get("appdata_dir"):
                ctx.state["notes"].append(f"private appdata is still in place: {ctx.state['appdata_dir']}")
                if ctx.state.get("installed_slot"):
                    ctx.state["notes"].append(f"installed slot {ctx.state['installed_slot']} is still in the user's save folder; "
                                              "the next run removes it, or run: harness/tools/fixtures.py uninstall")
                ctx.state["notes"].append("the user's save files were not compared (--keep-open). "
                                          "Stop the game with powershell -ExecutionPolicy Bypass -File harness/game-close.ps1 -Slot <n> (or the MCP tool stop_game), then delete the appdata with "
                                          "harness/tools/fixtures.py remove --appdata <that folder>")
            return "teardown: game left running (--keep-open)"
        running = find_game_processes(install.root)
        stop_processes(running)
        remaining = find_game_processes(install.root)
        if remaining:
            raise PhaseFailed(f"game process remains after teardown: PID {[p.pid for p in remaining]}")
        # UE4SS.log is buffered, so the copy from collect can be short. Copy again after the game ended.
        if copy_ue4ss_log(install, ctx.run.path):
            ctx.state["artifacts"]["logs"] = list_logs(ctx.run.path)
        stop_orphan_crash_reporters(ctx)
        pids = [process.pid for process in running]
        stopped = f"teardown: game stopped (PID {pids})" if pids else "teardown: game stopped (none was running)"
        appdata_detail = _finish_appdata(install, ctx)
        return f"{stopped}; {appdata_detail}" if appdata_detail else stopped

    return run


def build_real_phases(
    scenario_name: str, keep_open: bool = False, install: GameInstall | None = None, test_save: str = DEFAULT_TEST_SAVE,
    telemetry_interval_s: float = DEFAULT_TELEMETRY_INTERVAL_S, fixture: str | None = None,
    pak_names: list[str] | None = None, pak_work_dir: Path | None = None, extra_env: dict[str, str] | None = None,
    save_path: Path | None = None, new_game_map: str | None = None, slot: gameslots.GameSlot | None = None,
) -> list[Phase]:
    """`slot` picks the game folder (spec 11). Without it the run uses `install`, or the normal game folder."""
    get_scenario(scenario_name)  # fail before any game starts if the name is wrong
    install = install or (slot.install() if slot else GameInstall())
    fixture = fixtures.check_name(fixture or fixtures.DEFAULT_FIXTURE)  # a bad name fails before any game starts
    phases = [
        Phase("preflight", _preflight(install, test_save, fixture, pak_names, pak_work_dir, save_path, new_game_map is not None),
              60 + LOCK_WAIT_S),
        Phase("deploy", _deploy(install), 120),
        Phase("launch", _launch(install, test_save, telemetry_interval_s, extra_env, new_game_map), 60 + LOCK_WAIT_S),
        Phase("boot", _boot_phase(slot), 240),
        Phase("scenario", _scenario(install, scenario_name), get_limit_s(scenario_name)),
        Phase("collect", _collect(install), 60, always_run=True),
        Phase("teardown", _teardown(install, keep_open), 30 + LOCK_WAIT_S, always_run=True),
    ]
    if pak_names and keep_open:
        # The game is still running and loads pak assets lazily (a widget on its first open). Removing the pak under it
        # hung the game on F9 (techmenu-session-1 to -3). The paks stay; the next run with --pak replaces them.
        phases.append(keep_paks_phase())
    elif pak_names:
        # After teardown: the game is stopped by then, so it no longer holds the pak file.
        phases.append(remove_paks_phase(install))
    return phases
