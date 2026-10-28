"""Tests for the shared module ModState and the mod_state feature of the pack mod (mod feature M01, iteration 01).

The fake game has no FName, so the test defines one. The Tags array is a fake TArray of those names.
"""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from fakegame.game import REPO_ROOT

FNAME = """
FName = function(text)
    return setmetatable({ text = text }, { __index = { ToString = function(self) return self.text end } })
end
"""

HELPERS = """
function make_world(names)
    local items = {}
    for index, text in ipairs(names) do items[index] = FName(text) end
    return items
end
function tag_names(pawn)
    local out = {}
    for index = 1, #pawn.Tags do out[#out + 1] = pawn.Tags[index]:ToString() end
    return out
end
"""

BEGIN_PLAY = "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ReceiveBeginPlay"


def find_pack_mod():
    found = sorted((REPO_ROOT / "mod").glob("*/Scripts/feature_loader.lua"))
    assert len(found) == 1, f"expected one mod with Scripts/feature_loader.lua, found {found}"
    return found[0].parents[1]


class ModStateTestCase(unittest.TestCase):
    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        self.game.exec(FNAME + HELPERS)
        self.game.exec('ModState = require("ModState")')

    def make_pawn(self, names=()):
        lua = self.game.lua
        items = lua.eval("make_world")(lua.table_from(list(names)))
        self.pawn = self.game.obj("PawnCPP", Tags=self.game.array(items.values()))
        if getattr(self, "engine", None) is None:
            self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn)
        self.engine.playerRef = self.pawn
        return self.pawn

    def tags(self):
        return list(self.game.lua.eval("tag_names")(self.pawn).values())

    def open_state(self, version=None):
        self.game.exec(
            "state = ModState.open('invasion', 'pawn', %s)\n"
            "state:register('count', 5, 'integer')\n"
            "state:register('flag', false, 'boolean')\n"
            "state:register('label', 'none', 'string')\n"
            "state:register('ratio', 0.5, 'number')" % ("nil" if version is None else version))

    def call_error(self, code):
        with self.assertRaises(Exception) as caught:
            self.game.exec(code)
        return str(caught.exception)


class DefaultTests(ModStateTestCase):
    def test_a_save_without_entries_gives_the_defaults(self):
        self.make_pawn()
        self.open_state()
        self.assertEqual(self.game.exec("return state:get('count')"), 5)
        self.assertEqual(self.game.exec("return state:get('flag')"), False)
        self.assertEqual(self.game.exec("return state:get('label')"), "none")
        self.assertEqual(self.tags(), [])

    def test_open_without_a_pawn_waits_and_load_reads_the_tags_later(self):
        self.open_state()
        self.assertFalse(self.game.exec("return state.loaded"))
        self.assertIn("not loaded yet", self.call_error("state:get('count')"))
        self.make_pawn(["invasion:count=9"])
        self.game.exec("state:load()")
        self.assertEqual(self.game.exec("return state:get('count')"), 9)


class ParseTests(ModStateTestCase):
    def test_entries_are_parsed_by_kind(self):
        self.make_pawn(["invasion:count=-12", "invasion:flag=true", "invasion:label=a.b-c_1", "invasion:ratio=0.25", "invasion:v=3"])
        self.open_state()
        self.assertEqual(self.game.exec("return state:get('count')"), -12)
        self.assertEqual(self.game.exec("return state:get('flag')"), True)
        self.assertEqual(self.game.exec("return state:get('label')"), "a.b-c_1")
        self.assertEqual(self.game.exec("return state:get('ratio')"), 0.25)
        self.assertEqual(self.game.exec("return state.stored_version"), 3)

    def test_a_bad_value_fails_loudly(self):
        self.make_pawn(["invasion:count=abc"])
        self.assertIn("bad entry 'invasion:count=abc'", self.call_error(
            "state = ModState.open('invasion', 'pawn'); state:register('count', 5, 'integer')"))

    def test_duplicate_entries_fail_loudly(self):
        self.make_pawn(["invasion:count=1", "invasion:count=2"])
        self.assertIn("duplicate entries", self.call_error(
            "state = ModState.open('invasion', 'pawn'); state:register('count', 5, 'integer')"))

    def test_an_entry_of_a_key_that_is_not_registered_is_kept_and_listed(self):
        self.make_pawn(["invasion:old_key=7"])
        self.open_state()
        self.game.exec("state:set('count', 6)")
        self.assertEqual(list(self.game.exec("return state.unknown").values()), ["invasion:old_key=7"])
        self.assertIn("invasion:old_key=7", self.tags())


