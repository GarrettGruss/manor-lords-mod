"""Tests for the feature scenario_settings (change add-scenario-settings-menu, #375) in the fake game.

They run the real Lua files. The fake game has no widgets, so the widget part of the base menu is replaced by a small stand-in
(the menu is "open" while a flag is set). They prove the logic: the new game detection, the pause, the settings and their effects
on the raid plan, the commands. The look and the real clicks are proven by the test scenario `scenario-settings-new-game-menu`.
"""

import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame
from test_fakegame_invasion import InvasionTestCase
from test_fakegame_modstate import find_pack_mod

DEFAULTS = {"yearly": 2, "great": 2, "vassal": 2, "first_raid_years": 2, "size_class": 2}
KEYS = ("yearly", "great", "vassal", "first_raid_years", "size_class")

STAND_IN_MENU = """
local menu = require("core.menu")
local feature = require("features.scenario_settings.init")
T = { open = false, opens = 0, closes = 0 }
menu.open = function() T.open = true; T.opens = T.opens + 1; return { ok = true } end
menu.is_open = function() return T.open end
menu.close = function() if T.open then T.open = false; T.closes = T.closes + 1; feature.on_close() end return { ok = true } end
"""


class RulesTests(unittest.TestCase):
    def run_lua(self, code):
        game = FakeGame()
        game.start()
        self.addCleanup(game.close)
        game.exec(f'package.path = "{(find_pack_mod() / "Scripts").as_posix()}/?.lua;" .. package.path')
        game.exec("config = require('config').scenario_settings; rules = require('features.scenario_settings.rules')")
        return game.lua.eval(f"(function() {code} end)")()

    def test_the_defaults_are_level_2_for_each_raid_type_two_years_medium(self):
        text = self.run_lua("local d = rules.defaults(config); return table.concat({ d.yearly, d.great, d.vassal, d.first_raid_years, d.size_class }, ',')")
        self.assertEqual(text, "2,2,2,2,2")

    def test_there_is_no_global_difficulty_row(self):
        self.assertEqual(self.run_lua("local keys = {}; for _, row in ipairs(rules.ROWS) do keys[#keys + 1] = row.key end; return table.concat(keys, ',')"),
                         "yearly,great,vassal,first_raid_years,size_class")

    def test_a_click_chooses_a_value_and_use_defaults_resets_all_five(self):
        text = self.run_lua("""
            local s = rules.defaults(config)
            for _, c in ipairs({ { 'yearly', 3 }, { 'great', 0 }, { 'vassal', 1 }, { 'first_raid_years', 3 }, { 'size_class', 3 } }) do
                s = rules.click(s, config, 'choose', c[1], c[2])
            end
            local changed = table.concat({ s.yearly, s.great, s.vassal, s.first_raid_years, s.size_class }, ',')
            local reset = rules.click(s, config, 'defaults')
            return changed .. '|' .. table.concat({ reset.yearly, reset.great, reset.vassal, reset.first_raid_years, reset.size_class }, ',')""")
        self.assertEqual(text, "3,0,1,3,3|2,2,2,2,2")

    def test_begin_keeps_the_selection_and_asks_to_close(self):
        self.assertEqual(self.run_lua("local s, begin = rules.click(rules.defaults(config), config, 'begin'); return tostring(begin) .. s.yearly"), "true2")

    def test_a_bad_choice_is_refused(self):
        self.assertEqual(self.run_lua("local s, problem = rules.click(rules.defaults(config), config, 'choose', 'yearly', 4); return tostring(s) .. '|' .. problem"),
                         "nil|setting yearly: 4 is not a valid choice")
        self.assertEqual(self.run_lua("return tostring(rules.click(rules.defaults(config), config, 'choose', 'difficulty', 2))"), "nil")

    def test_every_level_0_to_3_is_a_choice_of_each_raid_type(self):
        self.assertEqual(self.run_lua("""
            local out = {}
            for _, key in ipairs({ 'yearly', 'great', 'vassal' }) do
                for level = 0, 3 do out[#out + 1] = tostring(rules.is_valid_value(key, level)) end
            end
            return table.concat(out, ',')"""), ",".join(["true"] * 12))

    def test_the_chosen_button_is_marked(self):
        self.assertEqual(self.run_lua("return rules.choice_text(config, 'yearly', 3, true) .. '|' .. rules.choice_text(config, 'yearly', 1, false)"), "> Medium <|Off")
        self.assertEqual(self.run_lua("return rules.selected_index(rules.defaults(config), 'great')"), 3)

    def test_the_two_cases_of_a_new_game(self):
        kinds = self.run_lua("""
            local function kind(info) return rules.kind_of_game(info, config) end
            return table.concat({
                kind({ save_file = '', applied = 0, day = 1 }),
                kind({ save_file = 'saveGame_3', applied = 0, day = 1 }),
                kind({ save_file = '', applied = 1, day = 400 }),
                kind({ save_file = '', applied = 0, day = 400 }),
                kind({ save_file = nil, applied = 0, day = 1 }),
            }, ',')""")
        self.assertEqual(kinds, "new,old_save,loaded,old_save,unknown")


