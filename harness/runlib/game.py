"""The game install, its processes, its environment and its boot files.

Everything here works on plain paths and psutil handles, so tests can use temp folders and fakes.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import psutil

from .runner import PhaseContext, PhaseFailed

GAME_PROCESS_NAMES = ("manorlords-win64-shipping.exe", "manorlords.exe")  # the real game, then the Steam stub
CRASH_REPORTER_NAMES = ("crashreportclient.exe",)  # UE starts it when the game crashes, and it waits for a click
STEAM_PROCESS_NAME = "steam.exe"
PAUSE_CALL_MARKER = "calling pauseGame"
DEFAULT_TEST_SAVE = "saveGame_0"
STOP_WAIT_S = 10


def _default_root() -> Path:
    return Path(r"C:\Program Files (x86)\Steam\steamapps\common\Manor Lords")


def _local_app_data() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "ManorLords" / "Saved"


@dataclass(frozen=True)
class GameInstall:
    """Where the game and its data are. Tests pass temp folders."""

    root: Path = field(default_factory=_default_root)
    saved_dir: Path = field(default_factory=_local_app_data)

    @property
    def win64(self) -> Path:
        return self.root / "ManorLords" / "Binaries" / "Win64"

    @property
    def exe(self) -> Path:
        return self.win64 / "ManorLords-Win64-Shipping.exe"

    @property
    def ue4ss_log(self) -> Path:
        return self.win64 / "ue4ss" / "UE4SS.log"

    @property
    def appmanifest(self) -> Path:
        return self.root.parent.parent / "appmanifest_1363080.acf"

    def save_file(self, slot: str) -> Path:
        return self.saved_dir / "SaveGames" / f"{slot}.sav"

    @property
    def crashes_dir(self) -> Path:
        return self.saved_dir / "Crashes"


def find_processes(names: tuple[str, ...]) -> list[psutil.Process]:
    found = []
    for process in psutil.process_iter(["name"]):
        if (process.info["name"] or "").lower() in names:
            found.append(process)
    return found


def find_game_processes() -> list[psutil.Process]:
    return find_processes(GAME_PROCESS_NAMES)


def find_crash_reporters() -> list[psutil.Process]:
    return find_processes(CRASH_REPORTER_NAMES)


def is_steam_running() -> bool:
    return bool(find_processes((STEAM_PROCESS_NAME,)))


def stop_processes(processes: list[psutil.Process], wait_s: float = STOP_WAIT_S) -> None:
    """Terminate the processes and wait until they are gone. Raise if one stays.

    The game ignores a close request, so there is no polite step.
    """
    for process in processes:
        try:
            process.terminate()
        except psutil.NoSuchProcess:
            pass  # it ended on its own: the goal is reached
    _gone, alive = psutil.wait_procs(processes, timeout=wait_s)
    if alive:
        raise RuntimeError(f"game process still running after terminate: PID {[p.pid for p in alive]}")


DEFAULT_TELEMETRY_INTERVAL_S = 5.0


def build_game_environment(run_dir: Path, test_save: str, base_env: dict | None = None,
                           telemetry_interval_s: float = DEFAULT_TELEMETRY_INTERVAL_S,
                           appdata_dir: Path | None = None) -> dict:
    """The environment for the game process. Each run has its own HARNESS_RUN_DIR.

    With `appdata_dir` the game gets its own LOCALAPPDATA. Its saves, config and crash reports then live there,
    and the user's save folder is never touched by the game.
    """
    env = dict(os.environ if base_env is None else base_env)
    if appdata_dir is not None:
        env["LOCALAPPDATA"] = str(Path(appdata_dir).resolve())
    env["HARNESS_RUN_DIR"] = str(Path(run_dir).resolve())
    env["HARNESS_AUTOBOOT"] = "1"
    env["HARNESS_TEST_SAVE"] = test_save
    env["HARNESS_TELEMETRY_INTERVAL_S"] = f"{telemetry_interval_s:g}"  # 0 turns telemetry off
    return env


def read_boot_file(path: Path) -> dict | None:
    """Return boot.json as a dict, or None if it is missing or not readable yet."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def count_pause_calls(mod_log: Path) -> int:
    try:
        text = Path(mod_log).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return 0
    return sum(1 for line in text.splitlines() if PAUSE_CALL_MARKER in line)


def ensure_game_alive(ctx: PhaseContext, where: str) -> None:
    """Raise PhaseFailed and record a crash if the game ended without a stop request."""
    if ctx.state["game_stop_requested"]:
        return
    exit_code = ctx.state["game_popen"].poll()
    if exit_code is None:
        return
    ctx.state["crash"] = {"reason": f"game process ended during {where}", "exit_code": exit_code}
    raise PhaseFailed(f"game process ended during {where} (exit code {exit_code})")


def sleep_until(deadline: float, step_s: float) -> None:
    time.sleep(max(0.0, min(step_s, deadline - time.monotonic())))