class TypoTests(ModStateTestCase):
    def test_get_and_set_of_an_unregistered_key_fail_with_a_clear_message(self):
        self.make_pawn()
        self.open_state()
        for code in ("state:get('cuont')", "state:set('cuont', 1)"):
            message = self.call_error(code)
            self.assertIn("key 'cuont' is not registered for mod 'invasion'", message)

    def test_a_wrong_value_type_fails(self):
        self.make_pawn()
        self.open_state()
        self.assertIn("must be an integer", self.call_error("state:set('count', 1.5)"))
        self.assertIn("must be a boolean", self.call_error("state:set('flag', 1)"))
        self.assertIn("must be a string of", self.call_error("state:set('label', 'a=b')"))
        self.assertEqual(self.tags(), [])

    def test_a_key_registered_twice_or_with_a_bad_kind_fails(self):
        self.make_pawn()
        self.open_state()
        self.assertIn("registered twice", self.call_error("state:register('count', 1, 'integer')"))
        self.assertIn("unknown kind", self.call_error("state:register('other', 1, 'float')"))
        self.assertIn("bad key", self.call_error("state:register('v', 1, 'integer')"))


class FlushTests(ModStateTestCase):
    def test_set_writes_one_entry_per_key_and_the_version(self):
        self.make_pawn()
        self.open_state(version=1)
        self.game.exec("state:set('count', 10); state:set('count', 11); state:set('flag', true)")
        self.assertEqual(sorted(self.tags()), ["invasion:count=11", "invasion:flag=true", "invasion:v=1"])

    def test_a_change_overwrites_in_place_and_never_grows_the_array(self):
        self.make_pawn()
        self.open_state(version=1)
        self.game.exec("state:set('count', 10)")
        length = len(self.tags())
        for value in range(11, 30):
            self.game.exec(f"state:set('count', {value})")
        self.assertEqual(len(self.tags()), length)
        self.assertEqual(self.tags().count("invasion:count=29"), 1)

    def test_other_tags_are_not_changed_and_keep_their_place(self):
        foreign = ["strength_Salt", "invasion2:count=1", "church_lv1_constructed", "Invasion:count=3"]
        self.make_pawn(foreign[:2] + ["invasion:count=4"] + foreign[2:])
        self.open_state(version=1)
        self.game.exec("state:set('count', 8); state:set('label', 'abc')")
        tags = self.tags()
        self.assertEqual([t for t in tags if not t.startswith("invasion:")], foreign)
        self.assertEqual(tags[:3], ["strength_Salt", "invasion2:count=1", "invasion:count=8"])

    def test_the_same_value_writes_nothing(self):
        self.make_pawn(["invasion:count=5", "invasion:v=1"])
        self.open_state(version=1)
        self.game.exec("state:set('count', 5)")
        self.assertEqual(self.tags(), ["invasion:count=5", "invasion:v=1"])

    def test_autoflush_off_waits_for_flush(self):
        self.make_pawn()
        self.open_state()
        self.game.exec("state.autoflush = false; state:set('count', 2)")
        self.assertEqual(self.tags(), [])
        self.game.exec("state:flush()")
        self.assertEqual(self.tags(), ["invasion:count=2"])

    def test_a_reload_reads_back_what_was_written(self):
        self.make_pawn()
        self.open_state(version=2)
        self.game.exec("state:set('count', 42); state:set('label', 'x_1'); state:set('ratio', 0.1)")
        self.game.exec("state.values.count = 0; state:load()")
        self.assertEqual(self.game.exec("return state:get('count')"), 42)
        self.assertEqual(self.game.exec("return state:get('ratio')"), 0.1)
        self.assertEqual(self.game.exec("return state.stored_version"), 2)

    def test_open_again_gives_the_same_state_with_its_keys(self):
        self.make_pawn(["invasion:count=3"])
        self.open_state()
        self.assertTrue(self.game.exec("return ModState.open('invasion', 'pawn') == state"))
        self.assertEqual(self.game.exec("return ModState.open('invasion', 'pawn'):get('count')"), 3)

    def test_a_new_pawn_after_a_load_is_read_again(self):
        self.make_pawn(["invasion:count=3"])
        self.open_state()
        self.game.fg.invalidate(self.pawn)
        self.make_pawn(["invasion:count=77"])
        self.game.exec("state:load()")
        self.assertEqual(self.game.exec("return state:get('count')"), 77)

    def test_set_without_a_pawn_fails_loudly(self):
        self.make_pawn()
        self.open_state()
        self.game.fg.invalidate(self.pawn)
        self.assertIn("no live player pawn", self.call_error("state:set('count', 1)"))


