"""Probe for spec 07: try each candidate action in the real game and record the state before and after.

This is a research tool, not a test. It never fails on a game answer: it writes every answer to
`probe.jsonl` in the run folder. Choose a group with the environment variable HARNESS_PROBE
(money, time, region, cheat, misc). Each group is one run, because a call may crash the game.
"""

import json
import os

from runlib.bridge_client import object_path

NAME = "probe-actions"
LIMIT_S = 120
HIDDEN = True


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.bridge = ctx.bridge
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step: str, **data) -> dict:
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:900]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")
        return entry

    def attempt(self, step: str, work) -> dict:
        """Run `work`. Record its result or its error. A game crash raises through ensure_alive."""
        self.ctx.log.info(f"PROBE start {step}")
        try:
            result = work()
            outcome = {"ok": True, "result": result}
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            self.ctx.ensure_alive(step)
            outcome = {"ok": False, "error": str(error)[:400]}
        return self.note(step, **outcome)

    def read(self, ref, names):
        return {name: self._safe_get(ref, name) for name in names}

    def _safe_get(self, ref, name):
        try:
            return self.bridge.read_property(ref, name)
        except Exception as error:  # noqa: BLE001
            return f"<error: {str(error)[:80]}>"


def _paths(bridge):
    engine = bridge.engine_path()
    return {
        "engine": engine,
        "player": bridge.player_path(),
        "calendar": bridge.calendar_path(engine),
    }


def _first_settled_region(bridge, engine):
    for ref in bridge.read_property(engine, "regions"):
        path = object_path(ref)
        if bridge.read_property(path, "isSettled"):
            return path
    raise RuntimeError("no settled region")


def _run_seconds(probe, seconds):
    return probe.ctx.time.run_game_seconds(seconds, speed=1)


# ---- groups ----

PLAYER_FIELDS = ["silver", "influence", "kingsFavour"]


def group_money(probe, paths):
    player, bridge = paths["player"], probe.bridge
    probe.note("start", values=probe.read(player, PLAYER_FIELDS + ["predictedIncome"]))
    steps = [
        ("changeSilver +100", "changeSilver", [100]),
        ("ChangeTreasury +100", "ChangeTreasury", [100]),
        ("changeSilver -50", "changeSilver", [-50]),
        ("changeInfluence +10", "changeInfluence", [10.0]),
        ("changeKingsFavour +5", "changeKingsFavour", [5]),
    ]
    for step, function, args in steps:
        probe.attempt(step, lambda f=function, a=args: bridge.call_function(player, f, a))
        probe.note(f"after {step}", values=probe.read(player, PLAYER_FIELDS))
    for name, value in (("silver", 500), ("influence", 50)):
        probe.attempt(f"set {name}={value}", lambda n=name, v=value: bridge._result("set", ref=player, name=n, value=v))
        probe.note(f"after set {name}", values=probe.read(player, PLAYER_FIELDS))
    probe.attempt("run 6 s", lambda: _run_seconds(probe, 6))
    probe.note("after 6 s running", values=probe.read(player, PLAYER_FIELDS + ["predictedIncome"]))


def group_time(probe, paths):
    engine, calendar, bridge = paths["engine"], paths["calendar"], probe.bridge
    names = ["day", "month", "Year", "Season", "daysTotal", "dayOfTheMonth", "isWinter"]
    probe.note("start", calendar=probe.read(calendar, names), engine=probe.read(engine, ["gameSpeed"]))
    for day in (10, 100, 200, 300):
        probe.attempt(f"setDay({day})", lambda d=day: bridge.call_function(engine, "setDay", [d]))
        probe.note(f"after setDay({day})", calendar=probe.read(calendar, names))
    probe.attempt("run 6 s", lambda: _run_seconds(probe, 6))
    probe.note("after 6 s running", calendar=probe.read(calendar, names))
    probe.attempt("set Season=3", lambda: bridge._result("set", ref=calendar, name="Season", value=3))
    probe.note("after set Season=3", calendar=probe.read(calendar, names))
    probe.attempt("UpdateDateAndSeason", lambda: bridge.call_function(calendar, "UpdateDateAndSeason"))
    probe.note("after UpdateDateAndSeason", calendar=probe.read(calendar, names))
    weather = ["wind", "raining", "snowing", "snowLevel", "isDrought", "droughtLevel", "fogLevel", "daysUntilNextRaid"]
    probe.note("weather start", values=probe.read(calendar, weather))
    probe.attempt("setWeatherSpeed(5)", lambda: bridge.call_function(calendar, "setWeatherSpeed", [5.0]))
    probe.attempt("set raining=true", lambda: bridge._result("set", ref=calendar, name="raining", value=True))
    probe.note("weather after", values=probe.read(calendar, weather))
    probe.attempt("run 6 s", lambda: _run_seconds(probe, 6))
    probe.note("weather after 6 s", values=probe.read(calendar, weather))
    probe.attempt("engine setGameSpeed(3)", lambda: bridge.call_function(engine, "setGameSpeed", [3.0]))
    probe.note("after engine setGameSpeed(3)", gameSpeed=probe.read(engine, ["gameSpeed"]), clock=bridge.measure_clock(3.0))
    probe.attempt("pause", lambda: probe.ctx.time.pause())


