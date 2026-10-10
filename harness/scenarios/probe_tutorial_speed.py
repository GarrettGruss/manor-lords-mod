"""Probe for spec 02/04: does a tutorial make the game fall back to 1x after changeGameSpeed?

Hypothesis: the game has a tutorial named tutorial_gameSpeed (settings useTutorials / showTutorials, state
tutorialsLeftToShow, pausedBeforeTutorial). The first speed change may start it and lower the speed once.

Steps: find the tutorial properties on the game instance, the player and the engine, write them to probe.json,
then change the speed to 3 and sample speed and clock for 10 s into probe.jsonl.
With HARNESS_PROBE_CLEAR_TUTORIALS=1 the scenario first empties engine.tutorialsLeftToShow.
With HARNESS_PROBE_DISABLE_TUTORIALS=1 the scenario first sets every writable boolean property whose name matches
useTutorials or showTutorials to false, and writes what it changed. Not a test: it never fails on a game answer.
"""

import json
import os
import time

from runlib.bridge_client import object_path

NAME = "probe-tutorial-speed"
LIMIT_S = 120
HIDDEN = True
START_AFTER_S = 8.0  # the earlier probes saw the fallback when the change came 27 to 28 s after the load
OBSERVE_S = 10.0
SAMPLE_S = 0.25
PATTERN = "utorial"


def _owners(bridge) -> dict:
    instance = bridge._result("objects", class_name="MLGameInstance", limit=1)["objects"][0]
    return {"gameInstance": object_path(instance), "player": bridge.player_path(), "engine": bridge.engine_path()}


def _tutorial_properties(bridge, owners: dict) -> dict:
    found = {}
    for label, ref in owners.items():
        try:
            result = bridge._result("props", ref=ref, include_super=True, pattern=PATTERN)
            found[label] = result.get("properties", result)
        except Exception as error:  # noqa: BLE001 - a probe records what it sees
            found[label] = f"ERROR {str(error)[:120]}"
    return found


def _disable_tutorials(bridge, owners: dict, properties: dict) -> list:
    changed = []
    for label, props in properties.items():
        if not isinstance(props, (dict, list)):
            continue
        names = props.keys() if isinstance(props, dict) else [p.get("name") for p in props if isinstance(p, dict)]
        for name in names:
            if name in ("useTutorials", "showTutorials"):
                try:
                    changed.append({"owner": label, "name": name, "result": bridge.write_property(owners[label], name, False)})
                except Exception as error:  # noqa: BLE001
                    changed.append({"owner": label, "name": name, "error": str(error)[:120]})
    return changed


def _count(bridge, name: str):
    """The length of a list property of the player, or None if it cannot be read."""
    if os.environ.get("HARNESS_PROBE_NO_READS") == "1":
        return None  # control runs: sample only the speed and the clock, as the first probe did
    try:
        value = bridge.read_property(bridge.player_path(), name)
        return len(value) if isinstance(value, list) else None
    except Exception:  # noqa: BLE001 - a probe records what it can read
        return None


def run(ctx) -> dict:
    bridge = ctx.bridge
    owners = _owners(bridge)
    properties = _tutorial_properties(bridge, owners)
    record = {"owners": owners, "properties": properties}
    if os.environ.get("HARNESS_PROBE_DISABLE_TUTORIALS") == "1":
        record["disabled"] = _disable_tutorials(bridge, owners, properties)
        record["after_disable"] = _tutorial_properties(bridge, owners)
    if os.environ.get("HARNESS_PROBE_CLEAR_TUTORIALS") == "1":
        # Empty the queue of tutorials the engine still wants to show, in memory only (the run's private game).
        try:
            record["cleared"] = bridge.write_property(owners["engine"], "tutorialsLeftToShow", [])
        except Exception as error:  # noqa: BLE001
            record["cleared"] = f"ERROR {str(error)[:200]}"
        record["after_clear"] = _tutorial_properties(bridge, owners)["engine"]
    (ctx.run_dir / "probe.json").write_text(json.dumps(record, indent=1, default=str)[:20000], encoding="utf-8")

    time.sleep(START_AFTER_S)
    with (ctx.run_dir / "probe.jsonl").open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"unpause": bridge.unpause(5.0)}) + "\n")
        bridge.call_on_player("changeGameSpeed", [3, False])
        started = time.monotonic()
        while time.monotonic() - started < OBSERVE_S:
            handle.write(json.dumps({"t": round(time.monotonic() - started, 2), "gameSpeed": bridge.read_game_speed(),
                                     "clock": bridge.read_clock_value(), "inbox": _count(bridge, "InBox"),
                                     "messages": _count(bridge, "TutorialMessages")}) + "\n")
            handle.flush()
            time.sleep(SAMPLE_S)
    ctx.time.pause()
    return ctx.result()
