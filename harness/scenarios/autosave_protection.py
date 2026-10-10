"""Check that the game's autosave timer was pushed away at boot and stays away while the game runs 60 game seconds."""

NAME = "autosave-protection"
DESCRIPTION = "HarnessBoot disables the autosave timer. The timer must stay far away after 60 running game seconds."
LIMIT_S = 120
RUN_GAME_SECONDS = 60
# The game default is 600 s. A timer that is disabled has about a year left.
MIN_REMAINING_S = 1_000_000


def run(ctx) -> dict:
    expect = ctx.expect
    before = ctx.actions.autosave_status()
    expect.equals("autosave timer exists", before.get("timer_exists"), True)
    expect.at_least("autosave timer is far away at READY (s)", before.get("remaining_s", 0), MIN_REMAINING_S)

    ctx.time.run_game_seconds(RUN_GAME_SECONDS, speed=1)

    after = ctx.actions.autosave_status()
    expect.equals("same timer after the run", after.get("handle_id"), before.get("handle_id"))
    expect.at_least("autosave timer is still far away (s)", after.get("remaining_s", 0), MIN_REMAINING_S)
    expect.changed("timer counted down while the game ran (s)", before["remaining_s"], after["remaining_s"], -RUN_GAME_SECONDS * 2, -RUN_GAME_SECONDS / 2)
    return ctx.result()
