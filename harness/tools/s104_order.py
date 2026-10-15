"""Order an upgrade (for example 13 = order oxen) on a master through PawnCPP:addUpgradeRequest. Issue 104 research tool.

    uv run python harness/tools/s104_order.py <run id> <master path> <upgrade id> [slot]

The request struct is passed as a JSON object. No save function is called.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "harness" / "tools"))
import s94_drive  # noqa: E402

bridge = s94_drive.make_bridge(sys.argv[1])
master = sys.argv[2]
request = {"buildingMaster": master, "upgradeID": int(sys.argv[3]), "Slot": int(sys.argv[4]) if len(sys.argv) > 4 else 0}
print(bridge.call_function(bridge.player_path(), "addUpgradeRequest", [request]))
