"""Spike 11: start one game from a slot folder, boot a new game, measure it, then stop it.

Usage: uv run python harness/tools/spike11_worker.py --slot-root <slot game root> --run-dir <dir> --settings low|user

It prints one JSON line with the result. The orchestrator is harness/tools/spike11_slots.py.
A new game is used, so no fixture is installed in the user's save folder.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runlib.bridge_client import Bridge  # noqa: E402
from runlib.windows import list_windows, pick_game_window  # noqa: E402
from runlib.game import GameInstall, build_game_environment, read_boot_file, stop_processes  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BOOT_TIMEOUT_S = 300
MEASURE_S = 20
REAL_USER_SETTINGS = Path(os.environ["LOCALAPPDATA"]) / "ManorLords" / "Saved" / "Config" / "Windows" / "GameUserSettings.ini"

LOW_SETTINGS = """;METADATA=(Diff=true, UseCommands=true)
[ScalabilityGroups]
sg.ResolutionQuality=50
sg.ViewDistanceQuality=0
sg.AntiAliasingQuality=0
sg.ShadowQuality=0
sg.GlobalIlluminationQuality=0
sg.ReflectionQuality=0
sg.PostProcessQuality=0
sg.TextureQuality=0
sg.EffectsQuality=0
sg.FoliageQuality=0
sg.ShadingQuality=0
sg.LandscapeQuality=0

[/Script/Engine.GameUserSettings]
bUseVSync=False
bUseDynamicResolution=False
ResolutionSizeX=1280
ResolutionSizeY=720
LastUserConfirmedResolutionSizeX=1280
LastUserConfirmedResolutionSizeY=720
WindowPosX=-1
WindowPosY=-1
FullscreenMode=2
LastConfirmedFullscreenMode=2
PreferredFullscreenMode=2
Version=5
AudioQualityLevel=0
LastConfirmedAudioQualityLevel=0
FrameRateLimit=30.000000
"""


# The game reads its own settings (resolution, fps cap, quality) from UserSettings.ini, not only GameUserSettings.ini.
LOW_GAME_SETTINGS = """;METADATA=(Diff=true, UseCommands=true)
[Settings]
ML.tutorials=false
ML.aaMode=none
r.ngx.dlss.enable=0
r.VSync=0
Foliage.LODDistanceScale=0.3
ML.grassDistance=0.2
ML.grassDensity=0.2
r.ViewDistanceScale=0.4
r.VolumetricFog=0
ML.volumetricClouds=false
r.volumetriccloud=0
r.LightShaftQuality=0
r.BloomQuality=0
sg.ResolutionQuality=50
sg.ViewDistanceQuality=0
sg.AntiAliasingQuality=0
sg.ShadowQuality=0
sg.GlobalIlluminationQuality=0
sg.ReflectionQuality=0
sg.PostProcessQuality=0
sg.TextureQuality=0
sg.EffectsQuality=0
sg.FoliageQuality=0
sg.ShadingQuality=0
sg.LandscapeQuality=0
r.MaterialQualityLevel=0
t.MaxFps=30
r.setres=1280x720w
r.Streaming.PoolSize=400
"""


def write_settings(appdata: Path, settings: str) -> None:
    """Put the graphics settings into the private appdata. The user's real config is only read, never written."""
    config = appdata / "ManorLords" / "Saved" / "Config" / "Windows"
    config.mkdir(parents=True, exist_ok=True)
    if settings in ("low", "low-live"):
        (config / "GameUserSettings.ini").write_text(LOW_SETTINGS, encoding="utf-8")
        (config / "UserSettings.ini").write_text(LOW_GAME_SETTINGS, encoding="utf-8")
    elif settings == "user":
        for name in ("GameUserSettings.ini", "UserSettings.ini"):
            shutil.copyfile(REAL_USER_SETTINGS.parent / name, config / name)
    else:
        raise ValueError(f"unknown settings {settings!r}")


# The game reads its settings from the REAL user folder, not the private LOCALAPPDATA (checked 2026-10-17:
# the window stayed 2560x1440). So low settings are applied live, after READY, and are not saved.
# The map load applies the real user resolution again, so r.setres is needed after READY too.
LOW_CONSOLE_COMMANDS = ("scalability 0", "r.setres 1280x720w", "t.MaxFps 30", "r.Streaming.PoolSize 400",
                        "r.VolumetricFog 0", "r.volumetriccloud 0", "r.ScreenPercentage 50")


def apply_low_console(bridge_one) -> list:
    return [bridge_one("console", command=command).get("ok", True) for command in LOW_CONSOLE_COMMANDS]


def connect_bridge(install: GameInstall, run_dir: Path) -> Bridge:
    os.environ["UE4SS_BRIDGE_GAME_DIR"] = str(install.win64)
    os.environ["UE4SS_BRIDGE_DATA_DIR"] = str((run_dir / "bridge").resolve())
    sys.path.insert(0, str(REPO_ROOT / "mcp"))
    from ue4ss_bridge import server

    return Bridge(server.one), server.one


