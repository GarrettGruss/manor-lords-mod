"""List the components of a Blueprint class JSON: name, class, transform, mesh, tags (spec 18, issue #104).

Usage: s104_components.py <json path under modtools/work/json, or absolute> [--all]
Without --all, components with a clutter_ or dirt_ prefix are only counted. The CDO properties are printed too.
A component template is an export whose object name ends in "_GEN_VARIABLE". SCS nodes give the attach parent.
"""
import json
import sys
from collections import Counter
from pathlib import Path

JSON_ROOT = Path("C:/Users/garre/development/manor-lords-mod/modtools/work/json")
QUIET_PREFIXES = ("clutter_", "dirt_", "Dirt_")


def short(value):
    if isinstance(value, dict):
        if "AssetPath" in value:
            return str(value["AssetPath"]["AssetName"])
        return {k: short(v) for k, v in value.items() if k != "$type"}
    if isinstance(value, list):
        return [short(v) for v in value]
    return value


def compact_value(prop):
    value = prop.get("Value")
    if isinstance(value, list) and value and isinstance(value[0], dict) and "Name" in value[0] and "Value" in value[0]:
        return {p["Name"]: compact_value(p) for p in value}
    return short(value)


def flatten_vector(value):
    if isinstance(value, dict) and len(value) == 1 and isinstance(next(iter(value.values())), dict):
        value = next(iter(value.values()))
    if isinstance(value, dict) and all(isinstance(v, (int, float, str)) for v in value.values()):
        return [round(float(v), 1) for v in value.values()]
    return value


def reference_name(index, asset):
    if index < 0:
        return str(asset["Imports"][-index - 1].get("ObjectName"))
    if index > 0:
        return str(asset["Exports"][index - 1].get("ObjectName"))
    return "none"


def component_row(export, asset):
    fields = {p["Name"]: compact_value(p) for p in export.get("Data", [])}
    row = {"class": reference_name(export.get("ClassIndex", 0), asset)}
    if "StaticMesh" in fields:
        row["mesh"] = reference_name(fields["StaticMesh"], asset) if isinstance(fields["StaticMesh"], int) else fields["StaticMesh"]
    for key, label in (("RelativeLocation", "loc"), ("RelativeRotation", "rot"), ("RelativeScale3D", "scale")):
        if key in fields:
            row[label] = flatten_vector(fields[key])
    for key, value in fields.items():
        if key not in ("StaticMesh", "RelativeLocation", "RelativeRotation", "RelativeScale3D"):
            row[key] = value
    return row


def attach_parents(asset):
    parents = {}
    for export in asset["Exports"]:
        if str(export.get("ObjectName")).startswith("SCS_Node"):
            fields = {p["Name"]: compact_value(p) for p in export.get("Data", [])}
            template = fields.get("ComponentTemplate")
            if isinstance(template, int):
                parents[reference_name(template, asset)] = {k: v for k, v in fields.items() if k in ("ParentComponentOrVariableName", "AttachToName", "InternalVariableName")}
    return parents


def main():
    path = Path(sys.argv[1])
    show_all = "--all" in sys.argv
    if not path.is_absolute():
        path = JSON_ROOT / path
    asset = json.loads(path.read_text(encoding="utf8"))
    parents = attach_parents(asset)
    quiet = Counter()
    for export in asset["Exports"]:
        name = str(export.get("ObjectName"))
        if name.endswith("_GEN_VARIABLE") or name == "StaticMeshComponent0":
            base = name.replace("_GEN_VARIABLE", "")
            if base.startswith(QUIET_PREFIXES) and not show_all:
                quiet[base.split("_")[0]] += 1
                continue
            print("COMP", base, json.dumps(component_row(export, asset)), json.dumps(parents.get(name, {})))
        elif name.startswith("Default__"):
            print("CDO", name, json.dumps({p["Name"]: compact_value(p) for p in export.get("Data", [])})[:1500])
    for prefix, count in quiet.items():
        print("COUNT", prefix + "_*", count)


main()
