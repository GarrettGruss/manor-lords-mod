"""Actions for scenarios (spec 07): create a game situation, then check that it happened.

Every action does four things: check that the game is loaded, read the state, make the change, read the state again.
It returns {"action", "ok", "args", "before", "after"} and adds a short line to the scenario notes.
A failed read-back also adds a failed assertion, so the scenario verdict is `fail`.

Only actions that were checked in the real game are here (docs/specs/07-feature-test-kit/implementation-notes/actions-catalog.md).
A name in NOT_POSSIBLE, or an unknown name, raises ActionNotPossible with the reason. The runner turns that into a failed scenario.

Call actions while the game is paused. A running game changes silver and stock by itself, and then an exact read-back can fail.
"""

from __future__ import annotations

from typing import Any, Callable

from .bridge_client import Bridge
from .commands import CommandChannel

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

NOT_POSSIBLE = {
    "save_state": "PawnCPP:requestSaveFile writes into the user's real save folder, even when the run has a private LOCALAPPDATA. "
                  "It overwrote the user's saveGame_9 in the probe. Make fixtures with harness/tools/fixtures.py instead.",
    "show_message": "PawnCPP:playEventMessage crashed the game when called through the bridge (spec 07 catalog).",
    "get_item_info": "RTSMultiEngineCPP:getItem crashed the game when called through the bridge (spec 07 catalog).",
    "remove_all_families": "MLCheatManager:RemoveAllFamilies changed no population or family count in the probe.",
    "spawn_raiders": "MLCheatManager:SpawnRaidersOfType and RTSMultiEngineCPP:spawnBanditCamp changed no unit count in the probe, "
                     "and the valid type names are unknown. Use spawn_bandit_squad.",
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

    # ---- item table (spec 09, read only, through the helper mod HarnessActions) ----

    def datatable_info(self) -> dict:
        """Row count, the first row names and the row struct of `itemStats`. It changes nothing."""
        return self._send_datatable("datatable_info")["info"]

    def datatable_read(self, row: str | int, field: str) -> float:
        """Read one number field (Weight, Value, spoilageRate) of one `itemStats` row. It changes nothing."""
        answer = self._send_datatable("datatable_read", row=str(row), field=field)
        return answer["values"][field]

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
