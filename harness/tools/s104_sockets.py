"""List the static mesh sockets of an asset JSON: socket name, location, rotation, scale (spec 18, issue #104).

Usage: s104_sockets.py <json path under modtools/work/json, or absolute>
"""
import json
import sys
from collections import Counter
from pathlib import Path

JSON_ROOT = Path("C:/Users/garre/development/manor-lords-mod/modtools/work/json")


def vector(value):
    if isinstance(value, list):
        value = {p["Name"]: p["Value"] for p in value}
    if isinstance(value, dict):
        inner = next(iter(value.values())) if len(value) == 1 else value
        if isinstance(inner, dict):
            value = inner
    return [round(float(v), 1) for k, v in value.items() if k != "$type"] if isinstance(value, dict) else value


def field(prop_list, name):
    for prop in prop_list:
        if prop.get("Name") == name:
            return prop.get("Value")
    return None


def main():
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = JSON_ROOT / path
    asset = json.loads(path.read_text(encoding="utf8"))
    sockets = []
    for export in asset["Exports"]:
        if str(export.get("ObjectName")).startswith("StaticMeshSocket"):
            data = export.get("Data", [])
            sockets.append((str(field(data, "SocketName")), vector(field(data, "RelativeLocation")), vector(field(data, "RelativeRotation")), vector(field(data, "RelativeScale"))))
    prefixes = Counter(name.rstrip("0123456789_") for name, *_ in sockets)
    print("sockets", len(sockets), dict(prefixes))
    for row in sockets:
        print(*row)


main()