DEFAULTS_BEFORE_MENU = {"yearly": 2, "great": 2, "vassal": 2, "first_raid_years": 1, "size_class": 2}


class SettingsTestCase(InvasionTestCase):
    PLAN_AT_START = False

    def setUp(self):
        super().setUp()
        self.pauses, self.unpauses = [], []
        self.game.method(self.pawn, "pauseGame", lambda _self: self.pauses.append(1))
        self.game.method(self.pawn, "unPauseGame", lambda _self: self.unpauses.append(1))
        self.speeds = []
        self.game.method(self.pawn, "changeGameSpeed", lambda _self, speed, _flag: self.speeds.append(speed))

    def stand_in_menu(self):
        self.game.exec(STAND_IN_MENU, state=self.mod_name)

    def menu_flag(self, name):
        return self.game.exec(f"return T.{name}", state=self.mod_name)

    def start_game(self, save_file, day):
        """Makes the game instance (the first read that can tell a new game from a loaded one) at the given day."""
        self.calendar.daysTotal = day
        self.game.obj("MLGameInstance", savefileToLoad=self.game.text(save_file))
        self.game.advance(2)

    def settings(self):
        answer = self.ask("scenario_settings_state")
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def values(self):
        state = self.settings()
        return {key: state[key] for key in DEFAULTS}


class NewGameTests(SettingsTestCase):
    def test_a_new_game_opens_the_menu_and_pauses_until_begin(self):
        self.stand_in_menu()
        self.start_game("", 1)
        state = self.settings()
        self.assertEqual((state["kind"], state["open"], state["paused"]), ("opened", True, True))
        self.assertEqual(self.pauses, [1])
        self.assertEqual(self.unpauses, [])
        self.assertFalse(state["settings_applied"])
        self.ask("scenario_settings_click", action="choose", key="yearly", value=3)
        self.ask("scenario_settings_click", action="choose", key="great", value=0)
        self.ask("scenario_settings_click", action="choose", key="vassal", value=1)
        self.ask("scenario_settings_click", action="choose", key="first_raid_years", value=3)
        self.ask("scenario_settings_click", action="choose", key="size_class", value=3)
        self.assertEqual(self.unpauses, [], "the game stays paused while the player chooses")
        self.ask("scenario_settings_click", action="begin")
        state = self.settings()
        self.assertEqual((state["open"], state["settings_applied"], state["difficulty_chosen"]), (False, True, True))
        self.assertEqual(self.values(), {"yearly": 3, "great": 0, "vassal": 1, "first_raid_years": 3, "size_class": 3})
        self.assertEqual(self.unpauses, [1])
        self.assertEqual(self.menu_flag("opens"), 1)
        self.assertEqual(self.speeds, [1], "a new game starts at speed 0: Begin sets the speed")

    def test_use_defaults_resets_the_choices_and_begin_applies_them(self):
        self.stand_in_menu()
        self.start_game("", 1)
        self.ask("scenario_settings_click", action="choose", key="yearly", value=1)
        self.ask("scenario_settings_click", action="choose", key="great", value=0)
        self.assertEqual(self.settings()["selection"]["yearly"], 1)
        self.ask("scenario_settings_click", action="defaults")
        self.assertEqual({k: self.settings()["selection"][k] for k in DEFAULTS}, DEFAULTS)
        self.ask("scenario_settings_click", action="begin")
        self.assertEqual(self.values(), DEFAULTS)

    def test_a_new_game_holds_the_daily_step_until_begin(self):
        self.stand_in_menu()
        self.start_game("", 1)
        self.banners.clear()
        for _ in range(3):
            self.set_day(self.calendar.daysTotal + 1)
        self.assertEqual(self.banners, [], "no pick banner and no clock banner while the menu is open")
        self.ask("scenario_settings_click", action="choose", key="great", value=0)
        self.ask("scenario_settings_click", action="begin")
        self.set_day(self.calendar.daysTotal + 1)
        self.assertEqual(self.ask("invasion_clock_state")["result"]["great_raid_day"], 0, "Great raid level 0: no clock")
        self.assertEqual([t for t in self.banners if t.startswith("Pick the difficulty")], [])

    def test_the_menu_does_not_open_twice_in_one_session(self):
        self.stand_in_menu()
        self.start_game("", 1)
        self.ask("scenario_settings_click", action="begin")
        self.game.advance(3)
        self.assertEqual(self.menu_flag("opens"), 1)
        self.assertEqual(self.pauses, [1])

    def test_a_menu_that_cannot_open_applies_the_defaults_and_does_not_pause(self):
        # No pak in the fake game: the base menu cannot make the widget.
        self.start_game("", 1)
        state = self.settings()
        self.assertEqual((state["open"], state["paused"], state["settings_applied"]), (False, False, True))
        self.assertEqual(self.values(), DEFAULTS)
        self.assertEqual(self.pauses, [])
        self.assertTrue(state["last_error"])

    def test_the_menu_waits_while_the_game_instance_is_unknown(self):
        self.stand_in_menu()
        self.game.advance(3)
        state = self.settings()
        self.assertEqual((state["decided"], state["open"], state["settings_applied"]), (False, False, False))
        self.assertEqual(self.pauses, [])


