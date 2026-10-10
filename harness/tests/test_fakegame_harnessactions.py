"""Mock test for the HarnessActions mod (spec 07): command file in, game call on the game thread, result file out."""

import json
import re
import unittest
from pathlib import Path

import fakegame_path  # noqa: F401
from fakegame import FakeGame

MAIN_LUA = Path(__file__).resolve().parents[2] / "mod" / "HarnessActions" / "Scripts" / "main.lua"
LETTER = ["welcome_from_hildebolt"]


def build_world(game, lords=2, send_error=None):
    """An engine with a player and some AI lords. The InBox of the player grows when a lord sends a letter."""
    game.exec("FName = function(text) return { fname = text } end")
    sent = []
    inbox = game.array([0] * 20, visible=lambda: len(sent))
    player = game.obj("MyPawnCPP_BP3_C", InBox=inbox)
    game.obj("RTSMultiEngineCPP", playerRef=player)

    def send_letter(lord, recipient, paragraphs):
        if send_error:
            raise RuntimeError(send_error)
        sent.append((recipient, [paragraphs[i].fname for i in range(1, len(paragraphs) + 1)]))

    for _ in range(lords):
        lord = game.obj("PawnCPP_AI")
        game.method(lord, "sendLetter", send_letter)
    return player, sent


def commands_dir(game):
    folder = game.run_dir / "commands"
    folder.mkdir(exist_ok=True)
    return folder


def send(game, number, body):
    request = {"id": f"{number:04d}", **body}
    (commands_dir(game) / f"{number:04d}.json").write_text(json.dumps(request), encoding="utf-8")
    game.advance(1)


def result(game, number):
    return json.loads((commands_dir(game) / f"{number:04d}.result.json").read_text(encoding="utf-8"))


def start(game, **world_options):
    world = build_world(game, **world_options)
    game.load_mod("HarnessActions")
    game.advance(1)
    return world


ACCEPT = "BndEvt__popupMessageWidget_Button_Accept_K2Node_ComponentBoundEvent_0_OnButtonReleasedEvent__DelegateSignature"


def add_popup(game, kind, closing=False):
    """A pop-up widget like the real one: `messageType` and `closing`, and the Accept handler sets `closing`."""
    widget = game.obj("popupMessageWidget_C", messageType=game.text(kind), closing=closing)
    pressed = []
    game.method(widget, ACCEPT, lambda w: (pressed.append(kind), game.exec("return nil"), None)[0])
    return widget, pressed


