"""Probe for spec 31: add a burgage plot extension without the mouse and watch the artisan state and the stocks. Research tool, not a test.

Start the game with HARNESS_ALLOW_UNSAFE=1 only if you need the part commands. Every answer goes to `probe.jsonl`.
Choose the extension with HARNESS_PROBE_EXT (extension number, default 6 = tailor; 17 = the new weaver of spec 31).
HARNESS_PROBE_DAYS sets the watched game days (default 6). The probe never calls a save function.
"""

import json
import os

NAME = "probe-extension"
LIMIT_S = 420
HIDDEN = True
LONG_REASON = "The probe waits for builders to finish an extension and then watches the stocks for several game days."
GOODS = {"planks": 17, "wool": 23, "yarn": 148, "flax": 11, "linen": 12, "clothes": 149}
GIVE = {"planks": 40, "wool": 60, "yarn": 60, "flax": 60, "linen": 60}


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step: str, **data) -> None:
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")

    def attempt(self, step: str, work):
        try:
            result = work()
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            self.ctx.ensure_alive(step)
            self.note(step, error=str(error)[:500])
            return None
        self.note(step, result=result)
        return result


def stocks(ctx) -> dict:
    actions = ctx.actions
    path = actions._region(None)
    return {name: actions._bridge.call_function(path, "getStockOfGood", [item, False, False]) for name, item in GOODS.items()}


def plot_id(answer) -> int | None:
    name = (answer or {}).get("building") or ""
    digits = name.rsplit("_", 1)[-1]
    return int(digits) if digits.isdigit() else None


def snapshot(probe, label: str, plot: int | None) -> None:
    probe.attempt(f"{label} artisan", lambda: probe.ctx.actions.master_artisan(building=plot, type_id=None if plot else 3))
    probe.attempt(f"{label} stocks", lambda: stocks(probe.ctx))


def focus_extension(probe, plot: int | None, mesh_part: str, label: str) -> None:
    """Centre the camera on the first extension part whose mesh name has `mesh_part`, then take a screenshot."""
    answer = probe.attempt(f"{label} find part", lambda: probe.ctx.actions.master_parts(building=plot, limit=0, ext_limit=60))
    rows = [row for ext in (answer or {}).get("extensions", []) for row in ext.get("rows", []) if mesh_part in (row.get("mesh") or "")]
    if not rows:
        probe.note(f"{label} focus", found=False, mesh_part=mesh_part)
        return
    where = rows[0]
    probe.attempt(f"{label} camera", lambda: probe.ctx.actions._bridge.centre_camera_on(where["x"], where["y"]))
    bridge = probe.ctx.actions._bridge
    player = bridge.player_path()
    probe.attempt(f"{label} zoom read", lambda: bridge.read_property(player, "zoomLevel"))
    for level in [float(v) for v in os.environ.get("HARNESS_PROBE_ZOOMS", "").split(",") if v]:
        probe.attempt(f"{label} zoom {level}", lambda level=level: bridge.write_property(player, "zoomLevel", level))
        probe.attempt(f"{label} camera {level}", lambda: bridge.centre_camera_on(where["x"], where["y"]))
        probe.ctx.screenshot(f"{label}_z{level}")
    probe.ctx.screenshot(label)


def run(ctx) -> dict:
    probe = Probe(ctx)
    actions = ctx.actions
    extension = int(os.environ.get("HARNESS_PROBE_EXT", "6"))
    days = int(os.environ.get("HARNESS_PROBE_DAYS", "6"))
    build_days = int(os.environ.get("HARNESS_PROBE_BUILD_DAYS", "5"))
    job = os.environ.get("HARNESS_PROBE_JOB")
    do_artisan = os.environ.get("HARNESS_PROBE_ARTISAN", "1") == "1"
    if extension < 0:
        for kind in (3, 4, 18, 36, 14, 20, 72, 35, 42, 86, 89, 31, 69):
            probe.attempt(f"census type {kind}", lambda kind=kind: actions.master_artisan(type_id=kind))
            probe.attempt(f"census parts {kind}", lambda kind=kind: actions.master_parts(type_id=kind, limit=0, ext_limit=0))
        probe.attempt("stocks", lambda: stocks(ctx))
        return ctx.result()
    probe.note("config", extension=extension, days=days, build_days=build_days, job=job, artisan=do_artisan)
    probe.attempt("upgrade row", lambda: actions._command("upgrade_stat", type=100 + extension))
    probe.attempt("0 parts", lambda: actions.master_parts(type_id=3, limit=3, ext_limit=3))
    for name, amount in GIVE.items():
        probe.attempt(f"give {name}", lambda name=name, amount=amount: actions.give_item(GOODS[name], amount))
    ctx.screenshot("start")
    answer = probe.attempt("1 add extension", lambda: actions.plot_upgrade(extension, type_id=3, extension=True))
    plot = plot_id(answer)
    probe.note("plot", id=plot)
    snapshot(probe, "1 after request", plot)
    for day in range(1, build_days + 1):
        ctx.time.run_game_days(1, speed=3)
        snapshot(probe, f"build day {day}", plot)
    probe.attempt("1b parts", lambda: actions.master_parts(building=plot, limit=2, ext_limit=4))
    ctx.screenshot("extension_built")
    focus_part = os.environ.get("HARNESS_PROBE_FOCUS")
    if focus_part:
        focus_extension(probe, plot, focus_part, "focus_built")
    if do_artisan:
        probe.attempt("2 make artisan", lambda: actions.plot_upgrade(extension, type_id=3, artisan=True))
        snapshot(probe, "2 after artisan request", plot)
    for day in range(1, int(os.environ.get("HARNESS_PROBE_ARTISAN_DAYS", "4")) + 1):
        ctx.time.run_game_days(1, speed=3)
        snapshot(probe, f"artisan day {day}", plot)
    if os.environ.get("HARNESS_PROBE_LV"):
        probe.attempt("3a write lv", lambda: actions.master_artisan_set(building=plot, lv=int(os.environ["HARNESS_PROBE_LV"])))
    if job is not None:
        probe.attempt("3 write job", lambda: actions.master_artisan_set(building=plot, job=int(job)))
    for good in [int(g) for g in os.environ.get("HARNESS_PROBE_RECIPES", "").split(",") if g]:
        probe.attempt(f"4 enable recipe {good}", lambda good=good: actions.master_artisan_set(building=plot, enable_recipe=good))
        snapshot(probe, f"4 after recipe {good}", plot)
    for day in range(1, days + 1):
        ctx.time.run_game_days(1, speed=3)
        snapshot(probe, f"day {day}", plot)
    probe.attempt("end parts", lambda: actions.master_parts(building=plot, limit=2, ext_limit=12))
    ctx.screenshot("end")
    return ctx.result()