class LoadedGameTests(SettingsTestCase):
    def test_a_loaded_save_does_not_open_the_menu_and_does_not_pause(self):
        self.stand_in_menu()
        self.start_game("saveGame_4", 61)
        state = self.settings()
        self.assertEqual((state["kind"], state["open"], state["paused"]), ("old_save", False, False))
        self.assertEqual(self.pauses, [])
        self.assertEqual(self.menu_flag("opens"), 0)

    def test_an_old_save_without_settings_gets_the_defaults_and_keeps_the_pick_open(self):
        self.start_game("saveGame_4", 61)
        state = self.settings()
        self.assertTrue(state["settings_applied"])
        self.assertEqual(self.values(), DEFAULTS)
        self.assertFalse(state["difficulty_chosen"], "the defaults are not a pick: the harness may still pick once")

    def test_a_save_with_settings_keeps_them(self):
        self.ask("scenario_settings_set", yearly=3, great=0, vassal=1, first_raid_years=1, size_class=1)
        self.stand_in_menu()
        self.start_game("saveGame_4", 61)
        self.assertTrue(self.settings()["decided"])
        self.assertEqual(self.values(), {"yearly": 3, "great": 0, "vassal": 1, "first_raid_years": 1, "size_class": 1})
        self.assertEqual(self.menu_flag("opens"), 0)

    def test_a_game_with_a_day_far_from_the_start_is_not_new_even_without_a_save_file_name(self):
        self.stand_in_menu()
        self.start_game("", 200)
        self.assertEqual(self.settings()["kind"], "old_save")
        self.assertEqual(self.menu_flag("opens"), 0)


class CommandTests(SettingsTestCase):
    def test_skip_applies_the_defaults(self):
        answer = self.ask("scenario_settings_skip")
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.values(), DEFAULTS)
        self.assertTrue(self.settings()["settings_applied"])
        self.assertFalse(self.settings()["open"])

    def test_set_chooses_values_and_reads_them_back(self):
        answer = self.ask("scenario_settings_set", yearly=3, great=0, vassal=1, first_raid_years=1, size_class=1)
        self.assertTrue(answer["ok"], answer)
        self.assertEqual(self.values(), {"yearly": 3, "great": 0, "vassal": 1, "first_raid_years": 1, "size_class": 1})

    def test_set_changes_only_the_named_settings(self):
        self.ask("scenario_settings_set", yearly=3, first_raid_years=1)
        self.ask("scenario_settings_set", great=0)
        self.assertEqual(self.values(), {"yearly": 3, "great": 0, "vassal": 2, "first_raid_years": 1, "size_class": 2})

    def test_a_value_outside_the_choices_is_refused(self):
        self.assertFalse(self.ask("scenario_settings_set", yearly=4)["ok"])
        self.assertFalse(self.ask("scenario_settings_set", vassal=-1)["ok"])
        self.assertEqual(self.values(), DEFAULTS_BEFORE_MENU)
        self.assertFalse(self.ask("scenario_settings_set", first_raid_years=0)["ok"])

    def test_a_click_without_an_open_menu_is_refused(self):
        self.assertFalse(self.ask("scenario_settings_click", action="begin")["ok"])

    def test_open_pauses_and_skip_closes_and_unpauses(self):
        self.stand_in_menu()
        self.assertTrue(self.ask("scenario_settings_open")["ok"])
        self.assertEqual(self.pauses, [1])
        self.ask("scenario_settings_skip")
        self.assertEqual(self.unpauses, [1])
        self.assertEqual(self.values(), DEFAULTS)