class HarnessActionsTests(unittest.TestCase):
    def test_popup_state_lists_the_open_popups_and_changes_nothing(self):
        with FakeGame() as game:
            start(game)
            _, pressed = add_popup(game, "hunger")
            add_popup(game, "old", closing=True)
            send(game, 1, {"command": "popup_state"})
            answer = result(game, 1)
            self.assertEqual((answer["ok"], answer["widgets"], answer["open"]), (True, 2, ["hunger"]))
            self.assertEqual(pressed, [])

    def test_close_popups_presses_accept_only_on_open_popups(self):
        with FakeGame() as game:
            start(game)
            _, pressed_hunger = add_popup(game, "hunger")
            _, pressed_old = add_popup(game, "old", closing=True)
            send(game, 1, {"command": "close_popups"})
            answer = result(game, 1)
            self.assertEqual((answer["ok"], answer["count"], answer["closed"]), (True, 1, ["hunger"]))
            self.assertEqual((pressed_hunger, pressed_old), (["hunger"], []))

    def test_close_popups_without_a_widget_is_a_clean_zero(self):
        with FakeGame() as game:
            start(game)
            send(game, 1, {"command": "close_popups"})
            answer = result(game, 1)
            self.assertEqual((answer["ok"], answer["count"], answer["widgets"]), (True, 0, 0))

    def test_ping_answers_with_the_version(self):
        with FakeGame() as game:
            start(game)
            send(game, 1, {"command": "ping"})
            answer = result(game, 1)
            self.assertEqual((answer["ok"], answer["command"], answer["id"]), (True, "ping", "0001"))
            self.assertRegex(answer["version"], r"^\d+")

    def test_send_letter_calls_the_lord_with_the_player_and_the_paragraphs(self):
        with FakeGame() as game:
            player, sent = start(game)
            send(game, 1, {"command": "send_letter", "sender": 2, "paragraphs": LETTER})
            answer = result(game, 1)
            self.assertEqual((answer["ok"], answer["inbox_before"], answer["inbox_after"]), (True, 0, 1))
            self.assertEqual(sent[0][1], LETTER)
            self.assertEqual(sent[0][0].GetFullName(sent[0][0]), player.GetFullName(player))

    def test_commands_run_in_order_and_each_gets_its_own_result(self):
        with FakeGame() as game:
            _, sent = start(game)
            send(game, 1, {"command": "send_letter", "sender": 1, "paragraphs": LETTER})
            send(game, 2, {"command": "send_letter", "sender": 1, "paragraphs": ["a_b"]})
            self.assertEqual((result(game, 1)["inbox_after"], result(game, 2)["inbox_after"]), (1, 2))
            self.assertEqual(len(sent), 2)

    def test_a_result_file_is_never_half_written(self):
        with FakeGame() as game:
            start(game)
            send(game, 1, {"command": "ping"})
            self.assertEqual([n for n in (commands_dir(game)).iterdir() if n.suffix == ".tmp"], [])

    def test_unknown_command_is_refused(self):
        with FakeGame() as game:
            _, sent = start(game)
            send(game, 1, {"command": "run_lua"})
            answer = result(game, 1)
            self.assertFalse(answer["ok"])
            self.assertIn("unknown command", answer["error"])
            self.assertEqual(sent, [])

    def test_a_request_with_the_wrong_number_is_refused(self):
        with FakeGame() as game:
            _, sent = start(game)
            (commands_dir(game) / "0001.json").write_text('{"id":"0009","command":"ping"}', encoding="utf-8")
            game.advance(1)
            self.assertIn("request id must be 0001", result(game, 1)["error"])

    def test_bad_input_is_refused_before_any_game_call(self):
        cases = {
            "no such lord": ({"sender": 9, "paragraphs": LETTER}, "no AI lord with sender number 9"),
            "no sender": ({"paragraphs": LETTER}, "no AI lord"),
            "space in name": ({"sender": 1, "paragraphs": ["a b"]}, "letters, digits and underscore"),
            "quote in name": ({"sender": 1, "paragraphs": ["a\\\"b"]}, "letters, digits and underscore"),
            "long name": ({"sender": 1, "paragraphs": ["a" * 65]}, "1 to 64"),
            "too many": ({"sender": 1, "paragraphs": ["a"] * 11}, "too many paragraphs"),
            "none": ({"sender": 1, "paragraphs": []}, "no paragraphs"),
            "missing": ({"sender": 1}, "no paragraphs"),
        }
        for label, (body, message) in cases.items():
            with self.subTest(case=label), FakeGame() as game:
                _, sent = start(game)
                send(game, 1, {"command": "send_letter", **body})
                answer = result(game, 1)
                self.assertFalse(answer["ok"])
                self.assertIn(message, answer["error"])
                self.assertEqual(sent, [])

    def test_a_game_error_becomes_an_error_result(self):
        with FakeGame() as game:
            start(game, send_error="the game said no")
            send(game, 1, {"command": "send_letter", "sender": 1, "paragraphs": LETTER})
            answer = result(game, 1)
            self.assertFalse(answer["ok"])
            self.assertIn("the game said no", answer["error"])
            send(game, 2, {"command": "ping"})  # the mod goes on after an error
            self.assertTrue(result(game, 2)["ok"])

    def test_no_player_gives_a_clear_error(self):
        with FakeGame() as game:
            game.exec("FName = function(text) return { fname = text } end")
            lord = game.obj("PawnCPP_AI")
            game.method(lord, "sendLetter", lambda *args: None)
            game.load_mod("HarnessActions")
            game.advance(1)
            send(game, 1, {"command": "send_letter", "sender": 1, "paragraphs": LETTER})
            self.assertIn("player pawn is not loaded", result(game, 1)["error"])

    def test_after_a_restart_the_mod_waits_for_the_next_number(self):
        with FakeGame() as game:
            _, sent = start(game)
            send(game, 1, {"command": "send_letter", "sender": 1, "paragraphs": LETTER})
            game.load_mod("HarnessActions")  # a hot reload runs the file again
            game.advance(2)
            self.assertEqual(len(sent), 1)  # request 0001 was not run a second time
            send(game, 2, {"command": "ping"})
            self.assertTrue(result(game, 2)["ok"])

    def test_the_log_names_the_mod_and_the_version(self):
        with FakeGame() as game:
            start(game)
            pattern = re.compile(r"\[HarnessActions\] loaded version [\w.-]+")
            self.assertTrue(any(pattern.search(line) for line in game.log_lines()), game.log_lines())


class NoEvalTests(unittest.TestCase):
    def test_the_mod_never_runs_text_as_code(self):
        source = MAIN_LUA.read_text(encoding="utf-8")
        code = "\n".join(line.split("--", 1)[0] for line in source.splitlines())
        for forbidden in (r"\bload\s*\(", r"\bloadstring\s*\(", r"\bdofile\s*\(", r"\bloadfile\s*\(", r"\bos\.execute", r"\bio\.popen"):
            self.assertIsNone(re.search(forbidden, code), forbidden)


if __name__ == "__main__":
    unittest.main()
