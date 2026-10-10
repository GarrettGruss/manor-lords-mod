"""Helpers for the tests of the mod-state contract (spec 10, U10): HarnessCommands, the stand-in mod and ModState.

They run the real Lua files in the fake game kit. They do not prove that the real game behaves the same.
"""

import json

import fakegame_path  # noqa: F401
import runlib_path  # noqa: F401

MIN_STEP_S = 0.5  # the kit moves time in steps of 0.5 s, so a smaller sleep would move nothing


def build_engine(game, days_total=100):
    """An engine with a calendar. The stand-in mod reads TemporalComponent.daysTotal."""
    calendar = game.obj("TemporalComponent", daysTotal=days_total, day=61, month=3, Year=1, Season=1)
    engine = game.obj("RTSMultiEngineCPP", TemporalComponent=calendar, playerRef=game.obj("PawnCPP"),
                      regions=game.array([]))
    game.method(engine, "getGameTimeAdjusted", lambda _self: game.now())
    return engine


def set_days(game, days_total):
    game.exec(f"FindFirstOf('RTSMultiEngineCPP').TemporalComponent.daysTotal = {days_total}")


def mod_channel(game, timeout_s=10):
    """The real client of the mod command channel (runlib.commands.ModCommandChannel) on the folder of the fake game."""
    from runlib.commands import ModCommandChannel
    sleep = sleep_in(game)
    return ModCommandChannel(game.run_dir / "modcmd", timeout_s=timeout_s, sleep=sleep, monotonic=game.now)


def dispatch(game, name, args=None, mod=None):
    """Run a command and return {"ok", "result" | "error"}. The arguments pass through JSON, as in a real request.

    A game with separate Lua states can only be reached through the request files of the mod, as in the real game.
    A game with one Lua state calls HarnessCommands.dispatch directly (the registry tests use this).
    `mod` is the folder to ask. It defaults to the text before the dot in `name`.
    """
    if game.separate_states:
        return _dispatch_by_file(game, name, args or {}, mod or name.split(".", 1)[0])
    game.lua.globals().TEST_NAME = name
    game.lua.globals().TEST_ARGS = json.dumps(args if args is not None else {})
    text = game.exec("""
        local json = require("HarnessJson")
        local args = json.decode(TEST_ARGS)
        return json.encode(require("HarnessCommands").dispatch(TEST_NAME, args))
    """)
    return json.loads(text)


def _dispatch_by_file(game, name, args, mod):
    from runlib.commands import CommandRefused
    try:
        return {"ok": True, **mod_channel(game).send(mod, name, args)}
    except CommandRefused as refused:
        return {"ok": False, "error": refused.reason}


def call(game, name, mod=None, **args):
    """Dispatch and return the result. Fail the test with the error text when the command was refused."""
    answer = dispatch(game, name, args, mod)
    if not answer["ok"]:
        raise AssertionError(f"{name} {args} was refused: {answer['error']}")
    return answer["result"]


def sleep_in(game):
    """A sleep function for CommandChannel: it moves the fake game time, so the mod can answer."""
    return lambda seconds: game.advance(max(seconds, MIN_STEP_S))