class LevelTests(SettingsTestCase):
    """Each raid type reads its own level (change update-raid-difficulty-levels, #404)."""

    def levels(self):
        info = self.ask("invasion_difficulty_state")["result"]
        return info["yearly"], info["great"], info["vassal"]

    def test_set_level_changes_one_raid_type(self):
        self.ask("scenario_settings_skip")
        self.assertEqual(self.levels(), (2, 2, 2))
        self.assertTrue(self.ask("invasion_set_level", kind="great", value=3)["ok"])
        self.assertEqual(self.levels(), (2, 3, 2))
        self.assertTrue(self.ask("invasion_set_level", kind="vassal", value=0)["ok"])
        self.assertEqual(self.levels(), (2, 3, 0))

    def test_set_difficulty_sets_all_three_levels(self):
        for value in (0, 1, 2, 3):
            self.assertTrue(self.ask("invasion_set_difficulty", value=value)["ok"])
            self.assertEqual(self.levels(), (value, value, value))

    def test_the_yearly_squads_follow_the_yearly_level_only(self):
        self.ask("scenario_settings_set", size_class=2)
        self.ask("invasion_plan_now", kind="plunder")
        for level, squads in ((1, 2), (2, 4), (3, 6)):
            self.ask("invasion_set_level", kind="great", value=4 - level)
            self.ask("invasion_set_level", kind="yearly", value=level)
            self.assertEqual(self.state()["squads"], squads, level)

    def test_the_vassal_squads_follow_the_vassal_level_only(self):
        self.ask("scenario_settings_skip")
        self.ask("invasion_plan_now", kind="plunder")
        self.ask("invasion_force_next")
        self.set_day(self.calendar.daysTotal + 1)
        self.ask("invasion_set_level", kind="yearly", value=3)
        self.assertTrue(self.ask("invasion_plan_now", kind="subjugation")["ok"])
        for level in (1, 2, 3):
            self.ask("invasion_set_level", kind="vassal", value=level)
            self.assertEqual(self.ask("invasion_subjugation_state")["result"]["squads"], 3 * level)

    def test_the_great_raid_waves_and_relief_follow_the_great_level_only(self):
        self.ask("scenario_settings_skip")
        self.ask("invasion_set_level", kind="yearly", value=3)
        seen = []
        for level in (1, 2, 3):
            self.ask("invasion_set_level", kind="great", value=level)
            info = self.ask("invasion_great_state")["result"]
            seen.append((info["waves"], info["relief_squads"]))
        self.assertEqual(seen, [(1, 15), (2, 8), (3, 0)])

    def test_yearly_level_0_plans_no_raid_and_clears_a_plan(self):
        self.ask("invasion_plan_now", kind="plunder")
        self.assertGreater(self.state()["squads"], 0)
        self.ask("invasion_set_level", kind="yearly", value=0)
        state = self.state()
        self.assertEqual((state["raid_day"], state["squads"]), (0, 0))
        self.assertFalse(self.ask("invasion_plan_now", kind="plunder")["ok"])
        self.assertFalse(self.ask("invasion_force_next")["ok"])
        self.ask("scenario_settings_set", first_raid_years=1)
        planned = [self.ask("invasion_yearly_advance_season", roll=0.0)["result"]["planned"] for _ in range(8)]
        self.assertEqual(planned, [False] * 8)
        self.banners.clear()
        for _ in range(200):
            self.set_day(self.calendar.daysTotal + 1)
        self.assertEqual((self.state()["raids_spawned"], self.raids, self.armies), (0, [], []))
        self.assertEqual([t for t in self.banners if t.startswith(("Raiders", "Subjugation", "Hussite"))], [])

    def test_vassal_level_0_plans_no_subjugation_raid(self):
        self.ask("scenario_settings_skip")
        self.ask("invasion_set_level", kind="vassal", value=0)
        self.ask("invasion_plan_now", kind="plunder")
        self.ask("invasion_force_next")
        self.set_day(self.calendar.daysTotal + 1)
        self.assertEqual(self.state()["raids_spawned"], 1)
        self.assertFalse(self.ask("invasion_plan_now", kind="subjugation")["ok"])
        self.assertEqual(self.ask("invasion_subjugation_state")["result"]["sub_day"], 0)
        # the next yearly roll plans a plunder raid, not a subjugation raid
        self.ask("scenario_settings_set", first_raid_years=1)
        self.ask("invasion_yearly_advance_season", roll=0.0)
        self.assertEqual(self.ask("invasion_subjugation_state")["result"]["sub_day"], 0)

    def test_vassal_level_0_clears_a_planned_subjugation_raid(self):
        self.ask("scenario_settings_skip")
        self.ask("invasion_plan_now", kind="plunder")
        self.ask("invasion_force_next")
        self.set_day(self.calendar.daysTotal + 1)
        self.assertTrue(self.ask("invasion_plan_now", kind="subjugation")["ok"])
        self.assertGreater(self.ask("invasion_subjugation_state")["result"]["sub_day"], 0)
        self.ask("invasion_set_level", kind="vassal", value=0)
        self.assertEqual(self.ask("invasion_subjugation_state")["result"]["sub_day"], 0)

    def test_great_level_0_blocks_the_great_raid_commands(self):
        self.ask("invasion_set_level", kind="great", value=0)
        self.assertFalse(self.ask("invasion_great_force_start")["ok"])
        self.assertEqual(self.ask("invasion_great_state")["result"]["waves"], 0)

    def test_the_levels_are_independent_of_each_other(self):
        self.ask("scenario_settings_set", yearly=0, great=3, vassal=1)
        self.assertEqual(self.levels(), (0, 3, 1))
        self.assertGreater(self.ask("invasion_clock_state")["result"]["great_raid_day"], 0)
        self.set_day(self.calendar.daysTotal + 1)
        self.assertGreater(self.ask("invasion_clock_state")["result"]["great_raid_day"], 0, "the clock runs at level 3 while the yearly level is 0")