def wait_for_ready(run_dir: Path, process: subprocess.Popen) -> float:
    started = time.monotonic()
    while time.monotonic() - started < BOOT_TIMEOUT_S:
        if process.poll() is not None:
            raise RuntimeError(f"game exited during boot with code {process.returncode}")
        boot = read_boot_file(run_dir / "boot.json")
        if boot and boot.get("state") == "FAILED":
            raise RuntimeError(f"HarnessBoot FAILED: {boot.get('reason')}")
        if boot and boot.get("state") == "READY":
            return round(time.monotonic() - started, 1)
        time.sleep(1)
    raise RuntimeError(f"no READY in {BOOT_TIMEOUT_S} s")


def measure_rate(bridge: Bridge, speed_index: int, process: psutil.Process) -> dict:
    """Run at one speed for MEASURE_S wall seconds. Set the speed again every 2 s, because the game can drop to 1x."""
    engine = bridge.engine_path()
    rss_peak = 0
    clock_start = bridge.read_clock_value(engine)
    wall_start = time.monotonic()
    while time.monotonic() - wall_start < MEASURE_S:
        bridge.call_on_player("changeGameSpeed", [speed_index, False])
        rss_peak = max(rss_peak, process.memory_info().rss)
        time.sleep(2)
    clock_end = bridge.read_clock_value(engine)
    wall = time.monotonic() - wall_start
    return {"speed_index": speed_index, "clock_rate": round((clock_end - clock_start) / wall, 3),
            "rss_peak_mb": round(rss_peak / 2**20)}


def gpu_dedicated_mb(pid: int) -> int:
    """Dedicated GPU memory of one process, from the Windows performance counter."""
    command = (rf"(Get-Counter '\GPU Process Memory(pid_{pid}_*)\Dedicated Usage').CounterSamples"
               " | Measure-Object -Property CookedValue -Sum | ForEach-Object Sum")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, check=True)
    return round(float(out.stdout.strip()) / 2**20)


SWP_NOSIZE_NOZORDER_NOACTIVATE = 0x0001 | 0x0004 | 0x0010


def move_window(hwnd: int, x: int, y: int) -> None:
    """Move the game window to a screen tile. The game ignores -WinX and -WinY (checked 2026-10-17)."""
    import ctypes

    if not ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, SWP_NOSIZE_NOZORDER_NOACTIVATE):
        raise RuntimeError(f"SetWindowPos failed for window {hwnd}")


def window_of(pid: int) -> dict:
    return pick_game_window(list_windows(), {pid})


def window_rect_when_shown(popen: subprocess.Popen, timeout_s: float = 60) -> list | None:
    """The first rectangle of the game window, to see the size and place before any console command runs."""
    started = time.monotonic()
    while time.monotonic() - started < timeout_s:
        try:
            return pick_game_window(list_windows(), {popen.pid}).get("rect")
        except Exception:  # noqa: BLE001 - no window yet
            time.sleep(0.5)
    return None


def run(slot_root: Path, run_dir: Path, settings: str, hold_s: float, game_args: list[str],
        tile: tuple[int, int] | None) -> dict:
    install = GameInstall(root=slot_root)
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "bridge").mkdir()
    appdata = run_dir / "appdata"
    write_settings(appdata, settings)
    env = build_game_environment(run_dir, "", appdata_dir=appdata, new_game_map="Jagged_Cliffs")
    popen = subprocess.Popen([str(install.exe), *game_args], cwd=install.win64, env=env,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = {"slot_root": str(slot_root), "settings": settings, "pid": popen.pid, "game_args": game_args}
    try:
        process = psutil.Process(popen.pid)
        result["window_at_menu"] = window_rect_when_shown(popen)
        if tile is not None:
            move_window(window_of(popen.pid)["hwnd"], *tile)
            result["window_after_move"] = window_of(popen.pid)["rect"]
        result["boot_s"] = wait_for_ready(run_dir, popen)
        bridge, bridge_one = connect_bridge(install, run_dir)
        if settings == "low-live":
            result["console"] = apply_low_console(bridge_one)
        if tile is not None:
            time.sleep(1)  # lets the resize finish before the move
            move_window(window_of(popen.pid)["hwnd"], *tile)
        result["unpause"] = bridge.unpause()["ok"]
        result["rates"] = [measure_rate(bridge, 1, process), measure_rate(bridge, 3, process)]
        bridge.pause()
        result["gpu_dedicated_mb"] = gpu_dedicated_mb(popen.pid)
        result["window_rect"] = pick_game_window(list_windows(), {popen.pid}).get("rect")
        time.sleep(hold_s)  # the orchestrator samples GPU memory while all games are up
        result["rss_end_mb"] = round(process.memory_info().rss / 2**20)
        result["ok"] = True
    except Exception as error:  # noqa: BLE001 - a spike reports the error as data
        result["ok"] = False
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        if popen.poll() is None:
            try:
                stop_processes([psutil.Process(popen.pid)])
            except RuntimeError as error:  # a slow exit must not lose the measurements
                result["stop_note"] = str(error)
                popen.kill()
                popen.wait(30)
        result["exit_code"] = popen.poll()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot-root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--settings", choices=("low", "low-live", "user"), default="low")
    parser.add_argument("--hold", type=float, default=20)
    parser.add_argument("--tile", type=int, nargs=2, metavar=("X", "Y"), help="move the window to this screen position")
    parser.add_argument("--game-args", default="", help="space separated launch arguments for the game")
    args = parser.parse_args()
    print(json.dumps(run(args.slot_root, args.run_dir, args.settings, args.hold, args.game_args.split(),
                         tuple(args.tile) if args.tile else None)))


if __name__ == "__main__":
    main()
