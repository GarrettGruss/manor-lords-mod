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
from . import sack
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

NOT_POSSIBLE = {
    "save_state": "PawnCPP:requestSaveFile writes into the user's real save folder, even when the run has a private LOCALAPPDATA. "
                  "It overwrote the user's saveGame_9 in the probe. Make fixtures with harness/tools/fixtures.py instead.",
    "show_message": "PawnCPP:playEventMessage crashed the game when called through the bridge (spec 07 catalog).",
    "get_item_info": "RTSMultiEngineCPP:getItem crashed the game when called through the bridge (spec 07 catalog).",
    "remove_all_families": "MLCheatManager:RemoveAllFamilies changed no population or family count in the probe.",
    "spawn_raiders": "MLCheatManager:SpawnRaidersOfType changed no unit count (checked again in spec 10). Use spawn_raid.",
    "choose_raid_type": "spawnRaiders and spawnEliteRaiders take no type or size: a squad is always 18 units. The raid id lists "
                        "(RaidSettings.defaultRaidIDs) were read but not written (spec 10, spike S2).",
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

    # ---- raids and units (through the helper mod HarnessActions, spec 10) ----

    def _command(self, name: str, **fields) -> dict:
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


def dead_count_delta(answer: dict) -> int:
    """Units that were counted dead by a kill command (before and after counts come from the mod)."""
    return answer["after"]["dead"] - answer["before"]["dead"]
