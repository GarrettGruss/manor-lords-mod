"""Spike scenario (change spike-playtest-telemetry, #384, task 1.1): does a flushed Lua log keep its lines when the game process is killed?

Steps: start the probe log (flushed line every second, plus a control log that is never flushed), write a burst,
then a second burst in a thread, kill ONLY this run's game process during that burst, and read the files.
The files are copied to PROBE_OUT (default: the scratchpad folder from the environment variable PROBE_OUT).
A killed game is the point of this test. The run verdict is a crash verdict; the expectations here are the result.
"""
import os
import shutil
import threading
import time
from pathlib import Path

import psutil

NAME = "probe-playtest-crash"
DESCRIPTION = "Spike: kill the game during a log burst and count the lines that survive (flushed log and unflushed control)."
COVERS: list[str] = []
LIMIT_S = 120
HIDDEN = True

PREFIX = "PlaytestProbe."


def count_lines(path: Path) -> tuple[int, int, str]:
    data = path.read_bytes()
    text = data.decode("ascii", "replace")
    lines = text.split("\n")
    complete = [line for line in lines if line]
    last = complete[-1] if complete else ""
    return len(complete), len(data), last


def run(ctx) -> dict:
    out = Path(os.environ.get("PROBE_OUT", ".")) / ctx.run_dir.name
    out.mkdir(parents=True, exist_ok=True)
    appdata = Path(ctx.phase.state["appdata_dir"])
    root = appdata / "ManorLords" / "Saved" / "ProbeTelemetry"
    pid = ctx.phase.state["game_pid"]
    started = ctx.mod.command(PREFIX + "log_start")
    ctx.log.info(f"log_start {started}")
    time.sleep(8.0)  # about 8 tick lines
    first = ctx.mod.command(PREFIX + "burst", n=500)
    ctx.log.info(f"burst1 {first}")
    answers: list = []

    def long_burst() -> None:
        try:
            answers.append(ctx.mod.command(PREFIX + "burst", n=100000))
        except Exception as error:  # the game is killed under this call
            answers.append(f"ended: {type(error).__name__}")

    thread = threading.Thread(target=long_burst, daemon=True)
    thread.start()
    time.sleep(0.6)
    own = [p for p in ctx.game_processes() if p.pid == pid]
    ctx.expect.equals("only this run's game process is killed", len(own), 1)
    killed_at = time.time()
    own[0].kill()
    try:
        own[0].wait(timeout=10)
    except psutil.TimeoutExpired:
        pass
    ctx.log.info(f"killed pid {pid} at {killed_at}")
    time.sleep(1.0)
    shutil.copytree(root, out / "ProbeTelemetry", dirs_exist_ok=True)
    logs = sorted((root / "logs").glob("session-*.log"))
    controls = sorted((root / "logs").glob("control-noflush-*.log"))
    n_log, bytes_log, last_log = count_lines(logs[0])
    n_ctl, bytes_ctl, last_ctl = count_lines(controls[0])
    marker = (root / "session.marker").read_text()
    result_text = (f"flushed log: {n_log} lines {bytes_log} bytes, last line {last_log!r}; "
                   f"control (no flush): {n_ctl} lines {bytes_ctl} bytes, last line {last_ctl!r}; marker {marker}; burst answer {answers}")
    ctx.log.info(result_text)
    ctx.notes.append(result_text)
    ctx.metric("lines_flushed_log", n_log)
    ctx.metric("lines_control_log", n_ctl)
    ctx.expect.at_least("flushed log kept the burst lines", n_log, 500 + 5)
    ctx.expect.equals("last flushed line is complete", len(last_log.split(" ")) >= 4, True)
    return ctx.result()