REGION_FIELDS = ["Approval", "publicOrder", "regionalWealth", "supplies_food", "settlementLevel"]


def group_region(probe, paths):
    bridge = probe.bridge
    region = _first_settled_region(bridge, paths["engine"])
    probe.note("region", path=region, values=probe.read(region, REGION_FIELDS + ["regionName"]))
    for name, value in (("Approval", 77), ("publicOrder", 33), ("regionalWealth", 123), ("supplies_food", 55.0)):
        probe.attempt(f"set {name}={value}", lambda n=name, v=value: bridge._result("set", ref=region, name=n, value=v))
    probe.note("after sets", values=probe.read(region, REGION_FIELDS))
    probe.attempt("addRegionalWealth(+25)", lambda: bridge.call_function(region, "addRegionalWealth", [25]))
    probe.note("after addRegionalWealth", values=probe.read(region, REGION_FIELDS))
    probe.attempt("run 6 s", lambda: _run_seconds(probe, 6))
    probe.note("after 6 s running", values=probe.read(region, REGION_FIELDS))
    probe.attempt("run 40 s (one day)", lambda: _run_seconds(probe, 40))
    probe.note("after one more day", values=probe.read(region, REGION_FIELDS))


def group_cheat(probe, paths):
    bridge = probe.bridge
    probe.attempt("FindAllOf MLCheatManager", lambda: bridge._result("objects", class_name="MLCheatManager", limit=5))
    probe.attempt("PlayerController.CheatManager", lambda: bridge.read_property("first:PlayerController", "CheatManager"))
    probe.attempt("console EnableCheats", lambda: bridge._result("console", command="EnableCheats"))
    probe.attempt("FindAllOf MLCheatManager again", lambda: bridge._result("objects", class_name="MLCheatManager", limit=5))
    probe.attempt("PlayerController.CheatManager again", lambda: bridge.read_property("first:PlayerController", "CheatManager"))
    before = probe.read(paths["player"], PLAYER_FIELDS)
    probe.attempt("console ChangeTreasury 77", lambda: bridge._result("console", command="ChangeTreasury 77"))
    probe.note("silver after console ChangeTreasury", before=before, after=probe.read(paths["player"], PLAYER_FIELDS))


def group_misc(probe, paths):
    bridge, player = probe.bridge, paths["player"]
    for box in ("InBox", "outbox"):
        probe.attempt(f"read {box}", lambda b=box: str(bridge.read_property(player, b))[:600])
    # requestSaveFile is NOT probed again. It wrote into the user's real save folder (catalog: save_state).
    probe.attempt("sendLetter to self (object arg as path)",
                  lambda: bridge.call_function(player, "sendLetter", [player, ["probe"]]))


def group_world(probe, paths):
    bridge = probe.bridge
    probe.attempt("spawnBanditCamp", lambda: bridge.call_function(paths["engine"], "spawnBanditCamp"))
    probe.attempt("run 3 s", lambda: _run_seconds(probe, 3))


def _player_region(bridge, player):
    return object_path(bridge.read_property(player, "currentRegion"))


