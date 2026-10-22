"""Spike scenario (change spike-playtest-telemetry, #384, tasks 1.2 to 1.4): crash detection at the next start, file access, stored zip.

Seed (the private appdata of this run only): the marker and logs of an earlier killed run (PROBE_OUT/<run>/ProbeTelemetry),
two real UE crash folders (copied read only from the user's Crashes folder), a copy of a fixture save under ProbeTelemetry/fixture/.
Then: detect the stale marker, find the newest crash folder, read the save, write a report folder, build the zip in one go and in
steps, and measure how long a bridge read of the game clock takes while the zip runs (a stand-in for a frame stall).
Never writes into any SaveGames folder.
"""
import os
import shutil
import threading
import time
import zipfile
import zlib
from pathlib import Path

NAME = "probe-playtest-files"
DESCRIPTION = "Spike: stale marker detection, newest crash folder, read a save copy, report folder, stored zip timings."
COVERS: list[str] = []
LIMIT_S = 300
HIDDEN = True

PREFIX = "PlaytestProbe."
REPO = Path(__file__).resolve().parents[2]
FIXTURE_SAV = REPO / "harness/fixtures/saves/base/slot.sav"
REAL_CRASHES = Path(os.environ["LOCALAPPDATA"]) / "ManorLords" / "Saved" / "Crashes"  # read only


class LatencySampler:
    """Reads the game clock in a loop and keeps (time, seconds the read took)."""

    def __init__(self, ctx):
        self.ctx, self.rows, self.stop = ctx, [], False
        self.engine = ctx.bridge.engine_path()

    def loop(self) -> None:
        while not self.stop:
            t0 = time.monotonic()
            try:
                self.ctx.bridge.read_clock_value(self.engine)
            except Exception:  # noqa: BLE001 - a spike
                pass
            self.rows.append((t0, time.monotonic() - t0))
            time.sleep(0.05)

    def window(self, t_from: float, t_to: float) -> dict:
        values = [d for t, d in self.rows if t_from <= t <= t_to]
        if not values:
            return {"n": 0}
        return {"n": len(values), "max_ms": round(max(values) * 1000), "mean_ms": round(sum(values) / len(values) * 1000)}


def seed(ctx, prev: Path) -> Path:
    root = Path(ctx.phase.state["appdata_dir"]) / "ManorLords" / "Saved"
    inv = root / "ProbeTelemetry"
    shutil.copytree(prev / "ProbeTelemetry", inv, dirs_exist_ok=True)
    (inv / "fixture").mkdir(exist_ok=True)
    shutil.copyfile(FIXTURE_SAV, inv / "fixture" / "fixture-save.sav")
    folders = sorted((p for p in REAL_CRASHES.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime)[-2:]
    for index, folder in enumerate(folders):
        target = root / "Crashes" / folder.name
        shutil.copytree(folder, target)
        os.utime(target, (time.time() - 3600 * (2 - index), time.time() - 3600 * (2 - index)))
    ctx.notes.append(f"seeded crash folders {[f.name for f in folders]}; newest is {folders[-1].name}")
    return folders[-1]


def run(ctx) -> dict:
    expect = ctx.expect
    prev = Path(os.environ["PROBE_OUT"]) / os.environ.get("PROBE_PREV", "ptt-crash-3")
    newest = seed(ctx, prev)
    cmd = lambda name, **a: ctx.mod.command(PREFIX + name, **a)  # noqa: E731
    detected = cmd("detect_previous")
    ctx.log.info(f"detect_previous {detected}")
    expect.equals("stale marker means the last session crashed", detected.get("crashed"), True)
    expect.at_least("marker age in seconds", detected.get("age_s", -1), 1)

    crash = cmd("newest_crash")
    ctx.log.info(f"newest_crash {crash}")
    expect.equals("newest crash folder found by dir /o-d", crash.get("newest"), newest.name)

    saved = ctx.read_file_crc = zlib.crc32(FIXTURE_SAV.read_bytes())
    read = cmd("read_test", rel="fixture/fixture-save.sav")
    ctx.log.info(f"read_test {read}")
    expect.equals("save size read in Lua", read.get("size"), FIXTURE_SAV.stat().st_size)
    expect.equals("save crc read in Lua", read.get("crc32"), saved)

    cmd("log_start")
    cmd("burst", n=20000)  # a log of about 0.6 MB
    folder = cmd("write_report_folder")
    ctx.log.info(f"report folder {folder}")
    expect.equals("report folder written", folder.get("exists"), True)

    sampler = LatencySampler(ctx)
    thread = threading.Thread(target=sampler.loop, daemon=True)
    thread.start()
    time.sleep(2.0)
    base = sampler.window(time.monotonic() - 2.0, time.monotonic())
    ctx.log.info(f"idle latency {base}")
    inv = Path(ctx.phase.state["appdata_dir"]) / "ManorLords" / "Saved" / "ProbeTelemetry"
    session = sorted((inv / "logs").glob("session-*.log"))[0]
    results = {"idle": base}
    for label, step_kb in (("one_go", 0), ("step_64kb", 64), ("step_256kb", 256), ("step_1024kb", 1024)):
        out = f"reports/probe-{label}.zip"
        (inv / "reports").mkdir(exist_ok=True)
        (inv / "reports" / "report.json").write_text('{"probe": true}')
        t0 = time.monotonic()
        answer = cmd("zip_start", out=out, save="fixture/fixture-save.sav", log="logs/" + session.name, report="reports/report.json", step_kb=step_kb)
        while not answer.get("done"):
            time.sleep(0.2)
            answer = cmd("zip_status")
        t1 = time.monotonic()
        window = sampler.window(t0, t1)
        zpath = inv / out
        ok = False
        with zipfile.ZipFile(zpath) as archive:
            ok = archive.testzip() is None and archive.read("save/saveGame_probe.sav") == FIXTURE_SAV.read_bytes() \
                and archive.read("session.log") == session.read_bytes()
        results[label] = {"wall_s": round(t1 - t0, 2), "lua_total_ms": round(answer.get("total_ms", -1)), "lua_max_tick_ms": round(answer.get("max_tick_ms", -1)),
                          "ticks": answer.get("ticks"), "zip_bytes": zpath.stat().st_size, "valid": ok, "bridge_latency": window}
        ctx.log.info(f"zip {label} {results[label]}")
        expect.equals(f"zip {label} opens and holds the same bytes", ok, True)
        time.sleep(1.0)
    sampler.stop = True
    ctx.notes.append(f"results {results}")
    return ctx.result()
