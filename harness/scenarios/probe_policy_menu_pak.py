"""Spike for issue #60 (spec 16, option c): show the custom policy menu from the pak widget and take a screenshot.

Run with the pak: `uv run python harness\\run.py --scenario probe-policy-menu-pak --fixture base --pak policymenu`.
The scenario records every answer. It fails only if the widget is not in the viewport.
"""

NAME = "probe-policy-menu-pak"
LIMIT_S = 240
HIDDEN = True
LONG_REASON = "Spike: it needs the pak policymenu."


def run(ctx) -> dict:
    actions = ctx.actions
    answer = actions._command("menu_pak_show", x=300, y=200)  # noqa: SLF001
    ctx.log.info(f"PROBE menu_pak_show {answer}")
    ctx.screenshot("policy-menu")
    state = actions._command("menu_pak_read")  # noqa: SLF001
    ctx.log.info(f"PROBE menu_pak_read {state}")
    ctx.expect.equals("the pak menu is in the viewport", state.get("in_viewport"), True)
    actions._command("menu_pak_hide")  # noqa: SLF001
    return ctx.result()
