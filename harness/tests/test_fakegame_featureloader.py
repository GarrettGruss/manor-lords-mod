"""Tests for the feature loader of the mod pack (spec 22): order, cycle, missing feature, disabled feature, main.lua."""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from fakegame.game import REPO_ROOT



def find_pack_mod():
    """The mod that has a feature loader. The harness must not name the mod, so the test finds it by its files."""
    found = sorted((REPO_ROOT / "mod").glob("*/Scripts/feature_loader.lua"))
    assert len(found) == 1, f"expected one mod with Scripts/feature_loader.lua, found {found}"
    return found[0].parents[1]


PACK_MOD = find_pack_mod()
SCRIPTS = (PACK_MOD / "Scripts").as_posix()

RUN = """
function(features, config)
    local loader = require("feature_loader")
    local loaded, logs = {}, {}
    local ok, result = pcall(loader.load, features, config,
        function(path) loaded[#loaded + 1] = path end, function(message) logs[#logs + 1] = message end)
    return ok, result, loaded, logs
end
"""


def enabled(*names):
    return {name: {"enabled": True} for name in names}


class FeatureLoaderTests(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.game.exec(f'package.path = "{SCRIPTS}/?.lua;" .. package.path')
        self.run_lua = self.game.lua.eval(RUN)

    def load(self, features, config):
        table = self.game.lua.table_from
        lua_features = table([table({"name": f["name"], "requires": table(f.get("requires", []))}) for f in features])
        lua_config = table({name: table(entry) for name, entry in config.items()})
        ok, result, loaded, _logs = self.run_lua(lua_features, lua_config)
        return ok, result if not ok else list(result.values()), list(loaded.values())

    def test_features_load_after_the_features_they_require(self):
        features = [{"name": "b", "requires": ["a"]}, {"name": "a"}, {"name": "c", "requires": ["b"]}]
        ok, order, loaded = self.load(features, enabled("a", "b", "c"))
        self.assertTrue(ok)
        self.assertEqual(order, ["a", "b", "c"])
        self.assertEqual(loaded, ["features.a.init", "features.b.init", "features.c.init"])

    def test_a_cycle_fails_and_names_the_cycle(self):
        features = [{"name": "a", "requires": ["b"]}, {"name": "b", "requires": ["a"]}]
        ok, message, loaded = self.load(features, enabled("a", "b"))
        self.assertFalse(ok)
        self.assertIn("cycle: a -> b -> a", message)
        self.assertEqual(loaded, [])

    def test_a_missing_required_feature_fails(self):
        ok, message, _ = self.load([{"name": "a", "requires": ["ghost"]}], enabled("a"))
        self.assertFalse(ok)
        self.assertIn("requires 'ghost'", message)

    def test_a_config_entry_without_a_feature_fails(self):
        ok, message, _ = self.load([{"name": "a"}], enabled("a", "ghost"))
        self.assertFalse(ok)
        self.assertIn("unknown feature 'ghost'", message)

    def test_a_disabled_feature_is_not_loaded(self):
        ok, order, loaded = self.load([{"name": "a"}, {"name": "b"}], {"a": {"enabled": True}, "b": {"enabled": False}})
        self.assertTrue(ok)
        self.assertEqual(order, ["a"])
        self.assertEqual(loaded, ["features.a.init"])

    def test_a_feature_without_a_config_entry_is_disabled(self):
        ok, order, _ = self.load([{"name": "a"}, {"name": "b"}], enabled("a"))
        self.assertTrue(ok)
        self.assertEqual(order, ["a"])

    def test_an_enabled_feature_cannot_require_a_disabled_one(self):
        ok, message, _ = self.load([{"name": "a"}, {"name": "b", "requires": ["a"]}], {"a": {"enabled": False}, "b": {"enabled": True}})
        self.assertFalse(ok)
        self.assertIn("disabled", message)

    def test_a_failing_feature_stops_the_load_with_its_name(self):
        loader = self.game.lua.eval(
            'function() local l = require("feature_loader"); return pcall(l.load, {{name="a", requires={}}}, {a={enabled=true}},'
            ' function() error("boom") end, function() end) end')
        ok, message = loader()
        self.assertFalse(ok)
        self.assertIn("feature 'a' failed to load", message)


class MainAndListTests(unittest.TestCase):
    def test_the_feature_list_equals_mod_json(self):
        manifest = json.loads((PACK_MOD / "mod.json").read_text(encoding="utf-8"))
        if "features" not in manifest:
            self.skipTest("mod.json has no features field yet")
        with FakeGame() as game:
            game.exec(f'package.path = "{SCRIPTS}/?.lua;" .. package.path')
            lua_list = game.lua.eval('function() return (require("feature_list")) end')()
            from_lua = [{"name": f["name"], "requires": list(f["requires"].values())} for f in lua_list.values()]
        from_json = [{"name": f["name"], "requires": f["requires"]} for f in manifest["features"]]
        self.assertEqual(from_lua, from_json)

    def test_main_loads_the_stub_feature_and_logs_one_line(self):
        with FakeGame() as game:
            game.exec(f'package.path = "{SCRIPTS}/?.lua;{SCRIPTS}/?/init.lua;" .. package.path')
            game.load_mod(PACK_MOD.name)
            lines = game.log_lines()
        self.assertEqual(sum("example feature loaded" in line for line in lines), 1)
        self.assertTrue(any("ready, features: example, mod_state, invasion" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