def group_cheat2(probe, paths):
    bridge, player = probe.bridge, paths["player"]
    manager = "first:MLCheatManager"
    region = _player_region(bridge, player)
    probe.note("player region", path=region, name=probe._safe_get(region, "regionName"))
    probe.attempt("set silver 100", lambda: bridge._result("set", ref=player, name="silver", value=100))
    probe.attempt("manager.ChangeTreasury(50)", lambda: bridge.call_function(manager, "ChangeTreasury", [50]))
    probe.note("silver after manager.ChangeTreasury(50)", values=probe.read(player, PLAYER_FIELDS))
    library = "cdo:/Script/ManorLords.MLBlueprintFunctionLibrary"
    names = {}
    for item in range(0, 40):
        try:
            names[item] = bridge.call_function(library, "TypeToName", [item])
        except Exception as error:  # noqa: BLE001
            names[item] = f"<error {str(error)[:60]}>"
            break
    probe.note("TypeToName", names=names)
    stock = lambda item: bridge.call_function(region, "getStockOfGood", [item, False, False])  # noqa: E731
    probe.attempt("stock of item 1 before", lambda: stock(1))
    probe.attempt("manager.GiveItemByID(1, 40)", lambda: bridge.call_function(manager, "GiveItemByID", [1, 40]))
    probe.attempt("stock of item 1 after GiveItemByID", lambda: stock(1))
    first_name = next((n for n in names.values() if isinstance(n, str) and n and not n.startswith("<")), "")
    probe.attempt(f"manager.GiveItemByName({first_name!r}, 25)", lambda: bridge.call_function(manager, "GiveItemByName", [first_name, 25]))
    probe.attempt("stock of item 1 after GiveItemByName", lambda: stock(1))
    probe.attempt("console GiveItemByName", lambda: bridge._result("console", command=f"GiveItemByName {first_name} 10"))
    probe.attempt("stock of item 1 after console", lambda: stock(1))
    calendar = paths["calendar"]
    probe.note("rain before", values=probe.read(calendar, ["raining", "wind", "snowing"]))
    probe.attempt("manager.RainNow", lambda: bridge.call_function(manager, "RainNow"))
    probe.attempt("run 3 s", lambda: _run_seconds(probe, 3))
    probe.note("rain after 3 s", values=probe.read(calendar, ["raining", "wind", "snowing"]))
    probe.attempt("run 10 s", lambda: _run_seconds(probe, 10))
    probe.note("rain after 13 s", values=probe.read(calendar, ["raining", "wind", "snowing"]))
    probe.note("level before", values=probe.read(region, ["settlementLevel", "tier"]))
    probe.attempt("manager.SetSettlementLevel(1)", lambda: bridge.call_function(manager, "SetSettlementLevel", [1]))
    probe.note("level after", values=probe.read(region, ["settlementLevel", "tier"]))


def _count(bridge, class_name):
    return bridge._result("objects", class_name=class_name, limit=1)["count"]


def group_cheat3(probe, paths):
    bridge, player = probe.bridge, paths["player"]
    manager = "first:MLCheatManager"
    region = _player_region(bridge, player)
    watched = lambda: {"SMUnit": _count(bridge, "SMUnit"), "PawnCPP": _count(bridge, "PawnCPP"),  # noqa: E731
                       "pop": bridge.call_function(region, "getNumTotalPopulation"),
                       "families": bridge.call_function(region, "getTotalNumFamilies")}
    probe.attempt("counts before", watched)
    probe.attempt("manager.SpawnBanditSquad", lambda: bridge.call_function(manager, "SpawnBanditSquad"))
    probe.attempt("counts after SpawnBanditSquad", watched)
    probe.attempt("manager.SpawnRaidersOfType('')", lambda: bridge.call_function(manager, "SpawnRaidersOfType", ["Bandit"]))
    probe.attempt("counts after SpawnRaidersOfType", watched)
    probe.attempt("run 5 s", lambda: _run_seconds(probe, 5))
    probe.attempt("counts after 5 s", watched)
    probe.attempt("manager.RemoveAllFamilies", lambda: bridge.call_function(manager, "RemoveAllFamilies"))
    probe.attempt("counts after RemoveAllFamilies", watched)


def group_weather(probe, paths):
    bridge, calendar = probe.bridge, paths["calendar"]
    names = ["wind", "raining", "snowing", "snowLevel", "isDrought", "droughtLevel", "fogLevel"]
    probe.note("start", values=probe.read(calendar, names))
    for name, value in (("raining", 1.0), ("snowing", 1.0), ("fogLevel", 0.8), ("droughtLevel", 0.5), ("wind", 0.9)):
        probe.attempt(f"set {name}={value}", lambda n=name, v=value: bridge._result("set", ref=calendar, name=n, value=v))
    probe.note("after sets", values=probe.read(calendar, names))
    probe.attempt("run 6 s", lambda: _run_seconds(probe, 6))
    probe.note("after 6 s", values=probe.read(calendar, names))


def group_items(probe, paths):
    bridge, engine = probe.bridge, paths["engine"]
    library = "cdo:/Script/ManorLords.MLBlueprintFunctionLibrary"
    probe.attempt("TypeToStr(1)", lambda: bridge.call_function(library, "TypeToStr", [1]))
    probe.attempt("getItem(1)", lambda: str(bridge.call_function(engine, "getItem", [1]))[:700])
    probe.attempt("getItem(5)", lambda: str(bridge.call_function(engine, "getItem", [5]))[:700])
    probe.attempt("itemStats", lambda: str(bridge.read_property(engine, "itemStats"))[:500])
    probe.attempt("props of Item struct names", lambda: str(bridge._result("props", ref="first:RTSMultiEngineCPP", pattern="item"))[:900])


