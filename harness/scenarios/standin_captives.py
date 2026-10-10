"""Stand-in mod: captives are taken and freed (a toy model)."""

NAME = "standin-captives"
DESCRIPTION = ("Stand-in mod: a toy model that proves the harness method, not the real mod. "
               "Capture captives, free some, and check the counts, the freed total and the ransom value. "
               "Needs the mods InvasionStandIn and HarnessActions.")
LIMIT_S = 60
COVERS = ["R5"]

PREFIX = "InvasionStandIn."
RANSOM_PER_CAPTIVE = 15  # a toy rule of the stand-in
TELEMETRY_WAIT_S = 20


def command(ctx, name, **args):
    return ctx.mod.command(PREFIX + name, **args)


def run(ctx) -> dict:
    expect = ctx.expect
    command(ctx, "reset")
    taken = command(ctx, "capture", count=5)
    expect.equals("R5 five captives are held", taken["held"], 5)
    expect.equals("R5 ransom value follows the count", taken["ransom_value"], 5 * RANSOM_PER_CAPTIVE)
    expect.eventually("R5 metric captives is 5", lambda: ctx.mod.metric(PREFIX + "captives", None) == 5, TELEMETRY_WAIT_S)

    freed = command(ctx, "free_captives", count=2)
    expect.equals("R5 three captives are still held", freed["held"], 3)
    expect.equals("R5 two captives are freed", freed["freed"], 2)
    expect.eventually("R5 metric captives is 3", lambda: ctx.mod.metric(PREFIX + "captives", None) == 3, TELEMETRY_WAIT_S)

    refusal = ctx.mod.refusal(PREFIX + "free_captives", count=10)
    expect.equals("R5 freeing more captives than held is refused", refusal is not None, True)
    expect.equals("R5 a refused free changes nothing", command(ctx, "captives"), freed)

    last = command(ctx, "free_captives", count=3)
    expect.equals("R5 no captive is held at the end", [last["held"], last["freed"], last["ransom_value"]], [0, 5, 0])
    expect.eventually("R5 metric captives is 0", lambda: ctx.mod.metric(PREFIX + "captives", None) == 0, TELEMETRY_WAIT_S)
    return ctx.result()
