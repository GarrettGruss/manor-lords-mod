"""Tests for the pop-up actions and the pop-up helper of scenarios (spec 10, spike S8). No game."""

import unittest

import runlib_path  # noqa: F401
from runlib.actions import Actions
from runlib.expectations import Expectations
from runlib.popups import PopupGuard


class FakePopups:
    """Answers like the mod. `stuck` pop-ups stay open after close_popups."""

    def __init__(self, open_popups=(), stuck=False):
        self.open = list(open_popups)
        self.stuck = stuck
        self.sent = []

    def send(self, command, **fields):
        self.sent.append(command)
        if command == "popup_state":
            return {"ok": True, "widgets": len(self.open), "open": list(self.open)}
        closed = [] if self.stuck else list(self.open)
        if not self.stuck:
            self.open = []
        return {"ok": True, "widgets": len(closed), "closed": closed, "count": len(closed)}


class FakeBridge:
    def engine_path(self):
        return "engine"


def make(popups):
    expect = Expectations()
    return Actions(FakeBridge(), expect, [], commands=popups), expect


class PopupActionTests(unittest.TestCase):
    def test_close_popups_closes_an_open_popup(self):
        actions, expect = make(FakePopups(["hunger"]))
        record = actions.close_popups()
        self.assertEqual((record["ok"], record["before"], record["after"]), (True, 1, 0))
        self.assertIn("hunger", record["note"])
        self.assertTrue(expect.result()["passed"])

    def test_nothing_open_is_ok(self):
        actions, _ = make(FakePopups())
        record = actions.close_popups()
        self.assertEqual((record["ok"], record["before"], record["after"]), (True, 0, 0))

    def test_a_popup_that_stays_open_fails_the_scenario(self):
        actions, expect = make(FakePopups(["hunger"], stuck=True))
        self.assertFalse(actions.close_popups()["ok"])
        self.assertFalse(expect.result()["passed"])

    def test_popup_state_is_read_only(self):
        popups = FakePopups(["hunger"])
        actions, _ = make(popups)
        self.assertEqual(actions.popup_state()["open"], ["hunger"])
        self.assertEqual(popups.sent, ["popup_state"])
        self.assertIn("close_popups", actions.available())


class PopupGuardTests(unittest.TestCase):
    def test_guard_counts_what_it_closed(self):
        popups = FakePopups(["hunger"])
        guard = PopupGuard(lambda: popups.send("close_popups"))
        guard()
        popups.open = ["starvation"]
        guard()
        guard()
        self.assertEqual(guard.closed, ["hunger", "starvation"])
        self.assertEqual(guard.calls, 3)

    def test_guard_survives_an_answer_without_a_list(self):
        guard = PopupGuard(lambda: {"ok": True})
        guard()
        self.assertEqual(guard.closed, [])


if __name__ == "__main__":
    unittest.main()