class FeatureTests(unittest.TestCase):
    """The feature file in the real mod: keys from config, the hook, the named commands."""

    def setUp(self):
        self.game = FakeGame()
        self.game.start()
        self.addCleanup(self.game.close)
        pack = find_pack_mod()
        self.mod_name = pack.name
        self.game.exec(f'package.path = "{(pack / "Scripts").as_posix()}/?.lua;" .. package.path')
        self.game.exec(FNAME + HELPERS)
        self.items = self.game.lua.eval("make_world")(self.game.lua.table_from(["strength_Salt"]))
        self.pawn = self.game.obj("PawnCPP", Tags=self.game.array(self.items.values()))
        self.engine = self.game.obj("RTSMultiEngineCPP", playerRef=self.pawn)

    def load_mod(self):
        self.game.load_mod(self.mod_name)
        self.game.advance(1)

    def command(self, number, name, **args):
        folder = self.game.run_dir / "modcmd" / self.mod_name
        folder.mkdir(parents=True, exist_ok=True)
        body = {"id": f"{number:04d}", "command": f"{self.mod_name}.{name}", "args": args}
        (folder / f"{number:04d}.json").write_text(json.dumps(body), encoding="utf-8")
        self.game.advance(1)
        return json.loads((folder / f"{number:04d}.result.json").read_text(encoding="utf-8"))

    def test_the_mod_loads_the_feature_and_dump_shows_defaults(self):
        self.load_mod()
        answer = self.command(1, "mod_state_dump")
        self.assertTrue(answer["ok"], answer)
        result = answer["result"]
        self.assertEqual(result["values"], {"selftest_int": 0, "selftest_flag": False, "selftest_text": "none"})
        self.assertEqual(result["tags"], ["strength_Salt"])

    def test_set_get_and_a_typo(self):
        self.load_mod()
        self.assertTrue(self.command(1, "mod_state_set", key="selftest_int", value="41")["ok"])
        self.assertTrue(self.command(2, "mod_state_set", key="selftest_flag", value="true")["ok"])
        self.assertTrue(self.command(3, "mod_state_set", key="selftest_text", value="abc_1")["ok"])
        dump = self.command(4, "mod_state_dump")["result"]
        self.assertEqual(dump["values"], {"selftest_int": 41, "selftest_flag": True, "selftest_text": "abc_1"})
        # The version entry is the version of the feature that opened the state last: liege_contracts (2) since change update-liege-tribute-to-contracts.
        expected = ["strength_Salt", "invasion:selftest_int=41", "invasion:selftest_flag=true", "invasion:selftest_text=abc_1", "invasion:v=2"]
        self.assertEqual(sorted(dump["tags"]), sorted(expected))
        typo = self.command(5, "mod_state_set", key="selftest_itn", value="1")
        self.assertFalse(typo["ok"])
        self.assertIn("not registered", typo["error"])
        self.assertFalse(self.command(6, "mod_state_get", key="selftest_itn")["ok"])
        self.assertFalse(self.command(7, "mod_state_set", key="selftest_int", value="x")["ok"])

    def test_the_begin_play_hook_loads_the_tags_after_a_game_load(self):
        self.load_mod()
        self.game.advance(4)
        self.assertIn(BEGIN_PLAY, self.game.fg.hooks)
        loaded = self.game.lua.eval("make_world")(self.game.lua.table_from(["invasion:selftest_int=9", "invasion:v=1"]))
        new_pawn = self.game.obj("PawnCPP", Tags=self.game.array(loaded.values()))
        self.game.fg.invalidate(self.pawn)
        self.game.fire_hook(BEGIN_PLAY, new_pawn)
        self.game.advance(1)  # the engine does not hold the new pawn yet, as in the real game
        self.engine.playerRef = new_pawn
        self.game.advance(1)
        self.assertEqual(self.command(1, "mod_state_dump")["result"]["values"]["selftest_int"], 9)

    def test_the_foreign_tag_command_accepts_only_test_tags(self):
        self.load_mod()
        self.assertTrue(self.command(1, "mod_state_add_foreign_tag", tag="mstest_a")["ok"])
        self.assertFalse(self.command(2, "mod_state_add_foreign_tag", tag="church_lv1")["ok"])
        self.assertEqual(self.command(3, "mod_state_dump")["result"]["tags"], ["strength_Salt", "mstest_a"])


    def test_the_tags_limit_commands_write_and_read_entries_on_the_pawn(self):
        self.load_mod()
        wrote = self.command(1, "tags_limit_write", target="pawn", label="ten", count=10, size=40)
        self.assertTrue(wrote["ok"], wrote)
        self.assertEqual(wrote["result"]["added"], 10)
        read = self.command(2, "tags_limit_read", target="pawn", label="ten")["result"]
        self.assertEqual(read["entry_count"], 10)
        self.assertEqual(read["longest"], 44)
        self.assertEqual(self.command(3, "tags_limit_read", target="pawn", label="other")["result"]["entry_count"], 0)

    def test_the_tags_limit_commands_use_a_lord_and_fail_without_a_target(self):
        self.load_mod()
        self.game.obj("PawnCPP_AI", Tags=self.game.array([]))
        self.assertTrue(self.command(1, "tags_limit_write", target="lord", label="mrk", count=1, size=40)["ok"])
        self.assertEqual(self.command(2, "tags_limit_read", target="lord", label="mrk")["result"]["entry_count"], 1)
        missing = self.command(3, "tags_limit_read", target="building", label="mrk")
        self.assertFalse(missing["ok"])
        self.assertIn("no target", missing["error"])


if __name__ == "__main__":
    unittest.main()
