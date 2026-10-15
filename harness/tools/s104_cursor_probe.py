"""Probe: what the player controller reports for the cursor. Issue 104 research tool."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "harness" / "tools"))
import s94_drive  # noqa: E402

bridge = s94_drive.make_bridge(sys.argv[1])
for name in ("first:PlayerController", "first:MLPlayerController"):
    for function in ("GetMousePosition", "IsInputKeyDown", "ShouldShowMouseCursor"):
        try:
            print(name, function, bridge.call_function(name, function, []))
        except Exception as error:
            print(name, function, "error", str(error)[:150])
player = bridge.player_path()
for prop in ("bShowMouseCursor", "mouseOverUI", "bIsMouseOverUI", "inputMode"):
    try:
        print("player", prop, bridge.read_property(player, prop))
    except Exception as error:
        print("player", prop, "error", str(error)[:100])
