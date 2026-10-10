"""Add and take silver with actions. Check the player value, the HUD number and the telemetry."""

NAME = "silver-change"
DESCRIPTION = "Set silver to 500, add 250, take 100. The player value, the HUD number and the telemetry must show 650."
LIMIT_S = 90
START = 500
ADDED = 250
TAKEN = 100
EXPECTED = START + ADDED - TAKEN
# The HUD writes 1000 and more as "1.2k". Below 1000 it shows the exact number, so the test stays below it.
assert EXPECTED < 1000
HUD_WAIT_S = 10
TELEMETRY_WAIT_S = 15  # the mod writes one sample every 5 s


def _digits(text) -> str:
    """Only the digits count."""
    return "".join(char for char in str(text) if char.isdigit())


def _hud_text(ctx) -> str:
    text = ctx.bridge.hud_treasury_text()
    ctx.log.info(f"HUD treasury text: {text!r}")
    return text


def _latest_silver(ctx):
    samples = ctx.telemetry.read()
    return samples[-1]["player"]["silver"] if samples else None


def run(ctx) -> dict:
    expect = ctx.expect
    actions = ctx.actions
    actions.set_silver(START)
    actions.add_silver(ADDED)
    actions.add_silver(-TAKEN)

    silver = ctx.bridge.read_property(ctx.bridge.player_path(), "silver")
    expect.equals("player silver after the actions", silver, EXPECTED)
    expect.eventually("telemetry shows the silver", lambda: _latest_silver(ctx) == EXPECTED, TELEMETRY_WAIT_S)

    # The value must also hold while game time runs. The HUD updates only while the game runs, so it is read after this.
    ctx.time.run_game_seconds(5, speed=1)
    held = ctx.bridge.read_property(ctx.bridge.player_path(), "silver")
    expect.in_range("player silver after 5 game seconds", held, EXPECTED, EXPECTED + 50)
    expect.eventually("HUD shows the silver", lambda: _digits(_hud_text(ctx)) == str(held), HUD_WAIT_S)
    return ctx.result()
