"""The request log of the UEBridge Lua mod (change add-bridge-request-log).

The mod runs in the fake game. A test writes request.json into the bridge folder of the run,
lets the fake time pass, and reads response.json and mod.log.
"""

import json
import re
import tempfile
import unittest
from pathlib import Path

import fakegame_path  # noqa: F401
from fakegame import FakeGame

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = (REPO_ROOT / "mod" / "UEBridge" / "scripts").as_posix()
SECRET_VALUE = "SECRET_PROPERTY_VALUE_71"
WRITTEN_VALUE = "WRITTEN_VALUE_88"
SECRET_SOURCE = "SECRET_LUA_SOURCE_42"
OBJECT_PATH = "/Game/Test.Widget"


class BridgeHarness:
    """Loads the bridge mod into a FakeGame and sends it requests through files."""

    def __init__(self, game, tmp, allow_eval):
        self.game = game
        mod_scripts = Path(tmp) / "ue4ss" / "Mods" / "UEBridge" / "scripts"
        mod_scripts.mkdir(parents=True)
        (mod_scripts / "settings.lua").write_text(
            f"return {{ allow_eval = {str(allow_eval).lower()} }}\n", encoding="utf-8")
        self.bridge = game.run_dir / "bridge"
        self.bridge.mkdir()
        game.exec(f'''
            package.path = "{SCRIPTS}/?.lua;" .. package.path
            package.preload["UEHelpers"] = function() return {{}} end
            function IterateGameDirectories()
                return {{ Game = {{ Binaries = {{ Win64 = {{ __absolute_path = "{Path(tmp).as_posix()}" }} }} }} }}
            end''')
        self._add_widget()
        game.load_script(SCRIPTS + "/main.lua")

    def _add_widget(self):
        game = self.game
        widget = game.obj("Widget", OBJECT_PATH, secret=SECRET_VALUE)
        prop = game.obj("Property")
        game.method(prop, "GetFName", lambda _self: game.text("secret"))
        class_object = game.fg.class_object("Widget")
        game.method(class_object, "ForEachProperty", lambda _self, callback: callback(prop))
        game.static(OBJECT_PATH, widget)

    def send(self, request):
        (self.bridge / "request.json").write_text(json.dumps(request), encoding="utf-8")
        self.game.advance(1)
        return json.loads((self.bridge / "response.json").read_text(encoding="utf-8"))

    def request_lines(self):
        return [line for line in self.game.log_lines() if "[UEBridge] request " in line]

    def log_text(self):
        return self.game.read_text("mod.log")


class BridgeRequestLogTests(unittest.TestCase):
    def run_bridge(self, allow_eval=False):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        game = FakeGame()
        game.start()
        self.addCleanup(game.close)
        return BridgeHarness(game, tmp.name, allow_eval)

    def test_a_read_request_logs_id_verb_target_and_duration(self):
        bridge = self.run_bridge()
        response = bridge.send({"id": "r1", "op": "batch",
                                "calls": [{"op": "get", "ref": OBJECT_PATH, "name": "secret"}]})
        self.assertTrue(response["ok"])
        lines = bridge.request_lines()
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"INFO \[UEBridge\] request id=r1 verb=get target=" + re.escape(OBJECT_PATH)
                         + r" ms=\d+ ok$")

    def test_a_failed_request_logs_the_error_text(self):
        bridge = self.run_bridge()
        bridge.send({"id": "r2", "op": "batch",
                     "calls": [{"op": "get", "ref": "/Game/Missing.Object", "name": "secret"}]})
        lines = bridge.request_lines()
        self.assertEqual(len(lines), 1)
        self.assertIn("WARN [UEBridge] request id=r2 verb=get target=/Game/Missing.Object", lines[0])
        self.assertIn("FAILED error=", lines[0])
        self.assertIn("object not found: /Game/Missing.Object", lines[0])

    def test_an_eval_request_logs_the_verb_but_not_the_lua_source(self):
        bridge = self.run_bridge(allow_eval=True)
        response = bridge.send({"id": "r3", "op": "eval", "code": f'return "{SECRET_SOURCE}"'})
        self.assertTrue(response["ok"])
        lines = bridge.request_lines()
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"request id=r3 verb=eval target=- ms=\d+ ok$")
        self.assertNotIn(SECRET_SOURCE, bridge.log_text())

    def test_no_property_value_reaches_the_log(self):
        bridge = self.run_bridge()
        bridge.send({"id": "r4", "op": "batch", "calls": [
            {"op": "get", "ref": OBJECT_PATH, "name": "secret"},
            {"op": "set", "ref": OBJECT_PATH, "name": "secret", "value": WRITTEN_VALUE}]})
        log = bridge.log_text()
        self.assertNotIn(SECRET_VALUE, log)
        self.assertNotIn(WRITTEN_VALUE, log)


if __name__ == "__main__":
    unittest.main()
