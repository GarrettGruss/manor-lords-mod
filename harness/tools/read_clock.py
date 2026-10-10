# Reads the game clock twice through ue4ss-bridge and prints one JSON line.
# The game counts as paused when the clock did not change.
# Run from the repo root with the project venv, with PYTHONPATH=mcp and UE4SS_BRIDGE_GAME_DIR set:
#   .venv\Scripts\python.exe harness\tools\read_clock.py [seconds]
import json
import sys
import time

from ue4ss_bridge import server as bridge


def read_clock(wait_seconds=6.0):
    """Return the clock report as a dict. A failed read is a result (ok false), not an exception."""
    try:
        engine = bridge.one("objects", class_name="RTSMultiEngineCPP", limit=1)["result"]["objects"][0]
        engine = engine.split(" ", 1)[1]

        def clock():
            return bridge.one("call", ref=engine, **{"function": "getGameTimeAdjusted"}, args=[])["result"]

        first = clock()
        time.sleep(wait_seconds)
        second = clock()
        speed = bridge.one("get", ref=engine, name="gameSpeed")["result"]
        result = {"ok": True, "clock": second, "change": round(second - first, 3),
                  "seconds": wait_seconds, "gameSpeed": speed, "paused": abs(second - first) < 0.001}
    except Exception as error:  # a failed read is a result, not a crash
        result = {"ok": False, "error": str(error).splitlines()[0][-200:] if str(error) else repr(error)}
    return result


def main():
    wait_seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    print(json.dumps(read_clock(wait_seconds)))


if __name__ == "__main__":
    main()
