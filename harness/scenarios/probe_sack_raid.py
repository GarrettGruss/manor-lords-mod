"""Probe for change fix-sack-fire-and-goods (tasks 1.1 and 1.2): do sack fires make rubble while raiders are in the village?

Research tool. It records every answer in `probe.jsonl` and never fails on a game answer.
Choose a mode with --env HARNESS_PROBE:
  explore   list the properties of one villager and of one building (look for a flee or fire state)
  burn      light fires, watch the stores and the villagers in steps (HARNESS_RAIDERS=0 for no raiders, default 2 squads)
"""

import json
import os

from runlib import sack

NAME = "probe-sack-raid"
LIMIT_S = 400
HIDDEN = True
LONG_REASON = "The probe watches fires burn for up to 150 game seconds."
SPEED = 3
STEP_GAME_S = 5
BURN_COUNT = 2
MIN_WATCH_GAME_S = 30
BURN_LIMIT_GAME_S = 150
VILLAGER_SAMPLE = 12
CENTER = (-37635.0, -53829.0)   # where spawn_units puts raiders (the player pawn)
NEAR = 20000.0
PATTERN = "flee|alarm|scare|panic|fire|fight|task|action|state|behav|mode|run|afraid|danger|enemy|threat"


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


def object_ref(entry) -> str:
    text = entry["__object"] if isinstance(entry, dict) else entry
    return text.split(" ", 1)[1]


def villagers(probe, limit: int) -> list[str]:
    """Paths of SMUnit objects that have a family role (Husband 0 to Daughter 3)."""
    bridge = probe.ctx.bridge
    found = bridge._result("objects", class_name="SMUnit", limit=400)["objects"]
    out = []
    for entry in found:
        ref = object_ref(entry)
        try:
            role = bridge.read_property(ref, "currentUnitRole")
        except Exception:  # noqa: BLE001
            continue
        if role in (0, 1, 2, 3):
            try:
                at = bridge.read_property(ref, "realPos")
            except Exception:  # noqa: BLE001
                continue
            if ((at["X"] - CENTER[0]) ** 2 + (at["Y"] - CENTER[1]) ** 2) ** 0.5 < NEAR:
                out.append(ref)
        if len(out) >= limit:
            break
    return out


def explore(probe) -> None:
    bridge = probe.ctx.bridge
    probe.attempt("spawn raiders", lambda: probe.ctx.actions.spawn_units("bandit", "Brigands", 2, 0, 0))
    probe.ctx.time.run_game_seconds(STEP_GAME_S, speed=SPEED)
    refs = villagers(probe, 1)
    probe.note("villager refs", refs=refs)
    for pat in ("[Ff]lee", "[Aa]larm", "[Ff]ire", "[Ss]car", "[Pp]anic", "[Aa]fraid", "[Ee]nemy", "[Tt]hreat", "[Ff]ight", "[Ss]tate", "[Aa]ction", "[Tt]ask", "[Bb]ehav", "[Rr]un", "[Dd]anger"):
        if refs:
            probe.attempt(f"villager props {pat}", lambda pat=pat: bridge._result("props", ref=refs[0], include_super=True, read_soft=False, pattern=pat))
    region = bridge.player_region_path()
    probe.attempt("region fire props", lambda: bridge._result("props", ref=region, include_super=True, read_soft=False, pattern="[Ff]ire"))
    probe.attempt("player pawn props", lambda: bridge._result("props", ref=bridge.player_path(), include_super=True, read_soft=False,
                                                              pattern="[Aa]larm"))


def villager_rows(probe, refs: list[str]) -> list:
    bridge, rows = probe.ctx.bridge, []
    for ref in refs:
        row = {"ref": ref.rsplit(".", 1)[-1]}
        for name in ("dead", "currAnimAction", "fightingStance"):
            try:
                row[name] = bridge.read_property(ref, name)
            except Exception as error:  # noqa: BLE001
                row[name] = f"err {str(error)[:60]}"
        try:
            row["task_types"] = [task["Type"] for task in bridge.read_property(ref, "Tasks")]
            at = bridge.read_property(ref, "realPos")
            row["pos"] = [round(at["X"]), round(at["Y"])]
        except Exception as error:  # noqa: BLE001
            row["task_types"] = f"err {str(error)[:60]}"
        rows.append(row)
    return rows


def burn(probe) -> None:
    ctx = probe.ctx
    actions, bridge = ctx.actions, ctx.bridge
    squads = int(ctx.variant_option("HARNESS_RAIDERS", "2"))
    region = bridge.player_region_path()
    refs = villagers(probe, VILLAGER_SAMPLE)
    start = actions.sack_census()
    probe.note("start", buildings=start["buildings"], stock=start["stock"]["total"], stores=start["stores"], people=start["people"], refs=len(refs))
    probe.note("villagers at start", rows=villager_rows(probe, refs))
    probe.note("units before", census=actions.units_census(sample=3))
    if squads:
        probe.attempt("spawn raiders in the village", lambda: actions.spawn_units("bandit", "Brigands", squads, float(ctx.variant_option("HARNESS_RAIDER_DX", "0")), 0))
        ctx.time.run_game_seconds(STEP_GAME_S, speed=SPEED)
        census = actions.units_census(sample=4)
        probe.note("units with raiders", census=census)
    record = actions.sack_buildings(count=BURN_COUNT, method="fire")
    lit = actions.sack_census()
    probe.note("lit", ok=record["ok"], buildings=lit["buildings"], stores=lit["stores"], stock=lit["stock"]["total"])
    elapsed = 0
    done = None
    while elapsed < BURN_LIMIT_GAME_S:
        ctx.time.run_game_seconds(STEP_GAME_S, speed=SPEED)
        elapsed += STEP_GAME_S
        now = actions.sack_census()
        on_fire = bridge.read_property(region, "bAnyBuildingOnFire")
        probe.note(f"t+{elapsed}", buildings=now["buildings"], stock=now["stock"]["total"], store_goods={e["id"]: [e["type"], e["goods"]] for e in now["stores"]},
                   region_fire=on_fire, villagers=villager_rows(probe, refs), bandits=actions.units_census()["by_side"])
        ctx.popups()
        if sack.burning(now) == 0 and done is None:
            done = elapsed
        if done is not None and elapsed >= MIN_WATCH_GAME_S:
            break
    ctx.time.pause()
    end = actions.sack_census()
    probe.note("end", burn_game_s=done, buildings=end["buildings"], stock_before=start["stock"]["total"], stock_after=end["stock"]["total"],
               stores_before=start["stores"], stores_after=end["stores"], people=end["people"])


MODES = {"explore": explore, "burn": burn}


def run(ctx) -> dict:
    probe = Probe(ctx)
    mode = ctx.variant_option("HARNESS_PROBE", "burn")
    if mode not in MODES:
        raise ValueError(f"HARNESS_PROBE must be one of {sorted(MODES)}")
    probe.note("mode", mode=mode)
    MODES[mode](probe)
    return ctx.result()