def group_names(probe, paths):
    bridge = probe.bridge
    manager = "first:MLCheatManager"
    region = _player_region(bridge, paths["player"])
    stock = lambda: {i: v for i in range(0, 80) if (v := bridge.call_function(region, "getStockOfGood", [i, False, False]))}  # noqa: E731
    probe.attempt("stock before", stock)
    for name in ("Wood", "Timber", "Log", "Logs", "Bread", "Firewood", "Stone", "Planks", "Iron", "Wheat", "Meat", "Fish", "Berries"):
        before = stock()
        probe.attempt(f"GiveItemByName({name}, 7)", lambda n=name: bridge.call_function(manager, "GiveItemByName", [n, 7]))
        after = stock()
        probe.note(f"diff after {name}", diff={k: [before.get(k, 0), v] for k, v in after.items() if before.get(k, 0) != v})
    probe.attempt("DT_Items props", lambda: str(bridge._result("props", ref="/Game/NotStronghold/Data/DT_Items.DT_Items"))[:600])


def group_message(probe, paths):
    bridge, player = probe.bridge, paths["player"]
    probe.attempt("playEventMessage", lambda: bridge.call_function(player, "playEventMessage", ["Default", "Probe title", "Probe text"]))


def group_hud(probe, paths):
    bridge, player = probe.bridge, paths["player"]
    probe.attempt("lord panels", lambda: bridge._result("objects", class_name="W_HUD_LordPanel_V2_C", limit=5))
    panels = bridge._result("objects", class_name="W_HUD_LordPanel_V2_C", limit=5)["objects"]
    panel = next(object_path(p) for p in panels if " /Engine/Transient" in p)
    probe.attempt("TreasuryNumeric", lambda: bridge.read_property(panel, "TreasuryNumeric"))
    numeric = object_path(bridge.read_property(panel, "TreasuryNumeric"))
    probe.attempt("numeric props", lambda: str(bridge._result("props", ref=numeric, include_super=True, pattern="[Vv]alue|Text"))[:1500])
    for fn in ("GetCurrentValue", "GetText", "GetTargetValue"):
        probe.attempt(f"numeric.{fn}", lambda f=fn: str(bridge.call_function(numeric, f))[:200])
    probe.attempt("add 100", lambda: bridge.call_function(player, "changeSilver", [100]))
    probe.attempt("run 3 s", lambda: _run_seconds(probe, 3))
    for fn in ("GetCurrentValue", "GetText", "GetTargetValue"):
        probe.attempt(f"after numeric.{fn}", lambda f=fn: str(bridge.call_function(numeric, f))[:200])
    probe.note("silver", values=probe.read(player, PLAYER_FIELDS))


def group_mail(probe, paths):
    bridge, player = probe.bridge, paths["player"]
    probe.attempt("pawns", lambda: bridge._result("objects", class_name="PawnCPP", limit=10))
    probe.attempt("InBox before", lambda: str(bridge.read_property(player, "InBox"))[:500])
    probe.attempt("run 45 s", lambda: _run_seconds(probe, 45))
    probe.attempt("InBox after", lambda: str(bridge.read_property(player, "InBox"))[:900])
    probe.attempt("outbox after", lambda: str(bridge.read_property(player, "outbox"))[:300])


def group_helper(probe, paths):
    from runlib.commands import CommandChannel
    bridge, player = probe.bridge, paths["player"]
    channel = CommandChannel(probe.ctx.run_dir / "commands", check_alive=probe.ctx.ensure_alive)
    probe.attempt("ping", lambda: channel.send("ping"))
    probe.attempt("InBox before", lambda: str(bridge.read_property(player, "InBox"))[:300])
    probe.attempt("send_letter bad sender", lambda: channel.send("send_letter", sender=99, paragraphs=["welcome_from_hildebolt"]))
    probe.attempt("send_letter", lambda: channel.send("send_letter", sender=1, paragraphs=["welcome_from_hildebolt"]))
    probe.attempt("InBox after", lambda: str(bridge.read_property(player, "InBox"))[:1200])
    probe.attempt("outboxes", lambda: [str(bridge.read_property(player, "outbox"))[:200]])


GROUPS = {"money": group_money, "time": group_time, "region": group_region, "cheat": group_cheat,
          "misc": group_misc, "world": group_world, "cheat2": group_cheat2,
          "cheat3": group_cheat3, "weather": group_weather, "items": group_items, "names": group_names, "message": group_message, "hud": group_hud, "mail": group_mail, "helper": group_helper}


def run(ctx) -> dict:
    group = os.environ.get("HARNESS_PROBE", "money")
    probe = Probe(ctx)
    probe.note("group", name=group)
    GROUPS[group](probe, _paths(ctx.bridge))
    ctx.check("probe finished", True, group)
    return ctx.result()
