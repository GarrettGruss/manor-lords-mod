"""Actions for scenarios (spec 07): create a game situation, then check that it happened.

Every action does four things: check that the game is loaded, read the state, make the change, read the state again.
It returns {"action", "ok", "args", "before", "after"} and adds a short line to the scenario notes.
A failed read-back also adds a failed assertion, so the scenario verdict is `fail`.

Only actions that were checked in the real game are here (docs/specs/07-feature-test-kit/implementation-notes/actions-catalog.md).
A name in NOT_POSSIBLE, or an unknown name, raises ActionNotPossible with the reason. The runner turns that into a failed scenario.

Call actions while the game is paused. A running game changes silver and stock by itself, and then an exact read-back can fail.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .bridge_client import Bridge
from .commands import CommandChannel
from . import battle, sack
from .units import ELITE_RAID_UNITS, SQUAD_UNITS, side_count

CHEAT_MANAGER = "first:MLCheatManager"
# Mid-season days. The calendar maps day of the year to the season (measured: 10 winter, 100 spring, 200 summer, 300 autumn).
SEASON_DAY = {"winter": 10, "spring": 100, "summer": 200, "autumn": 300}
SEASON_ID = {"winter": 0, "spring": 1, "summer": 2, "autumn": 3}
# Region properties that took a written value in the real game.
REGION_VALUES = {"Approval": int, "publicOrder": int, "regionalWealth": int, "supplies_food": float}
REGION_VALUE_NOTES = {"supplies_food": "the game recalculates supplies_food at the next day tick"}
WEATHER_VALUES = ("raining", "snowing", "fogLevel", "droughtLevel", "wind")
WEATHER_NOTE = "the game moves the weather back toward its own target within seconds"
# Item ids whose names were checked with GiveItemByName (Timber -> 16, Planks -> 17, Fish -> 30).
ITEM_IDS = {"timber": 16, "planks": 17, "fish": 30}
# Letter paragraphs that were sent in the real game. Other names may be missing in the game data.
LETTER_PARAGRAPHS = ("welcome_from_hildebolt",)
DEFAULT_PLACE_FX = 0.65  # open meadow right of the start camp; the middle (0.5, 0.7) overlaps a building site in some starts
DEFAULT_PLACE_FY = 0.65
FLOAT_TOLERANCE = 0.01  # property floats are 32 bit
MAX_NOTE_CHARS = 140
DATATABLES = ("items", "units")
# The banner text goes into the game as a string. The mod checks the same rules (mod/shared/HarnessUi).
BANNER_TEXT_PATTERN = re.compile(r"^[A-Za-z0-9 ,.!:\-]+$")
MAX_BANNER_TEXT = 60
MAX_BANNER_SUBTEXT = 80
MAX_BUILDING_TYPE = 300  # same limits as mod/shared/HarnessBuild
MAX_GOOD_ID = 200
MAX_REBEL_FAMILIES = 6  # same limit as the Lua module HarnessBandits
MAX_REBEL_SQUADS = 6
MAX_TURN_UNITS = 20
MAX_KILL_SQUADS = 10  # same limit as the Lua module HarnessBandits
REBEL_WAYPOINT = (-31000, -22500)  # where the Outlaws AI sends new squads on fixture base (spec 15, runs s15-h*, s15-w*)
TENT_TYPE = 87  # EBuildingType homeless_tents (buildingStats row 87)
BANDIT_TAGS = ("attacking", "acquainted", "at_war")
MAX_SETTLE_SILVER = 999999
WALL_TYPES = (2, 3, 4)  # wooden, stone low, stone high (a fence, 1, gets no mesh)
RUIN_METHODS = ("fire", "collapse")
MAX_MANOR_AMOUNT = 1000  # same limits as mod/shared/HarnessManor
MAX_WORKER_SLOTS = 6  # same limit as mod/shared/HarnessManor
STORAGE_JOBS = (44, 45)  # EJobType: GranaryWorker, WarehouseWorker

NOT_POSSIBLE = {
    "save_state": "PawnCPP:requestSaveFile writes into the user's real save folder, even when the run has a private LOCALAPPDATA. "
                  "It overwrote the user's saveGame_9 in the probe. Make fixtures with harness/tools/fixtures.py instead.",
    "get_item_info": "RTSMultiEngineCPP:getItem crashed the game when called through the bridge (spec 07 catalog).",
    "remove_all_families": "MLCheatManager:RemoveAllFamilies changed no population or family count in the probe.",
    "spawn_raiders": "MLCheatManager:SpawnRaidersOfType changed no unit count (checked again in spec 10). Use spawn_raid.",
    "choose_raid_type": "spawnRaiders and spawnEliteRaiders take no type or size: a squad is always 18 units. The raid id lists "
                        "(RaidSettings.defaultRaidIDs) were read but not written (spec 10, spike S2). To get a chosen unit type on a side, use spawn_units (spike S7).",
    "steer_squad": "no way to order a spawned squad was verified (spec 10).",
}


class ActionNotPossible(Exception):
    """The action is unknown or was found not possible. The message says why."""


class ActionError(Exception):
    """A precondition failed, for example the game world is not loaded."""


# ---- checks: pure functions, tested without a game ----

def changed_by(expected: float) -> Callable[[float, float], bool]:
    return lambda before, after: after - before == expected


def equals(expected: Any) -> Callable[[Any, Any], bool]:
    return lambda before, after: after == expected


def near(expected: float) -> Callable[[float, float], bool]:
    return lambda before, after: after is not None and abs(after - expected) <= FLOAT_TOLERANCE


def increased(before: float, after: float) -> bool:
    return after > before


def season_day(name: str) -> int:
    if name not in SEASON_DAY:
        raise ActionNotPossible(f"unknown season {name!r}. Use one of {sorted(SEASON_DAY)}.")
    return SEASON_DAY[name]


def item_id(item: int | str) -> int:
    if isinstance(item, int) and not isinstance(item, bool):
        return item
    key = str(item).lower()
    if key not in ITEM_IDS:
        raise ActionNotPossible(f"item name {item!r} was not checked. Use an item id, or one of {sorted(ITEM_IDS)}.")
    return ITEM_IDS[key]


class Actions:
    """`ensure_alive` raises when the game process ended. `expect` is an Expectations object. `notes` is a list."""

    def __init__(self, bridge: Bridge, expect=None, notes: list[str] | None = None,
                 log: Callable[[str], None] = lambda message: None,
                 ensure_alive: Callable[[], None] = lambda: None, commands: CommandChannel | None = None,
                 mouse_placer: Callable[[int, float, float], None] | None = None):
        self._bridge = bridge
        self._commands = commands
        self._mouse_placer = mouse_placer
        self._expect = expect
        self._notes = notes if notes is not None else []
        self._log = log
        self._ensure_alive = ensure_alive
        self.records: list[dict] = []

    # ---- dispatch ----

    def run(self, name: str, *args, **kwargs) -> dict:
        """Run an action by name. Unknown and not-possible names raise ActionNotPossible."""
        if name.startswith("_"):
            raise ActionNotPossible(f"{name}: not an action")
        return getattr(self, name)(*args, **kwargs)

    def available(self) -> list[str]:
        return sorted(name for name in dir(type(self)) if not name.startswith("_") and name not in ("run", "available"))

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in NOT_POSSIBLE:
            raise ActionNotPossible(f"{name}: {NOT_POSSIBLE[name]}")
        raise ActionNotPossible(f"{name}: unknown action. Available: {self.available()}")

    # ---- the common steps ----

    def _precondition(self) -> None:
        self._ensure_alive()
        try:
            self._bridge.engine_path()
        except RuntimeError as error:
            raise ActionError(f"the game world is not loaded: {error}") from error

    def _perform(self, action: str, args: dict, read: Callable[[], Any], call: Callable[[], Any],
                 check: Callable[[Any, Any], bool], note: str = "") -> dict:
        self._precondition()
        before = read()
        call()
        after = read()
        return self._record(action, args, check(before, after), before, after, note)

    def _record(self, action: str, args: dict, ok: bool, before: Any, after: Any, note: str = "") -> dict:
        record = {"action": action, "ok": bool(ok), "args": args, "before": before, "after": after}
        if note:
            record["note"] = note
        self.records.append(record)
        self._log(f"action {record}")
        line = f"{action}{args or ''}: {before} -> {after} {'ok' if ok else 'FAILED'}"
        self._notes.append(line[:MAX_NOTE_CHARS])
        if not ok and self._expect is not None:
            self._expect.record(f"action {action} read-back", False, f"{before} -> {after}", f"args {args}")
        return record

    # ---- player values ----

    def _player_value(self, name: str) -> Callable[[], Any]:
        return lambda: self._bridge.read_property(self._bridge.player_path(), name)

    def _on_player(self, function: str, amount: Any) -> Callable[[], Any]:
        return lambda: self._bridge.call_function(self._bridge.player_path(), function, [amount])

    def _set_player(self, name: str, value: Any) -> Callable[[], Any]:
        return lambda: self._bridge.write_property(self._bridge.player_path(), name, value)

    def add_silver(self, amount: int) -> dict:
        """Add (or take, with a negative number) silver. Verified: +100, +100, -50 gave 100, 200, 150."""
        return self._perform("add_silver", {"amount": amount}, self._player_value("silver"),
                             self._on_player("changeSilver", amount), changed_by(amount))

    def set_silver(self, amount: int) -> dict:
        """Set the silver. Verified: 150 -> 500, and the value held for 6 game seconds."""
        return self._perform("set_silver", {"amount": amount}, self._player_value("silver"),
                             self._set_player("silver", amount), equals(amount))

    def add_influence(self, amount: int) -> dict:
        """Add influence. Verified: +10 gave 10. The game function takes a float; the property is an integer."""
        return self._perform("add_influence", {"amount": amount}, self._player_value("influence"),
                             self._on_player("changeInfluence", float(amount)), changed_by(amount))

    def set_influence(self, amount: int) -> dict:
        return self._perform("set_influence", {"amount": amount}, self._player_value("influence"),
                             self._set_player("influence", amount), equals(amount))

    def add_kings_favour(self, amount: int) -> dict:
        return self._perform("add_kings_favour", {"amount": amount}, self._player_value("kingsFavour"),
                             self._on_player("changeKingsFavour", amount), changed_by(amount))

    # ---- calendar ----

    def _calendar_read(self, *names: str) -> Callable[[], dict]:
        def read() -> dict:
            calendar = self._bridge.calendar_path()
            return {name: self._bridge.read_property(calendar, name) for name in names}
        return read

    def set_day(self, day: int) -> dict:
        """Set the day of the year (1 to 365). The month and the season follow. `daysTotal` grows by 1 for each call."""
        read = self._calendar_read("day", "Season")
        call = lambda: self._bridge.call_function(self._bridge.engine_path(), "setDay", [day])  # noqa: E731
        return self._perform("set_day", {"day": day}, read, call, lambda before, after: after["day"] == day,
                             note="daysTotal grows by 1 for each setDay call")

    def set_season(self, name: str) -> dict:
        """Jump to the middle of a season: winter, spring, summer or autumn. Checks the Season value of the calendar."""
        day = season_day(name)
        read = self._calendar_read("day", "Season")
        call = lambda: self._bridge.call_function(self._bridge.engine_path(), "setDay", [day])  # noqa: E731
        check = lambda before, after: after["day"] == day and after["Season"] == SEASON_ID[name]  # noqa: E731
        return self._perform("set_season", {"season": name}, read, call, check,
                             note="only the calendar was checked, not the look of the world")

    # ---- regions ----

    def _region(self, region: str | None) -> str:
        """None or "player": the region of the player. Otherwise the `regionName` of a region."""
        if region in (None, "player"):
            return self._bridge.player_region_path()
        for path in self._bridge.region_paths():
            if self._bridge.read_property(path, "regionName") == region:
                return path
        raise ActionError(f"no region named {region!r}")

    def set_region_value(self, name: str, value: float, region: str | None = None) -> dict:
        """Set Approval, publicOrder, regionalWealth or supplies_food. The read-back is immediate.

        Approval, publicOrder and regionalWealth held for one game day in the probe. supplies_food did not.
        """
        if name not in REGION_VALUES:
            raise ActionNotPossible(f"set_region_value: {name!r} was not checked. Use one of {sorted(REGION_VALUES)}.")
        path = self._region(region)
        value = REGION_VALUES[name](value)
        check = near(value) if REGION_VALUES[name] is float else equals(value)
        return self._perform("set_region_value", {"name": name, "value": value, "region": region or "player"},
                             lambda: self._bridge.read_property(path, name),
                             lambda: self._bridge.write_property(path, name, value), check,
                             note=REGION_VALUE_NOTES.get(name, ""))

    def add_regional_wealth(self, amount: int, region: str | None = None) -> dict:
        path = self._region(region)
        return self._perform("add_regional_wealth", {"amount": amount, "region": region or "player"},
                             lambda: self._bridge.read_property(path, "regionalWealth"),
                             lambda: self._bridge.call_function(path, "addRegionalWealth", [amount]), changed_by(amount))

    def set_settlement_level(self, level: int, region: str | None = None) -> dict:
        """Verified for level 1 in the region of the player (0 -> 1), through the cheat manager."""
        path = self._region(region)
        return self._perform("set_settlement_level", {"level": level, "region": region or "player"},
                             lambda: self._bridge.read_property(path, "settlementLevel"),
                             lambda: self._bridge.call_function(CHEAT_MANAGER, "SetSettlementLevel", [level]), equals(level))

    # ---- goods and weather ----

    def give_item(self, item: int | str, amount: int) -> dict:
        """Add goods to the stock of the player region (cheat manager GiveItemByID). Checked with the stock of that region."""
        item_number = item_id(item)
        path = self._region(None)
        stock = lambda: self._bridge.call_function(path, "getStockOfGood", [item_number, False, False])  # noqa: E731
        call = lambda: self._bridge.call_function(CHEAT_MANAGER, "GiveItemByID", [item_number, amount])  # noqa: E731
        return self._perform("give_item", {"item": item, "item_id": item_number, "amount": amount}, stock, call, changed_by(amount))

    def set_weather(self, name: str, value: float) -> dict:
        """Write a weather value of the calendar (raining, snowing, fogLevel, droughtLevel, wind). The read-back is immediate."""
        if name not in WEATHER_VALUES:
            raise ActionNotPossible(f"set_weather: {name!r} was not checked. Use one of {list(WEATHER_VALUES)}.")
        read = lambda: self._bridge.read_property(self._bridge.calendar_path(), name)  # noqa: E731
        call = lambda: self._bridge.write_property(self._bridge.calendar_path(), name, float(value))  # noqa: E731
        return self._perform("set_weather", {"name": name, "value": value}, read, call, near(float(value)), note=WEATHER_NOTE)

    def spawn_bandit_squad(self) -> dict:
        """Spawn one bandit squad (cheat manager). Checked with the number of SMUnit objects (+18 in the probe)."""
        return self._perform("spawn_bandit_squad", {}, lambda: self._bridge.count_objects("SMUnit"),
                             lambda: self._bridge.call_function(CHEAT_MANAGER, "SpawnBanditSquad"), increased)

    # ---- buildings (real OS mouse) ----

    def place_building(self, type_id: int, fx: float = DEFAULT_PLACE_FX, fy: float = DEFAULT_PLACE_FY) -> dict:
        """Place a building of `type_id` with a REAL left click at a fraction (fx, fy) of the game window.

        WARNING: this uses the OS mouse and the keyboard focus. Do not use it while a person works on this computer.
        The game window comes to the front, the cursor moves over it, and the cursor goes back afterwards.
        The player needs the goods of the building (HitchingPost 30 is free). A blocked spot places nothing and fails the read-back.
        Checked with the number of buildings of this type in the player region (+1).
        """
        if self._mouse_placer is None:
            raise ActionNotPossible("place_building: no OS mouse input in this context")
        path = self._region(None)
        count = lambda: self._bridge.call_function(path, "getBuildingCount", [type_id, False])  # noqa: E731
        call = lambda: self._mouse_placer(type_id, fx, fy)  # noqa: E731
        return self._perform("place_building", {"type_id": type_id, "fx": fx, "fy": fy}, count, call, changed_by(1),
                             note="uses the OS mouse and keyboard focus")

    # ---- letters (through the helper mod HarnessActions, because sendLetter needs object parameters) ----

    def _inbox_state(self) -> dict:
        inbox = self._bridge.read_property(self._bridge.player_path(), "InBox")
        return {"count": len(inbox), "last": inbox[-1]["paras"] if inbox else None}

    def send_letter(self, paragraphs: list[str], sender: int = 1) -> dict:
        """An AI lord (number `sender`, from 1) sends a letter to the player. Checked with the InBox of the player."""
        unknown = [name for name in paragraphs if name not in LETTER_PARAGRAPHS]
        if unknown:
            raise ActionNotPossible(f"send_letter: paragraph {unknown} was not checked. Use {list(LETTER_PARAGRAPHS)}.")
        if self._commands is None:
            raise ActionNotPossible("send_letter: no command channel to the mod HarnessActions in this context")
        call = lambda: self._commands.send("send_letter", sender=sender, paragraphs=list(paragraphs))  # noqa: E731
        check = lambda before, after: after["count"] == before["count"] + 1 and after["last"] == list(paragraphs)  # noqa: E731
        return self._perform("send_letter", {"paragraphs": list(paragraphs), "sender": sender}, self._inbox_state, call, check)

    # ---- data tables (spec 09 item table, spec 10 spike S7 unit table; through the helper mod HarnessActions) ----

    @staticmethod
    def _table_fields(table: str) -> dict:
        if table not in DATATABLES:
            raise ActionNotPossible(f"datatable: unknown table {table!r}. Use one of {list(DATATABLES)}.")
        return {} if table == "items" else {"table": table}

    def datatable_info(self, table: str = "items") -> dict:
        """Row count, the first row names and the row struct of a table ("items" = `itemStats`, "units" = DT_UnitTemplates). It changes nothing."""
        return self._send_datatable("datatable_info", **self._table_fields(table))["info"]

    def datatable_read(self, row: str | int, field: str, table: str = "items") -> float:
        """Read one number field of one row. Items: Weight, Value, spoilageRate. Units: cost, maxSize, minMeleeTraining, minArcheryTraining,
        minHouseLv, combatExperience. It changes nothing."""
        answer = self._send_datatable("datatable_read", row=str(row), field=field, **self._table_fields(table))
        return answer["values"][field]

    def datatable_rows(self, table: str = "units") -> list[dict]:
        """Every row with every allowed number field: [{"row", "values": {field: number}}]. Separator rows ("-----") are left out. Read only."""
        return self._send_datatable("datatable_rows", **self._table_fields(table))["rows"]

    def datatable_write(self, row: str, field: str, value: float, table: str = "units") -> dict:
        """Write one number field of one row in memory and read it back. Verified for units: maxSize 32 -> 12 changed the size of the next
        spawned squad (spike S7). The change lasts until the game ends or the value is written again: restore it at the end of a scenario."""
        fields = {"row": str(row), "field": field, "value": value, **self._table_fields(table)}
        answer = self._send_datatable("datatable_write", **fields)
        change = answer["change"]
        return self._record("datatable_write", {"table": table, "row": str(row), "field": field, "value": value},
                            change["after"] is not None and abs(change["after"] - value) <= FLOAT_TOLERANCE, change["before"], change["after"])

    def _send_datatable(self, command: str, **fields) -> dict:
        if self._commands is None:
            raise ActionNotPossible(f"{command}: no command channel to the mod HarnessActions in this context")
        self._precondition()
        return self._commands.send(command, **fields)

    # ---- autosave (through the helper mod HarnessActions) ----

    def autosave_status(self) -> dict:
        """Read the autosave timer of the game: handle_id, timer_exists, remaining_s and settings_period_s. It changes nothing."""
        if self._commands is None:
            raise ActionNotPossible("autosave_status: no command channel to the mod HarnessActions in this context")
        self._precondition()
        return self._commands.send("autosave_status")["status"]

    # ---- raids and units (through the helper mod HarnessActions, spec 10) ----

    def _command(self, name: str, /, **fields) -> dict:  # positional only: a command field may be called "name" (spawn_ai_lord)
        if self._commands is None:
            raise ActionNotPossible(f"{name}: no command channel to the mod HarnessActions in this context")
        self._precondition()
        return self._commands.send(name, **fields)

    def _raid_timer(self) -> dict:
        calendar = self._bridge.calendar_path()
        return {name: self._bridge.read_property(calendar, name) for name in ("daysUntilNextRaid", "daysSinceLastRaid")}

    def set_raid_timer(self, days_until: int, days_since: int | None = None) -> dict:
        """Write TemporalComponent.daysUntilNextRaid (and daysSinceLastRaid). Verified: the value holds, falls by 1 each game day,
        and a raid spawns on the day tick that brings it to 0 (set 3: raid on the 3rd day tick). The game then sets a new timer.
        """
        calendar = self._bridge.calendar_path()

        def call() -> None:
            self._bridge.write_property(calendar, "daysUntilNextRaid", int(days_until))
            if days_since is not None:
                self._bridge.write_property(calendar, "daysSinceLastRaid", int(days_since))

        def check(before: dict, after: dict) -> bool:
            return after["daysUntilNextRaid"] == days_until and (days_since is None or after["daysSinceLastRaid"] == days_since)

        return self._perform("set_raid_timer", {"days_until": days_until, "days_since": days_since}, self._raid_timer, call, check)

    def raid_state(self) -> dict:
        """Read the raid timer, the raid setup (yearsUntilFirstRaid, raidingFrequency, ...), the raid id lists and list sizes."""
        return self._command("raid_state")

    def units_census(self, sample: int = 0) -> dict:
        """Count the units by side, role, state and region (and `sample` rows of non-civil units). Read only. About 10 ms in the game."""
        return self._command("units_census", sample=sample)["census"]

    def _spawn(self, action: str, command: str, expected: int, **fields) -> dict:
        answer = self._command(command, **fields)
        before, after = side_count(answer["before"], "bandit"), side_count(answer["after"], "bandit")
        return self._record(action, fields, after - before == expected, before, after, note=f"bandit units, expected +{expected}")

    def spawn_raid(self, squads: int = 1, elite: bool = False) -> dict:
        """Spawn raider squads at the position of the player pawn (RTSMultiEngineCPP:spawnRaiders). Verified: +18 units a squad.

        elite=True calls spawnEliteRaiders: +54 units. Size and type cannot be chosen (see NOT_POSSIBLE choose_raid_type).
        The raiders are side "bandit". They appear a few thousand units away and walk on their own.
        """
        if elite:
            return self._spawn("spawn_raid", "spawn_elite_raiders", ELITE_RAID_UNITS, elite=True)
        return self._spawn("spawn_raid", "spawn_raiders", SQUAD_UNITS * squads, squads=squads)

    def spawn_bandit_camp(self) -> dict:
        """RTSMultiEngineCPP:spawnBanditCamp: one squad of 18 at a random place. Verified: +18 units."""
        return self._spawn("spawn_bandit_camp", "spawn_bandit_camp", SQUAD_UNITS)

    def kill_units(self, side: str = "bandit", count: int = 1, with_loot: bool = False) -> dict:
        """Kill live units of one side with SMUnit:just_die. Verified: the units get dead=true and their loot goes to 0."""
        answer = self._command("kill_units", side=side, count=count, with_loot=int(with_loot))
        killed = answer["killed"]
        dead = dead_count_delta(answer)
        return self._record("kill_units", {"side": side, "count": count}, killed >= 1 and dead == killed, 0, dead,
                            note=f"killed {killed}, loot carried {answer['loot_carried']}")

    def set_unit_loot(self, side: str = "bandit", count: int = 1, amount: int = 1) -> dict:
        """Write SMUnit.ItemsLooted on live units of one side. Verified: the value holds. The unit of the number is not known."""
        answer = self._command("set_unit_loot", side=side, count=count, amount=amount)
        return self._record("set_unit_loot", {"side": side, "count": count, "amount": amount}, answer["changed"] == answer["wanted"],
                            answer["wanted"], answer["changed"])

    # ---- sack: take buildings, goods and people from the village (spec 10, spike S6; HarnessActions version 8) ----

    def sack_census(self) -> dict:
        """Read the village of the player: buildings by state, stock, stores (buildings with goods), families and people. Read only."""
        return self._command("sack_census")["census"]

    def sack_buildings(self, percent: int | None = None, count: int | None = None, method: str = "collapse") -> dict:
        """Burn ("fire") or collapse standing buildings: `count`, or `percent` of the standing ones (rounded half up).

        Verified: both turn a building into rubble (IsRubble, type 75). A collapse is at once. A fire burns for about 50 game seconds
        and destroys the goods inside. The building stays in the list until it is demolished. Checked with the rubble count.
        """
        fields = self._sack_fields(percent, count)
        fields["method"] = sack.check_method(method)
        answer = self._command("sack_buildings", **fields)
        before, after = answer["before"], answer["after"]
        ok = answer["hit"] == answer["wanted"] and sack.rubble(after) - sack.rubble(before) == answer["hit"]
        return self._record("sack_buildings", fields, ok, sack.rubble(before), sack.rubble(after),
                            note=f"rubble buildings, wanted {answer['wanted']}, hit {answer['hit']}, method {method}")

    def sack_goods(self, percent: int | None = None, good: int | None = None, amount: int | None = None, store: int | None = None) -> dict:
        """Remove goods. `percent`: that share of every good (of one store when `store` is given). `good` and `amount`: units of one good.

        Verified: the stock total falls by the units removed. The unit is one item (one call of consumeGoodNoCheck).
        """
        fields = self._goods_fields(percent, good, amount, store)
        answer = self._command("sack_goods", **fields)
        before, after = sack.stock_total(answer["before"]), sack.stock_total(answer["after"])
        return self._record("sack_goods", fields, before - after == answer["removed"], before, after,
                            note=f"stock total, removed {answer['removed']}")

    def sack_people(self, percent: int | None = None, count: int | None = None) -> dict:
        """Kill every member of `count` families, or of `percent` of them (rounded half up). Verified: SMUnit:just_die on each member.

        Checked with the family count, which falls at once (the population count follows at once too).
        """
        fields = self._sack_fields(percent, count)
        answer = self._command("sack_people", **fields)
        before, after = answer["before"], answer["after"]
        ok = sack.families(before) - sack.families(after) == answer["families"] and answer["families"] == answer["wanted"]
        return self._record("sack_people", fields, ok, sack.population(before), sack.population(after),
                            note=f"population, families {sack.families(before)} -> {sack.families(after)}, people killed {answer['people']}")

    def sack_village(self, buildings_pct: int, stock_pct: int, people_pct: int, method: str = "collapse") -> dict:
        """The three sack steps in one command: goods first, then people, then buildings. Returns the answer of the mod.

        The record is checked against the rounding rule: each count falls by share(total, percent).
        """
        fields = {"buildings_pct": sack.check_percent("buildings_pct", buildings_pct), "stock_pct": sack.check_percent("stock_pct", stock_pct),
                  "people_pct": sack.check_percent("people_pct", people_pct), "method": sack.check_method(method)}
        answer = self._command("sack_village", **fields)
        before, after = answer["before"], answer["after"]
        ok = (sack.rubble(after) - sack.rubble(before) == sack.share(sack.standing(before), buildings_pct)
              and sack.families(before) - sack.families(after) == sack.share(sack.families(before), people_pct))
        self._record("sack_village", fields, ok, sack.stock_total(before), sack.stock_total(after),
                     note=f"stock total; buildings hit {answer['buildings_hit']}, families removed {answer['families_removed']}")
        return answer

    @staticmethod
    def _sack_fields(percent: int | None, count: int | None) -> dict:
        if (percent is None) == (count is None):
            raise sack.SackError("give exactly one of percent and count")
        return {"percent": sack.check_percent("percent", percent)} if percent is not None else {"count": sack.check_positive("count", count)}

    @staticmethod
    def _goods_fields(percent: int | None, good: int | None, amount: int | None, store: int | None) -> dict:
        if (percent is None) == (good is None):
            raise sack.SackError("give exactly one of percent and good")
        fields = {} if store is None else {"store": sack.check_positive("store", store)}
        if percent is not None:
            return {**fields, "percent": sack.check_percent("percent", percent)}
        return {**fields, "good": sack.check_positive("good", good), "amount": sack.check_positive("amount", amount or 0)}

    # ---- loot on the ground: a stand-in ledger, because the base game has none (spec 10, spike R3) ----

    def drop_loot(self, count: int, good: int, side: str = "bandit") -> dict:
        """Kill `count` units that carry loot. A pile (place, amount, good) is recorded for each death in the ledger of HarnessLoot.

        The base game leaves nothing on the ground (spike S5, R3). The ledger shows that a mod-defined pile can be driven and read.
        The record has the answer of the mod under "answer": {"killed", "piles"}. It is ok when every wanted unit died and has a pile.
        """
        fields = {"count": sack.check_positive("count", count), "good": sack.check_positive("good", good), "side": side}
        answer = self._command("drop_loot", **fields)
        record = self._record("drop_loot", fields, answer["killed"] == count and len(answer["piles"]) == count, count, answer["killed"])
        record["answer"] = answer
        return record

    def loot_piles(self) -> list[dict]:
        """The piles of the ledger (id, x, y, amount, good). Read only."""
        return self._command("loot_piles")["piles"]

    def recover_loot(self, pile: int) -> dict:
        """A peasant brings a pile home: its goods go into the stock (cheat manager GiveItemByID), the pile leaves the ledger.

        Checked with the stock of that good in the player region (+ the amount of the pile). The walk of a peasant is not modelled.
        """
        piles = {entry["id"]: entry for entry in self.loot_piles()}
        if pile not in piles:
            raise sack.SackError(f"no pile with id {pile} in the ledger ({sorted(piles)})")
        target = piles[pile]
        region = self._region(None)
        stock = lambda: self._bridge.call_function(region, "getStockOfGood", [target["good"], False, False])  # noqa: E731
        call = lambda: self._command("recover_loot", pile=pile)  # noqa: E731
        return self._perform("recover_loot", {"pile": pile, "good": target["good"], "amount": target["amount"]}, stock, call,
                             changed_by(target["amount"]), note="instant: no peasant walks")

    # ---- typed units, battles and mercenaries (spec 10, spikes S7, P5, C1, C2; HarnessActions version 9) ----

    def spawn_units(self, side: str, template: str, count: int = 1, dx: float = 0, dy: float = 0) -> dict:
        """Spawn `count` squads of a unit template (a row of DT_UnitTemplates) with RTSMultiEngineCPP:spawnArmy.

        side "player": the units belong to the player pawn. side "bandit": they belong to the bandit pawn and fight the player.
        The place is the player pawn plus (dx, dy) game units. Verified: spearMilitia gave 32 units, militiaFoot 32, retinue_tier3 36, Brigands 18.
        The start size follows the field maxSize of the row (see datatable_write). The answer has the squad ids and sizes in the key "answer".
        """
        fields = {"side": battle.check_side(side), "template": battle.check_name("template", template), "count": battle.check_count(count),
                  "dx": battle.check_offset("dx", dx), "dy": battle.check_offset("dy", dy)}
        answer = self._command("spawn_units", **fields)
        record = self._record("spawn_units", fields, answer["units"] > 0 and all(squad["units"] > 0 for squad in answer["squads"]),
                              0, answer["units"], note=f"{side} {template} x{count}, squads {[squad['id'] for squad in answer['squads']]}")
        record["answer"] = answer
        return record

    def battle_state(self, detail: bool = False) -> dict:
        """The living units, experience and casualties of the squads that spawn_units and hire_mercenaries made. Read only.

        detail=True adds one row (uid, xp) for each living unit (at most 64 a squad). See runlib/battle.py for the shape.
        """
        return self._command("battle_state", detail=int(detail))

    def clear_battle(self, side: str | None = None) -> dict:
        """Kill the living units of those squads (of one side if `side` is given) and forget the squads. The ids of later squads are new."""
        fields = {} if side is None else {"side": battle.check_side(side)}
        answer = self._command("clear_battle", **fields)
        return self._record("clear_battle", fields, True, 0, answer["killed"], note=f"squads forgotten {answer['squads_forgotten']}")

    def set_squad_experience(self, squad: int, value: float) -> dict:
        """Write combatExperience on every living unit of one squad of the battle registry. Checked per unit by the mod."""
        fields = {"squad": int(squad), "value": battle.check_experience(value)}
        answer = self._command("set_squad_experience", **fields)
        return self._record("set_squad_experience", fields, answer["alive"] > 0 and answer["changed"] == answer["alive"],
                            answer["alive"], answer["changed"])

    def mercenary_offers(self) -> dict:
        """The companies that can be hired: {"offers": [{"name", "cost", "arrives_in", "units"}], "silver", "hired"}. Read only."""
        return self._command("mercenary_offers")

    def hire_mercenaries(self, company: str) -> dict:
        """Hire one offered company with RTSMultiEngineCPP:hireMercs. Verified: silver falls by the cost, the offer leaves the list,
        and the units are there at once (a company of 3 templates gave 3 squads and 108 units). The game itself does not check the cost
        (silver went to -100 in a probe), so the mod and this action refuse when the silver is below the cost.

        The answer of the mod is under "answer". The record compares silver before and after with the cost.
        """
        battle.check_name("company", company)
        offers = self.mercenary_offers()
        offer = battle.find_offer(offers["offers"], company)
        if offers["silver"] < offer["cost"]:
            raise battle.BattleError(f"not enough silver to hire {company}: {offers['silver']} is below the cost {offer['cost']}")
        answer = self._command("hire_mercenaries", company=company)
        paid = answer["silver_before"] - answer["silver_after"]
        ok = (paid == offer["cost"] and answer["units"] > 0 and answer["offers_after"] == len(offers["offers"]) - 1
              and (answer["hired_after"] or 0) == (answer["hired_before"] or 0) + 1)
        record = self._record("hire_mercenaries", {"company": company}, ok, answer["silver_before"], answer["silver_after"],
                              note=f"cost {offer['cost']}, paid {paid}, units {answer['units']}")
        record["answer"] = answer
        return record

    # ---- pop-ups (spec 10, spike S8) ----

    def popup_state(self) -> dict:
        """Read the pop-up windows: {"widgets": n, "open": [types]}. Read only."""
        return self._command("popup_state")

    def close_popups(self) -> dict:
        """Press Accept on every open pop-up ("Hunger!" and similar), then check that none is open. Safe to call at any time.

        An open pop-up pauses the game. Pressing Accept resumes it at the old speed (verified at 8x, spike S8).
        Nothing open is a valid answer: `before` and `after` are both 0 and `closed` is empty.
        """
        before = len(self.popup_state()["open"])
        answer = self._command("close_popups")
        after = len(self.popup_state()["open"])
        return self._record("close_popups", {}, after == 0, before, after,
                            note=f"closed {answer['closed']}" if answer["closed"] else "")

    # ---- construction sites and ruins (spec 10, spike R8) ----

    def building_sites(self, type_id: int | None = None) -> dict:
        """The buildings of the village (one type if given): each with `built`, `rubble`, `burning` and `needs` (goods a site still needs).

        `counts` (when a type is given) has built, sites and rubble. Read only. Placing a site needs place_building (real OS mouse).
        """
        fields = {} if type_id is None else {"type": check_building_type(type_id)}
        return self._command("building_sites", **fields)

    def ruin_building(self, type_id: int, method: str = "fire") -> dict:
        """Burn or collapse the first built building of a type. Verified: it becomes Rubble (type 75) and the counts change by one."""
        check_building_type(type_id)
        if method not in RUIN_METHODS:
            raise ActionError(f"ruin_building: method must be one of {RUIN_METHODS}")
        answer = self._command("ruin_building", type=type_id, method=method)
        ok = answer["after"]["built"] == answer["before"]["built"] - 1 and answer["after"]["rubble"] == answer["before"]["rubble"] + 1
        record = self._record("ruin_building", {"type_id": type_id, "method": method}, ok, answer["before"]["built"], answer["after"]["built"],
                              note=f"rubble {answer['before']['rubble']} -> {answer['after']['rubble']}")
        record["answer"] = answer
        return record

    def demolish_ruins(self) -> dict:
        """Demolish every ruin of the village. Verified: the rubble count falls to 0 and the place is free for a new site."""
        answer = self._command("demolish_ruins")
        record = self._record("demolish_ruins", {}, answer["after"] == 0, answer["before"], answer["after"])
        record["answer"] = answer
        return record

    def set_site_cost(self, type_id: int, good: int, amount: int) -> dict:
        """Lower the amount of one good that a construction site needs (never raise it). Verified: the builders then use the lower amount
        (4 planks -> 2: the stock fell by 2 when the building was built). This is the base for a partial rebuild cost."""
        check_building_type(type_id)
        if not isinstance(good, int) or not 0 <= good <= MAX_GOOD_ID:
            raise ActionError(f"set_site_cost: good must be an item number from 0 to {MAX_GOOD_ID}")
        if not isinstance(amount, int) or amount < 0:
            raise ActionError("set_site_cost: amount must be a whole number, 0 or more")
        answer = self._command("set_site_cost", type=type_id, good=good, amount=amount)
        now = {need["good"]: need["amount"] for need in answer["needs"]}
        record = self._record("set_site_cost", {"type_id": type_id, "good": good, "amount": amount}, now.get(good) == amount,
                              answer["before"], now.get(good))
        record["answer"] = answer
        return record

    # ---- manor (spec 12, criterion M1) ----

    def manor_state(self) -> dict:
        """The manor modules of the village: `modules` (id, type, built, goods, total, capacity, is_region_manor) and `region_manor_id`. Read only."""
        return self._command("manor_state")

    def finish_manor_site(self, type_id: int = 57) -> dict:
        """Harness shortcut, NOT a base game action: finish a Keep site at once and register it as the manor of the region.

        The test village (5 families) never finishes a Keep by itself: the game says "not_enough_workers" (it needs 40 builder units).
        The mod writes `Data.constructed = true` and calls `setRegionsManor`. Checked: the module reads as built and is the region manor.
        """
        check_building_type(type_id)
        answer = self._command("finish_manor_site", type=type_id)
        module = answer["module"]
        return self._record("finish_manor_site", {"type_id": type_id}, module["built"] and module["is_region_manor"], False, module["built"],
                            note="shortcut: Data.constructed + setRegionsManor")

    def manor_put(self, good: int, amount: int, manor: int | None = None) -> dict:
        """Put goods into a built manor module (mod-defined store on the building inventory). Verified when the module and the region stock both rise by `amount`."""
        check_manor_goods(good, amount)
        fields = {} if manor is None else {"manor": manor}
        answer = self._command("manor_put", good=good, amount=amount, **fields)
        ok = answer["after"] == answer["before"] + amount and answer["stock_after"] == answer["stock_before"] + amount
        record = self._record("manor_put", {"good": good, "amount": amount}, ok, answer["before"], answer["after"],
                              note=f"region stock {answer['stock_before']} -> {answer['stock_after']}")
        record["answer"] = answer
        return record

    def manor_take(self, good: int, amount: int, manor: int | None = None) -> dict:
        """Take goods out of a manor module. Verified when the module and the region stock both fall by `amount`."""
        check_manor_goods(good, amount)
        fields = {} if manor is None else {"manor": manor}
        answer = self._command("manor_take", good=good, amount=amount, **fields)
        ok = answer["after"] == answer["before"] - amount and answer["stock_after"] == answer["stock_before"] - amount
        record = self._record("manor_take", {"good": good, "amount": amount}, ok, answer["before"], answer["after"],
                              note=f"region stock {answer['stock_before']} -> {answer['stock_after']}")
        record["answer"] = answer
        return record

    def manor_stock(self, good: int, manor: int | None = None) -> int:
        """Units of one good in a manor module (the first built one, or the one with this id). Read only."""
        for module in self.manor_state()["modules"]:
            if (manor is None and module["built"]) or module["id"] == manor:
                return next((entry["amount"] for entry in module["goods"] if entry["good"] == good), 0)
        raise ActionError(f"manor_stock: no {'built ' if manor is None else ''}manor module{'' if manor is None else f' with id {manor}'}")

    def manor_worker_slot(self, job: int = 45, slots: int = 3, manor: int | None = None) -> dict:
        """Give the manor module the worker slots of a Storehouse (job 45, WarehouseWorker) or a Granary (job 44, GranaryWorker).

        The base game reads the slots and the role of a building from its row in the DataTable buildingStats. The mod writes that row
        (in memory only), so this is a mod-defined change of a base game table. Verified when the building reads back the slots and the job.
        """
        check_worker_slot(job, slots)
        fields = {} if manor is None else {"manor": manor}
        answer = self._command("manor_worker_slot", job=job, slots=slots, **fields)
        after = answer["after"]
        ok = after["max_slots"] == slots and after["job"] == job
        record = self._record("manor_worker_slot", {"job": job, "slots": slots}, ok, answer["before"]["max_slots"], after["max_slots"],
                              note=f"{answer['job_name']}: job {answer['before']['job']} -> {after['job']}")
        record["answer"] = answer
        return record

    def manor_assign_worker(self, family: int | None = None, manor: int | None = None) -> dict:
        """Assign one family to the manor module (Region:assignFamily). Without `family` the first family with no workplace is used.

        Verified when the number of assigned families on the building rises by one.
        """
        fields = {}
        if family is not None:
            if not isinstance(family, int) or isinstance(family, bool) or family < 0:
                raise ActionError(f"family must be a whole number, 0 or more, got {family!r}")
            fields["family"] = family
        if manor is not None:
            fields["manor"] = manor
        answer = self._command("manor_assign_worker", **fields)
        ok = answer["after"]["assigned"] == answer["before"]["assigned"] + 1
        record = self._record("manor_assign_worker", {"family": answer["family"]}, ok, answer["before"]["assigned"], answer["after"]["assigned"],
                              note=f"workers (people) {answer['after']['workers']}")
        record["answer"] = answer
        return record

    def manor_unassign_workers(self, manor: int | None = None) -> dict:
        """Take every family off the manor module. Verified when no family is assigned any more."""
        fields = {} if manor is None else {"manor": manor}
        answer = self._command("manor_unassign_workers", **fields)
        record = self._record("manor_unassign_workers", {}, answer["after"]["assigned"] == 0, answer["before"]["assigned"], answer["after"]["assigned"])
        record["answer"] = answer
        return record

    def manor_worker_state(self) -> dict:
        """Per manor module: `max_slots`, `job`, `assigned` (families), `workers` (people), `is_storage`, plus `goods` and `total`. Read only."""
        return self._command("manor_worker_state")

    # ---- walls outside the manor system (spec 14, implementation-notes/free-walls.md) ----
    # Steps for a free wall: road_mode(True), click the road points with the real mouse (the road preview shows), road_commit(),
    # wall_make(road_id, 2). No manor, goods or builders are needed (verified in the real game).

    def wall_state(self) -> dict:
        """Every wall road (roadType 3 or a wallType): id, wall_name, blueprint, meshes, length, middle. `counts` has one number for each wall name. Read only."""
        return self._command("wall_state")

    def road_mode(self, on: bool) -> dict:
        """Turn the road tool of the player on or off. Verified: `road_mode` in the answer follows."""
        if not isinstance(on, bool):
            raise ActionError("road_mode: on must be true or false")
        return self._command("road_mode", on=1 if on else 0)

    def road_commit(self) -> dict:
        """Commit the road that the player has drawn (2 or more points). Returns `road`, the id of the new road (a plain road, wall_name none)."""
        return self._command("road_commit")

    def wall_make(self, road_id: int, wall_type: int = 2) -> dict:
        """Make a committed road a wall: 2 wooden palisade, 3 stone low, 4 stone high. Verified: the road gets roadType 3 and wall meshes at once, with no cost."""
        if not isinstance(road_id, int) or isinstance(road_id, bool) or road_id <= 0:
            raise ActionError("wall_make: road_id must be a road id from road_commit or wall_state")
        if wall_type not in WALL_TYPES:
            raise ActionError(f"wall_make: wall_type must be one of {WALL_TYPES}")
        return self._command("wall_make", road=road_id, wall_type=wall_type)

    def wall_remove(self, road_id: int) -> dict:
        """Remove a wall road with the game's removeRoad. Verified: the meshes and the spline are gone, and wall_state no longer lists it."""
        if not isinstance(road_id, int) or isinstance(road_id, bool) or road_id <= 0:
            raise ActionError("wall_remove: road_id must be a road id from wall_state")
        return self._command("wall_remove", road=road_id)

    # ---- Policies (spec 16, implementation-notes/policies.md) ----
    # The player's region has policy slots. policy_state reads them; policy_enact calls PawnCPP:enactPolicy.

    def policy_state(self) -> dict:
        """Policies in the slots (`policies`: slot, id, name), signed ids, available ids, `max_policies`, approval and its factors,
        silver, influence, development points spent. Read only."""
        return self._command("policy_state")

    def policy_enact(self, policy: int, slot: int = 0) -> dict:
        """PawnCPP:enactPolicy(region, slot, policy). The answer has `before`, `after` and the game's `returned` value.
        Refused when the policy id is not in the available list or the slot is outside `max_policies`."""
        self._check_policy_id("policy_enact", policy)
        if not isinstance(slot, int) or isinstance(slot, bool) or slot < 0:
            raise ActionError("policy_enact: slot must be a whole number from 0")
        return self._command("policy_enact", policy=policy, slot=slot)

    def policy_sign(self, policy: int, signed: bool) -> dict:
        """Region:setPolicySigned(policy, signed). The answer has `before` and `after`."""
        self._check_policy_id("policy_sign", policy)
        if not isinstance(signed, bool):
            raise ActionError("policy_sign: signed must be true or false")
        return self._command("policy_sign", policy=policy, signed=signed)

    @staticmethod
    def _check_policy_id(name: str, policy: int) -> None:
        if not isinstance(policy, int) or isinstance(policy, bool) or policy <= 0:
            raise ActionError(f"{name}: policy must be a policy id from policy_state")

    # ---- Bandit negotiation (spec 15, implementation-notes/bandit-settlement.md) ----

    def bandit_state(self) -> dict:
        """Families, homeless families and vacant home slots (`regions[].vacant_slots`) of the player, bandit units, silver, influence and the relation tags with the bandit lord. Read only."""
        return self._command("bandit_state")

    def bandit_tag(self, tag: str, remove: bool = False) -> dict:
        """Add (or remove) a relation tag between the player and the bandit lord. The settle paragraph needs the tag `attacking`."""
        if tag not in BANDIT_TAGS:
            raise ActionError(f"bandit_tag: tag must be one of {BANDIT_TAGS}")
        return self._command("bandit_tag", tag=tag, remove=1 if remove else 0)

    def bandit_settle_offer(self, silver: int) -> dict:
        """Send the letter paragraph `raider_suggestSettle+<silver>` to the bandit lord (the Negotiation option of the diplomacy panel).
        Verified: it needs the tag `attacking`; the silver is taken; the bandit units lose their squad at once and are deleted after a few game seconds."""
        if not isinstance(silver, int) or isinstance(silver, bool) or not 0 <= silver <= MAX_SETTLE_SILVER:
            raise ActionError(f"bandit_settle_offer: silver must be a whole number from 0 to {MAX_SETTLE_SILVER}")
        return self._command("bandit_letter", paragraphs=[f"raider_suggestSettle+{silver}"])

    def settle_raiders(self) -> dict:
        """The developer cheat MLCheatManager:SettleRaiders. Verified: the bandit units lose their squad, then they are deleted. No families appear."""
        return self._command("settle_raiders")

    def bandit_mark(self) -> dict:
        """Remember the bandit units, so that `bandit_track` can tell what happened to each of them."""
        return self._command("bandit_mark")

    def bandit_track(self) -> dict:
        """Counts of the marked units: in a squad, without a squad, gone (deleted), dead."""
        return self._command("bandit_track")

    # ---- Reverse direction: families become bandits (spec 15, implementation-notes/homeless-rebellion.md) ----

    def bandit_spawn_at(self, x: float, y: float, z: float = 0, template: str = "Brigands", count: int = 1) -> dict:
        """Bandit squads at a chosen point (spawnArmy, owner = the bandit lord). Verified: 18 Brigands appear at the point; they then walk to a rally point and stay idle."""
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= MAX_REBEL_SQUADS:
            raise ActionError(f"bandit_spawn_at: count must be a whole number from 1 to {MAX_REBEL_SQUADS}")
        return self._command("bandit_spawn_at", x=x, y=y, z=z, template=template, count=count)

    def bandit_turn(self, count: int = 1, source: str = "squad") -> dict:
        """SMUnit:turnToBandit on units. source "squad": units from spawn_units side=player (verified: no visible change).
        source "family": members of the first families (verified: the unit leaves its family and gets the role Soldier; one run crashed the game later, cause not isolated)."""
        if source not in ("squad", "family"):
            raise ActionError("bandit_turn: source must be squad or family")
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= MAX_TURN_UNITS:
            raise ActionError(f"bandit_turn: count must be a whole number from 1 to {MAX_TURN_UNITS}")
        return self._command("bandit_turn", count=count, source=source)

    def homeless_rebel(self, count: int, mode: str = "home", families_per_squad: int = 1, template: str = "Brigands") -> dict:
        """Remove `count` families (sack_people), then bandits appear for them. Verified: families 10 -> 8 for count=2, homeless stays 0.
        mode "home": a Brigands squad (18 units) at the home of each family. The squads walk to a waypoint (-31000,-22500), wait there,
        and about 650 game seconds (16 game days) after the spawn they march into the village and burn (runs s15-h1, h2, h3: 3 of 3).
        mode "raid": a real raid (spawnRaiders) targets each home; the squad appears at the map edge and burns after about 215 game seconds."""
        if mode not in ("home", "raid"):
            raise ActionError("homeless_rebel: mode must be home or raid")
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= MAX_REBEL_FAMILIES:
            raise ActionError(f"homeless_rebel: count must be a whole number from 1 to {MAX_REBEL_FAMILIES}")
        if not isinstance(families_per_squad, int) or isinstance(families_per_squad, bool) or not 1 <= families_per_squad <= MAX_REBEL_FAMILIES:
            raise ActionError(f"homeless_rebel: families_per_squad must be a whole number from 1 to {MAX_REBEL_FAMILIES}")
        return self._command("homeless_rebel", count=count, mode=mode, families_per_squad=families_per_squad, template=template)

    def bandit_kill_squads(self, squad: int, count: int = 1) -> dict:
        """SMUnit:just_die on every living bandit unit of the squads `squad`, `squad` + 1, ... (`count` squads). Removes a raid and keeps other squads."""
        if not isinstance(squad, int) or isinstance(squad, bool) or squad < 1:
            raise ActionError("bandit_kill_squads: squad must be a squad id (a whole number above 0)")
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= MAX_KILL_SQUADS:
            raise ActionError(f"bandit_kill_squads: count must be a whole number from 1 to {MAX_KILL_SQUADS}")
        return self._command("bandit_kill_squads", squad=squad, count=count)

    def steer_state(self, squad: int) -> dict:
        """Read only (spike #59): owner side, living units, centre and mean unit target of one squad."""
        self._check_squad_id("steer_state", squad)
        return self._command("steer_state", squad=squad)

    def steer_move(self, squad: int, x: float, y: float, z: float = 0, half_width: float = 300, formation: str = "Line") -> dict:
        """Order one squad to a point: PawnCPP:formALineArmy of the owner pawn (spike #59). The answer holds the squad centre before the order."""
        self._check_squad_id("steer_move", squad)
        for name, value in (("x", x), ("y", y), ("z", z), ("half_width", half_width)):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ActionError(f"steer_move: {name} must be a number")
        return self._command("steer_move", squad=squad, x=x, y=y, z=z, half_width=half_width, formation=formation)

    def steer_select(self, squad: int) -> dict:
        """Select one squad for its owner pawn (PawnCPP:selectSquad). The next real right click orders it."""
        self._check_squad_id("steer_select", squad)
        return self._command("steer_select", squad=squad)

    def steer_cursor(self, x: float, y: float, z: float = 0) -> dict:
        """Put the cursor over the world point (PlayerController:SetMouseLocation). The point must be on screen. It moves the real cursor."""
        for name, value in (("x", x), ("y", y), ("z", z)):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ActionError(f"steer_cursor: {name} must be a number")
        return self._command("steer_cursor", x=x, y=y, z=z)

    def steer_mouse3d(self) -> dict:
        """The terrain point under the cursor (PawnCPP:getMouse3d). Read only."""
        return self._command("steer_mouse3d")

    def steer_rmb(self) -> dict:
        """Call PawnCPP:RMB_BP_pressed and RMB_BP_released: the selected squads go to the terrain point under the cursor."""
        return self._command("steer_rmb")

    def steer_hook(self, functions: list[str]) -> dict:
        """Record the calls of these functions (full paths such as /Script/ManorLords.PawnCPP:formALineArmy). Read them with steer_hook_log."""
        if not functions or not all(isinstance(name, str) for name in functions):
            raise ActionError("steer_hook: functions must be a list of function paths")
        return self._command("steer_hook", functions=",".join(functions))

    def steer_hook_log(self, clear: bool = False) -> dict:
        """The recorded calls (path, count, arguments) and the call count of each hooked function."""
        return self._command("steer_hook_log", clear=clear)

    @staticmethod
    def _check_squad_id(command: str, squad: int) -> None:
        if not isinstance(squad, int) or isinstance(squad, bool) or squad < 1:
            raise ActionError(f"{command}: squad must be a squad id (a whole number above 0)")

    def rebel_rally(self, count: int = 2) -> dict:
        """Rally of rebels in the woods near the AI waypoint: remove `count` families, then one Brigands squad appears at the forest spot
        that is nearest to the waypoint (-31000,-22500). The squad walks to the waypoint at once and waits there (about 480 game seconds),
        then it burns the village (about 650 game seconds after the spawn). The AI picks the wait point. A forest far from the waypoint
        does not hold the squad: it walks through the village and burns on the way (run s15-w1). See "Rally in the woods" in
        implementation-notes/homeless-rebellion.md."""
        spots = self.forest_spot(min_dist=15000, max_dist=40000)["spots"]
        if not spots:
            raise ActionError("rebel_rally: no forest spot between 15000 and 40000 units from the village")
        spot = min(spots, key=lambda s: (s["x"] - REBEL_WAYPOINT[0]) ** 2 + (s["y"] - REBEL_WAYPOINT[1]) ** 2)
        self._command("sack_people", count=count)
        spawned = self.bandit_spawn_at(spot["x"], spot["y"], spot["z"], count=1)
        return {"spot": spot, "squads": spawned["squads"]}

    def rebel_raid_rally(self, count: int = 2) -> dict:
        """Homeless rebellion with a real raid: remove `count` families, then one raid (spawnRaiders) aimed at a forest spot.
        The target only sets where the raiders appear (the map edge). They walk north, burn a few buildings on the way, stand at the AI
        waypoint (-31000,-22500, inside the player region) for about 100 to 150 game seconds, then attack the village. The settle letter
        while they stand there removes them and gave +2 families (runs s15-p2, p5). The answer has the squad ids, the spot and the
        families before and after. See "Raid aimed at the woods" in implementation-notes/homeless-rebellion.md."""
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= MAX_REBEL_FAMILIES:
            raise ActionError(f"rebel_raid_rally: count must be a whole number from 1 to {MAX_REBEL_FAMILIES}")
        return self._command("rebel_raid_rally", count=count)

    def rebel_fallback_attack(self, squad: int, raid_squads: int = 1) -> dict:
        """Mod-driven fallback for a rally that cannot be held: kill the rally squad, then send a real raid at the village.
        Measured (run s15-w5): the first building burned 100 to 135 game seconds after the raid spawn."""
        killed = self.bandit_kill_squads(squad)
        return {"killed": killed["killed"], "raid": self._command("spawn_raiders", squads=raid_squads)}

    def forest_spot(self, min_dist: int = 15000, max_dist: int = 40000) -> dict:
        """Up to 5 dense tree groups of the player region, best first (read only). The trees are foliage instances, not Resource actors.
        Distances are game units from the village centre (100 units = 1 m)."""
        for name, value in (("min_dist", min_dist), ("max_dist", max_dist)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ActionError(f"forest_spot: {name} must be a whole number of 0 or more")
        if max_dist <= min_dist:
            raise ActionError("forest_spot: max_dist must be larger than min_dist")
        return self._command("forest_spot", min_dist=min_dist, max_dist=max_dist)

    # ---- Housing and homeless tents (spec 15, implementation-notes/tent-placement.md) ----

    def building_stat(self, type_id: int) -> dict:
        """Scalar fields of the buildingStats row of one building type (read only). Type 87 is the homeless tent."""
        return self._command("building_stat", type=type_id)

    def housing_state(self) -> dict:
        """Player region: families, homeless, living and vacant slots, tents and residential buildings, and the tents of the whole world (read only)."""
        return self._command("housing_state")

    def accommodate_homeless(self) -> dict:
        """Region:accomodateHomelessFamilies(nil). Moves homeless families into free homes. The answer has the housing before and after."""
        return self._command("accommodate_homeless")

    # ---- Composite building parts (spec 18, implementation-notes/part-edit-test.md) ----

    def master_parts(self, building: int | None = None, type_id: int | None = None, limit: int = 5) -> dict:
        """Parts (SMBuilding actors) and extensions of one building master, by id or by type (read only)."""
        fields = {"limit": limit}
        if building is not None:
            fields["building"] = building
        if type_id is not None:
            fields["type"] = type_id
        return self._command("master_parts", **fields)

    def master_part_remove(self, building: int, index: int, mode: str = "hide") -> dict:
        """UNSAFE test command (the game needs HARNESS_ALLOW_UNSAFE=1): hide, destroy or unlink part `index` (from 1) of a master."""
        return self._command("master_part_remove", building=building, index=index, mode=mode)

    def master_part_add(self, building: int, from_part: int = 1, dx: float = 0, dy: float = 0, dz: float = 0) -> dict:
        """UNSAFE test command: spawn a copy of part `from_part` and append it to the part list of the master."""
        return self._command("master_part_add", building=building, **{"from": from_part}, dx=dx, dy=dy, dz=dz)

    def family_state(self) -> dict:
        """Housing numbers with approval and public order, and the ids of the housed families (read only)."""
        return self._command("family_state")

    def family_eject(self, count: int, suppress: bool = True, home: str = "none") -> dict:
        """Region:SetFamilyHome(id, nil, suppress) for `count` housed families: they become homeless (spec 15 part 7)."""
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 10:
            raise ActionError("family_eject: count must be a whole number from 1 to 10")
        if home not in ("none", "tent"):
            raise ActionError("family_eject: home must be none or tent")
        return self._command("family_eject", count=count, suppress=bool(suppress), home=home)

    def family_census(self) -> dict:
        """Who lives where (read only): one row per family (living members, roles, familyHome) and one row per home or tent with its occupant family ids."""
        return self._command("family_census")

    def member_fields(self, family: int = 0) -> dict:
        """Property names and plain values of the first member of the family with this zero-based index (read only)."""
        if not isinstance(family, int) or isinstance(family, bool) or family < 0:
            raise ActionError("member_fields: family must be a whole number of 0 or more")
        return self._command("member_fields", count=family)

    def family_add(self, count: int = 1, adult: bool = False) -> dict:
        """A villager leaves a family of 2 or more and starts a new, homeless family (Region:AddNewFamily). With adult, the villager with the highest `Age` of its family is taken. On fixture `base` every member has Age 1 and role 3, so this changes nothing there (run s61-plots-add)."""
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 10:
            raise ActionError("family_add: count must be a whole number from 1 to 10")
        return self._command("family_add", count=count, adult=bool(adult))

    def plot_field_place(self, plots: list[dict]) -> dict:
        """Write burgage plots into the pawn (`extractedPlots`) without the mouse. Needs the build tool open: see `open_burgage_tool`.
        Plot data: see runlib/plotgeom.py. After this, call `commit_plots`."""
        if not plots:
            raise ActionError("plot_field_place: plots must not be empty")
        return self._command("plot_field_place", plots=plots)

    def open_burgage_tool(self) -> None:
        """Set placePlotType 3 (burgage plot) and placeFieldMode on the player pawn. No click."""
        player = self._bridge.player_path()
        self._bridge.write_property(player, "placePlotType", 3)
        self._bridge.write_property(player, "placeFieldMode", True)

    def commit_plots(self) -> None:
        """PawnCPP:addCommitFieldRequest(): the game builds the plots written by `plot_field_place`."""
        self._bridge.call_function(self._bridge.player_path(), "addCommitFieldRequest")

    def burgage_count(self, constructed_only: bool = True) -> int:
        """Region:getBuildingCount(3, constructed_only) for burgage plots of the player region."""
        return self._bridge.call_function(self._bridge.player_region_path(), "getBuildingCount", [3, constructed_only])

    def tent_find_spot(self) -> dict:
        """Up to 5 free spots (x, y, z) for a tent around the village centre. Read only: it does not place anything.
        A spot is outside every building border (the game's own check) and at least 900 units from every building. Water and roads are not checked."""
        return self._command("tent_find_spot")

    def tent_auto_place(self) -> dict:
        """Find a free spot, centre the camera on it and place a tent (type 87) with the REAL OS mouse.

        TEST STEP ONLY. The final mod needs a mouse-free method, and none is known (the placement call takes a struct that Lua cannot fill).
        The spot finder is mouse-free. The click is not. Checked with the number of tents of the player region (+1).
        """
        spots = self.tent_find_spot().get("spots") or []
        if not spots:
            raise ActionNotPossible("tent_auto_place: tent_find_spot found no free spot")
        spot = spots[0]
        self._bridge.centre_camera_on(spot["x"], spot["y"])
        return self.place_building(TENT_TYPE, 0.5, 0.5)

    # ---- AI lords (spec 10, spike S11, implementation-notes/baron-model.md) ----
    # A lord is a number from 1 in FindAllOf("PawnCPP_AI") order (lord 1 was the baron in every run). Target 0 is the player.
    # The game's AI moves the armies; these calls steer its inputs. There is no direct move order.

    def lords_state(self, log: int = 12) -> dict:
        """Every AI lord (traits, influence, silver, enemies, relation tags with the player, squads with `realPos` center and target),
        the challenges and the last `log` lines of the three AI debug logs. Read only."""
        return self._command("lords_state", log=log)

    def lord_declare_war(self, lord: int, target: int = 0) -> dict:
        """PawnCPP:declareWar. Verified: the relation gets the tag `at_war` and the target joins the lord's `enemies`."""
        return self._command("lord_declare_war", lord=lord, target=target)

    def lord_declare_peace(self, lord: int, target: int = 0) -> dict:
        """PawnCPP:declarePeace. Not run in the real game yet."""
        return self._command("lord_declare_peace", lord=lord, target=target)

    def lord_set_influence(self, lord: int, value: int) -> dict:
        """Write the lord's influence (0 to 10000). Verified: with 2000 the baron claimed a region by itself."""
        return self._command("lord_set_influence", lord=lord, value=value)

    def lord_challenge(self, lord: int, target: int = 0) -> dict:
        """RTSMultiEngineCPP:initChallenge over the target's current region. Verified: the lord's AI moves its army to the area,
        fights an army there, and takes the region when it wins."""
        return self._command("lord_challenge", lord=lord, target=target)

    def lord_claim(self, lord: int, target: int = 0) -> dict:
        """PawnCPP:layClaim on the target's current region. Not run in the real game yet."""
        return self._command("lord_claim", lord=lord, target=target)

    def lord_spawn_army(self, lord: int, template: str, count: int = 1, dx: float = 0, dy: float = 0) -> dict:
        """spawnArmy with the lord as owner, dx and dy from the player pawn. The lord's AI commands the squads."""
        return self._command("lord_spawn_army", lord=lord, template=template, count=count, dx=dx, dy=dy)

    def spawn_ai_lord(self, name: str, can_build: bool = False) -> dict:
        """RTSMultiEngineCPP:spawnNewAILord (no portrait). Returns `lord`, the number of the new lord.
        Verified: with war, an army, a challenge and `lord_start_ai`, its AI marched the army to the challenge area (S11).
        With can_build its AI still did not build (S13, dynamic-lords.md)."""
        return self._command("spawn_ai_lord", name=name, build=1 if can_build else 0)

    def lord_start_ai(self, lord: int, speed: float = 1, can_build: bool = False) -> dict:
        """PawnCPP_AI:startAI(speed, canBuild). Needed for a lord made with spawn_ai_lord."""
        return self._command("lord_start_ai", lord=lord, value=speed, build=1 if can_build else 0)

    def regions_state(self) -> dict:
        """Every region: object name, name, owner, settled, settlement type and level, town center, manor, buildings, families."""
        return self._command("regions_state")

    def lord_relations(self, lord: int) -> dict:
        """RTSMultiEngineCPP:addPawnRelations(lord). Verified (S13): a new lord gets relation rows, with no tags towards the player."""
        return self._command("lord_relations", lord=lord)

    def lord_take_region(self, lord: int, region: str) -> dict:
        """Write Region.ownerPawn = lord (region by object name, as regions_state prints). Verified (S13): the owner changes and the
        village stays. The lord does NOT build there (use lord_receive_region for that)."""
        return self._command("lord_take_region", lord=lord, region=region)

    def claim_region(self, region: str, target: int = 0, finalize: bool = True) -> dict:
        """PawnCPP:layClaim and finalizeClaim (target 0 is the player, N a lord). Verified (S13 part 2): a free region gets the owner
        and a CityPlanningComponent at once; no 14 day wait."""
        return self._command("claim_region", target=target, region=region, finalize=1 if finalize else 0)

    def settle_region(self, region: str, target: int = 0, settlement_type: int = 1, supply: int = 0,
                      x: float | None = None, y: float | None = None, z: float = 0) -> dict:
        """PawnCPP:settleRegion for a region the pawn owns (claim it first). Gives the starter village (4 buildings, 5 families).
        Verified (S13 part 2). It crashed the game 3 of 3 times for a region without an owner, so the command refuses that.
        x, y, z set the camp position (default: the settled center of the region)."""
        fields = {"target": target, "region": region, "type": settlement_type, "supply": supply}
        if x is not None and y is not None:
            fields.update(x=x, y=y, z=z)
        return self._command("settle_region", **fields)

    def region_clear_owner(self, region: str) -> dict:
        """Write Region.ownerPawn = nil. The buildings stay. First step of lord_receive_region."""
        return self._command("region_clear_owner", region=region)

    def lord_receive_region(self, lord: int, region: str) -> dict:
        """Clear the owner, then the lord claims the region. Verified (S13 part 2): the lord builds there (10 to 15 AI_build lines in 20
        game days, 4 to 14 buildings), also in a village that the player settled. lord_take_region alone does not make the lord build."""
        return self._command("lord_receive_region", lord=lord, region=region)

    def lord_found_village(self, lord: int, region: str, settlement_type: int = 1, supply: int = 0) -> dict:
        """The lord claims and settles a free region. Verified (S13 part 2): the lord then builds on its own. supply 2 gave
        more resources (no 'lacks resources' lines in 20 cycles)."""
        return self._command("lord_found_village", lord=lord, region=region, type=settlement_type, supply=supply)

    # ---- UI banner (spec 10, spike S9, criterion T4) ----

    def show_message(self, text: str, subtext: str = "") -> dict:
        """Show a banner ("Raid in 3 days") with PawnCPP:playEventMessage and read the text back from the widget.

        Verified in the real game: a new `genericAchievement_EventMessage_C` appears and its `Text` and `main_txt` hold the text.
        The screenshot shows the banner at the top of the screen. The old banners stay in memory for a while, so the mod
        returns the new widget. Allowed characters: letters, digits, space and , . ! : - (the mod refuses others).
        """
        check_banner_text("text", text, MAX_BANNER_TEXT, required=True)
        check_banner_text("subtext", subtext, MAX_BANNER_SUBTEXT, required=False)
        answer = self._command("show_message", text=text, subtext=subtext)
        ok = answer["shown"] and answer.get("text") == text and answer.get("main_text") == text
        record = self._record("show_message", {"text": text}, ok, None, answer.get("main_text"), note=f"banner {text!r}")
        record["answer"] = answer
        return record

    def read_message(self) -> dict:
        """The text of the banner that show_message made last: {"alive", "text", "subtext", "main_text", "finished"}. Read only."""
        return self._command("read_message")

    def list_messages(self) -> dict:
        """The banners that are still in memory: {"count", "messages"}. Read only."""
        return self._command("list_messages")


def check_manor_goods(good: int, amount: int) -> None:
    if not isinstance(good, int) or isinstance(good, bool) or not 0 <= good <= MAX_GOOD_ID:
        raise ActionError(f"good must be an item number from 0 to {MAX_GOOD_ID}, got {good!r}")
    if not isinstance(amount, int) or isinstance(amount, bool) or not 1 <= amount <= MAX_MANOR_AMOUNT:
        raise ActionError(f"amount must be a whole number from 1 to {MAX_MANOR_AMOUNT}, got {amount!r}")


def check_worker_slot(job: int, slots: int) -> None:
    if job not in STORAGE_JOBS or isinstance(job, bool):
        raise ActionError(f"job must be one of {STORAGE_JOBS} (44 GranaryWorker, 45 WarehouseWorker), got {job!r}")
    if not isinstance(slots, int) or isinstance(slots, bool) or not 1 <= slots <= MAX_WORKER_SLOTS:
        raise ActionError(f"slots must be a whole number from 1 to {MAX_WORKER_SLOTS}, got {slots!r}")


def check_building_type(type_id: int) -> int:
    if not isinstance(type_id, int) or isinstance(type_id, bool) or not 0 <= type_id <= MAX_BUILDING_TYPE:
        raise ActionError(f"building type must be a number from 0 to {MAX_BUILDING_TYPE}, got {type_id!r}")
    return type_id


def check_banner_text(label: str, value: str, max_chars: int, required: bool) -> None:
    if not value:
        if required:
            raise ActionError(f"show_message: {label} is required")
        return
    if len(value) > max_chars:
        raise ActionError(f"show_message: {label} is longer than {max_chars} characters")
    if not BANNER_TEXT_PATTERN.match(value):
        raise ActionError(f"show_message: {label} may use only letters, digits, space and , . ! : -")


def dead_count_delta(answer: dict) -> int:
    """Units that were counted dead by a kill command (before and after counts come from the mod)."""
    return answer["after"]["dead"] - answer["before"]["dead"]
