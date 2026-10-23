"""Spike scenario (change spike-playtest-telemetry, #384, task 1.2): which reflected functions run when the game quits cleanly?

The probe hooks candidate functions and logs each call to a flushed log. The scenario closes the window of THIS run's game
(WM_CLOSE, no real mouse), waits for the process to end, and copies the log. If the game does not end in 25 s, only this
run's game process is killed. The files are copied to PROBE_OUT/<run>.
"""
import ctypes
import os
import shutil
import time
from pathlib import Path

import psutil

NAME = "probe-playtest-quit"
DESCRIPTION = "Spike: hook candidate quit functions, close the game window, read which hooks ran."
COVERS: list[str] = []
LIMIT_S = 150
HIDDEN = True

PREFIX = "PlaytestProbe."
WM_CLOSE = 0x0010


def run(ctx) -> dict:
    out = Path(os.environ["PROBE_OUT"]) / ctx.run_dir.name
    out.mkdir(parents=True, exist_ok=True)
    root = Path(ctx.phase.state["appdata_dir"]) / "ManorLords" / "Saved" / "ProbeTelemetry"
    pid = ctx.phase.state["game_pid"]
    cmd = lambda name, **a: ctx.mod.command(PREFIX + name, **a)  # noqa: E731
    cmd("log_start")
    cmd("gc_sentinel")
    hooks = cmd("quit_hooks")
    ctx.log.info(f"quit_hooks {hooks}")
    time.sleep(4.0)
    window = ctx.game_window()
    ctx.log.info(f"closing window {window}")
    ctypes.windll.user32.PostMessageW(window["hwnd"], WM_CLOSE, 0, 0)
    t0 = time.monotonic()
    process = psutil.Process(pid)
    ended = False
    while time.monotonic() - t0 < 25:
        if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
            ended = True
            break
        time.sleep(0.25)
    ctx.log.info(f"game ended after WM_CLOSE: {ended} ({time.monotonic() - t0:.1f} s)")
    if not ended:
        process.kill()
        process.wait(timeout=10)
    time.sleep(1.0)
    shutil.copytree(root, out / "ProbeTelemetry", dirs_exist_ok=True)
    log = sorted((root / "logs").glob("session-*.log"))[0].read_text()
    hook_lines = [line for line in log.splitlines() if " hook " in line]
    ctx.log.info(f"hook lines {len(hook_lines)}; first {hook_lines[:6]}; last {hook_lines[-6:]}")
    ctx.log.info(f"marker after exit: {(root / 'session.marker').read_text()}")
    ctx.notes.append(f"ended by WM_CLOSE: {ended}; hook lines {len(hook_lines)}")
    ctx.metric("hook_lines", len(hook_lines))
    return ctx.result()
