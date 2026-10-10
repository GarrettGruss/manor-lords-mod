"""Assertions for scenarios (spec 04, Part C).

Each assertion adds one short record {name, ok, value, rule}. The records go into scenario.json and summary.json.
The simulation is not deterministic, so use ranges for numbers. Use `equals` only for flags and names.
"""

from __future__ import annotations

import time
from typing import Any, Callable

MAX_RULE_CHARS = 60  # keeps a record short, so summary.json stays under 4 KB
POLL_S = 0.5


def _number(value: Any) -> str:
    return f"{value:g}" if isinstance(value, (int, float)) and not isinstance(value, bool) else repr(value)


class Expectations:
    def __init__(self, log: Callable[[str], None] = lambda message: None,
                 sleep: Callable[[float], None] = time.sleep, monotonic: Callable[[], float] = time.monotonic):
        self.records: list[dict] = []
        self._log = log
        self._sleep = sleep
        self._monotonic = monotonic

    def record(self, name: str, ok: bool, value: Any, rule: str) -> bool:
        entry = {"name": name, "ok": bool(ok), "value": value, "rule": rule[:MAX_RULE_CHARS]}
        self.records.append(entry)
        self._log(f"assert {'ok' if ok else 'FAILED'}: {name} value={value} rule={rule}")
        return entry["ok"]

    def in_range(self, name: str, value: float, lo: float, hi: float) -> bool:
        return self.record(name, value is not None and lo <= value <= hi, value, f"{_number(lo)}..{_number(hi)}")

    def at_least(self, name: str, value: float, lo: float) -> bool:
        return self.record(name, value is not None and value >= lo, value, f">={_number(lo)}")

    def at_most(self, name: str, value: float, hi: float) -> bool:
        return self.record(name, value is not None and value <= hi, value, f"<={_number(hi)}")

    def changed(self, name: str, before: float, after: float, min_delta: float | None = None, max_delta: float | None = None) -> bool:
        """The value moved. With no limits, any change counts. The limits apply to `after - before`."""
        if before is None or after is None:
            return self.record(name, False, None, "values must be numbers")
        delta = after - before
        ok = delta != 0 if min_delta is None and max_delta is None else (
            (min_delta is None or delta >= min_delta) and (max_delta is None or delta <= max_delta)
        )
        low = "" if min_delta is None else _number(min_delta)
        high = "" if max_delta is None else _number(max_delta)
        rule = "delta!=0" if min_delta is None and max_delta is None else f"delta {low}..{high}"
        return self.record(name, ok, delta, rule)

    def equals(self, name: str, value: Any, expected: Any) -> bool:
        return self.record(name, value == expected, value, f"=={_number(expected)}")

    def eventually(self, name: str, fn: Callable[[], Any], timeout_s: float) -> bool:
        """Poll `fn` until it returns a true value. The value of the record is the wait time in seconds."""
        started = self._monotonic()
        while True:
            if fn():
                return self.record(name, True, round(self._monotonic() - started, 1), f"true within {_number(timeout_s)}s")
            if self._monotonic() - started >= timeout_s:
                return self.record(name, False, round(self._monotonic() - started, 1), f"true within {_number(timeout_s)}s")
            self._sleep(POLL_S)

    def result(self) -> dict:
        return {"passed": all(item["ok"] for item in self.records), "asserts": list(self.records)}