class EffectTests(SettingsTestCase):
    def advance_season(self, roll):
        answer = self.ask("invasion_yearly_advance_season", roll=roll)
        self.assertTrue(answer["ok"], answer)
        return answer["result"]

    def test_no_raid_comes_before_the_first_raid_year(self):
        # 2 years: no raid in years 1 and 2 (8 season changes), then the roll of year 3 plans one.
        self.ask("scenario_settings_set", first_raid_years=2)
        planned = [self.advance_season(0.0)["planned"] for _ in range(7)]
        self.assertEqual(planned, [False] * 7, "season changes 1 to 7 are in years 1 and 2")
        answer = self.advance_season(0.0)
        self.assertEqual((answer["year"], answer["position"], answer["planned"]), (3, 1, True), answer)

    def test_one_year_delay_is_the_old_year_two(self):
        self.ask("scenario_settings_set", first_raid_years=1)
        planned = [self.advance_season(0.0)["planned"] for _ in range(3)]
        self.assertEqual(planned, [False, False, False])
        answer = self.advance_season(0.0)
        self.assertEqual((answer["year"], answer["planned"]), (2, True))

    def test_three_years_means_year_four_and_the_last_season_always_raids(self):
        self.ask("scenario_settings_set", first_raid_years=3)
        for _ in range(11):
            self.assertFalse(self.advance_season(0.0)["planned"])
        answer = self.advance_season(0.9)  # season 12 of the game: the first season of year 4, the roll fails
        self.assertEqual((answer["year"], answer["position"], answer["planned"]), (4, 1, False))
        for _ in range(2):
            self.assertFalse(self.advance_season(0.9)["planned"])
        self.assertTrue(self.advance_season(0.9)["planned"], "the fourth season of the first raid year always raids")

    def test_a_fixed_size_class_is_used_for_every_plan(self):
        self.ask("scenario_settings_set", yearly=2, size_class=3)
        for _ in range(6):
            self.assertTrue(self.ask("invasion_plan_now", kind="plunder")["ok"])
            state = self.state()
            self.assertEqual((state["size_class"], state["squads"]), (3, 6))
            self.ask("invasion_force_next")
            self.set_day(self.calendar.daysTotal + 1)
            self.assertEqual(self.state()["raids_spawned"] >= 1, True)
            self.set_day(self.calendar.daysTotal + 1)

    def test_without_a_setting_the_size_class_is_random_as_before(self):
        sizes = set()
        for _ in range(12):
            self.ask("invasion_plan_now", kind="plunder")
            sizes.add(self.state()["size_class"])
            self.ask("invasion_force_next")
            self.set_day(self.calendar.daysTotal + 1)
            self.set_day(self.calendar.daysTotal + 1)
        self.assertGreater(len(sizes), 1)

    def test_great_raid_level_0_stops_the_clock_and_the_banner(self):
        self.assertGreater(self.ask("invasion_clock_state")["result"]["great_raid_day"], 0, "the clock runs by default")
        self.ask("scenario_settings_set", great=0)
        self.assertEqual(self.ask("invasion_clock_state")["result"]["great_raid_day"], 0)
        self.banners.clear()
        for _ in range(3):
            self.set_day(self.calendar.daysTotal + 1)
        self.assertEqual(self.ask("invasion_clock_state")["result"]["great_raid_day"], 0)
        self.assertEqual(self.ask("invasion_great_state")["result"]["phase"], 0)
        self.assertEqual([text for text in self.banners if text.startswith(("Great raid", "The great raid"))], [])
        self.assertEqual(self.ask("raid_widget_state")["result"]["wanted_lines"][2], "")

    def test_great_raid_level_1_runs_the_clock_again(self):
        self.ask("scenario_settings_set", great=0)
        self.ask("scenario_settings_set", great=1)
        self.set_day(self.calendar.daysTotal + 1)
        self.assertGreater(self.ask("invasion_clock_state")["result"]["great_raid_day"], 0)

    def test_a_minor_raid_banner_has_no_clock_subtitle_when_the_great_raid_is_off(self):
        self.ask("scenario_settings_set", great=0)
        self.ask("invasion_plan_now", kind="plunder")
        self.ask("invasion_force_next")
        self.set_day(self.calendar.daysTotal + 1)
        self.assertEqual(self.state()["raids_spawned"], 1)
        self.assertEqual(len(self.armies), 1)


