"""Place a building with the real OS mouse (action place_building). It moves the real cursor and takes the keyboard focus.

Do not run it while a person works on this computer. The HitchingPost costs nothing. Check: one more building of that type,
and the cursor is back where it was.
"""

from runlib.osinput import Win32Input

NAME = "place-building"
DESCRIPTION = "Place a HitchingPost with a real mouse click (uses the OS mouse and focus). The player region must get one more."
LIMIT_S = 120
EXCLUSIVE = True  # real mouse input: a parallel suite runs it with no other game
# Hidden on purpose: it takes over the real mouse and the keyboard focus. It is not offered to agents by the MCP tools
# and not in any suite. Run it by hand on a computer that nobody is using: run.py --scenario place-building
HIDDEN = True
HITCHING_POST = 30
CURSOR_TOLERANCE_PX = 2


def run(ctx) -> dict:
    mouse = Win32Input()
    cursor_before = mouse.get_cursor()
    record = ctx.actions.place_building(HITCHING_POST)
    ctx.expect.equals("hitching posts after the click", record["after"], record["before"] + 1)
    x, y = mouse.get_cursor()
    moved = max(abs(x - cursor_before[0]), abs(y - cursor_before[1]))
    ctx.expect.in_range("cursor distance from its start position (px)", moved, 0, CURSOR_TOLERANCE_PX)
    return ctx.result()
