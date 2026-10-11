"""Show a raid countdown banner, update it each game day, and read the text back from the widget (spec 10, spike S9, criterion T4)."""

from runlib.actions import ActionError

NAME = "ui-countdown"
DESCRIPTION = ("Write daysUntilNextRaid=4. Show 'Raid in N days' with N from the timer, read the widget text back, take a screenshot, "
               "run one game day, and show the new N. T4 is partly human: this proves the text and the picture, not the looks (Q4).")
COVERS = ["T4"]
LIMIT_S = 150
START_DAYS = 4
STEPS = 3          # N = 4, 3, 2. The raid comes on the day the timer reaches 0, so the test stops before that.
SPEED = 3


def banner_text(days: int) -> str:
    return f"Raid in {days} days"


def show_and_check(ctx, days: int) -> None:
    expect = ctx.expect
    record = ctx.actions.show_message(banner_text(days), "Prepare your defence")
    answer = record["answer"]
    expect.equals(f"a new banner widget appeared for {days} days", answer["shown"], True)
    stored = ctx.actions.read_message()
    expect.equals(f"widget Text after reading back ({days})", stored.get("text"), banner_text(days))
    expect.equals(f"text block of the banner ({days})", stored.get("main_text"), banner_text(days))
    expect.equals(f"second line of the banner ({days})", stored.get("bottom_text"), "Prepare your defence")
    ctx.screenshot(f"countdown-{days}")


def check_bad_text_is_refused(ctx) -> None:
    try:
        ctx.actions.show_message("Raid in <3> days")
        ctx.expect.record("text with markup characters is refused", False, "accepted", "refused")
    except ActionError as error:
        ctx.expect.record("text with markup characters is refused", True, str(error)[:70], "ActionError")


def run(ctx) -> dict:
    expect, bridge = ctx.expect, ctx.bridge
    calendar = bridge.calendar_path()
    ctx.actions.set_raid_timer(START_DAYS, days_since=5)
    check_bad_text_is_refused(ctx)

    shown = []
    for step in range(STEPS):
        days = bridge.read_property(calendar, "daysUntilNextRaid")
        shown.append(days)
        show_and_check(ctx, days)
        if step < STEPS - 1:
            ctx.time.run_game_days(1, speed=SPEED)

    expect.equals("the countdown fell by one each game day", shown, [START_DAYS - step for step in range(STEPS)])
    expect.at_least("banners listed after the updates", ctx.actions.list_messages()["count"], 1)
    ctx.metric("countdown_steps", len(shown))
    return ctx.result()