class DifficultyTests(SettingsTestCase):
    def test_set_difficulty_marks_it_as_chosen_and_a_later_pick_is_refused(self):
        self.assertFalse(self.ask("invasion_difficulty_state")["result"]["chosen"])
        self.ask("invasion_set_difficulty", value=3)
        self.assertTrue(self.ask("invasion_difficulty_state")["result"]["chosen"])
        self.assertFalse(self.ask("invasion_pick_difficulty", value=1)["ok"])
        self.ask("invasion_set_difficulty", value=1)
        info = self.ask("invasion_difficulty_state")["result"]
        self.assertEqual((info["yearly"], info["great"], info["vassal"]), (1, 1, 1))

    def test_a_level_outside_0_to_3_is_refused_and_changes_nothing(self):
        before = self.ask("invasion_difficulty_state")["result"]
        for call in (dict(name="invasion_set_difficulty", value=4), dict(name="invasion_set_level", kind="great", value=4),
                     dict(name="invasion_set_level", kind="vassal", value=-1), dict(name="invasion_pick_difficulty", value=4)):
            name = call.pop("name")
            self.assertFalse(self.ask(name, **call)["ok"], name)
        self.assertEqual(self.ask("invasion_difficulty_state")["result"], before)

    def test_a_pick_still_works_once_before_any_set(self):
        answer = self.ask("invasion_pick_difficulty", value=2)
        self.assertTrue(answer["ok"], answer)
        self.assertFalse(self.ask("invasion_pick_difficulty", value=3)["ok"])

    def test_no_pick_banner_after_the_settings_were_applied(self):
        self.ask("scenario_settings_skip")
        self.banners.clear()
        for _ in range(20):
            self.set_day(self.calendar.daysTotal + 1)
        self.assertEqual([text for text in self.banners if text.startswith("Pick the difficulty")], [])

    def test_no_pick_banner_before_any_setting(self):
        self.banners.clear()
        for _ in range(8):
            self.set_day(self.calendar.daysTotal + 1)
        self.assertEqual([text for text in self.banners if text.startswith("Pick the difficulty")], [])

    def test_an_old_save_gets_no_pick_banner(self):
        self.start_game("saveGame_4", 61)
        self.banners.clear()
        for _ in range(20):
            self.set_day(self.calendar.daysTotal + 1)
        self.assertEqual([text for text in self.banners if text.startswith("Pick the difficulty")], [])


if __name__ == "__main__":
    unittest.main()
