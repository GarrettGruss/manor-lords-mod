"""Spike #65 helper: edit the unpacked JSON of buildingStats and castlePlanner for the manor module pak.

Why a script: the edit is a clone of a row and a widget change, and must be repeatable.
The input and output JSON files are under the git-ignored pakmod work folder. Run it from the repo root:
  uv run python harness/tools/s65_edit_json.py stats <json> <source row> <new row>
  uv run python harness/tools/s65_edit_json.py planner <json> <widget name> <new id>
  uv run python harness/tools/s65_edit_json.py blueprint <json> <row> <package path> <class name>
  uv run python harness/tools/s65_edit_json.py visible <json> <row>
"""
import copy
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def clone_stats_row(path, source, new):
    data = load(path)
    rows = data["Exports"][0]["Table"]["Data"]
    names = [row["Name"] for row in rows]
    if new in names:
        raise SystemExit(f"error: row {new} already exists")
    if source not in names:
        raise SystemExit(f"error: source row {source} not found")
    clone = copy.deepcopy(rows[names.index(source)])
    clone["Name"] = new
    rows.append(clone)
    # UAssetGUI 1.1.0 wrote no file when the new row name was missing in the name map.
    if new not in data["NameMap"]:
        data["NameMap"].append(new)
    save(path, data)
    print(f"ok: row {new} cloned from row {source}; {len(rows)} rows")


def retarget_widget(path, widget_name, new_id):
    data = load(path)
    hits = [e for e in data["Exports"] if e.get("ObjectName") == widget_name]
    if len(hits) != 1:
        raise SystemExit(f"error: expected one export named {widget_name}, found {len(hits)}")
    export = hits[0]
    for prop in export["Data"]:
        if prop["Name"] == "ID":
            prop["Value"] = int(new_id)
    export["Data"] = [p for p in export["Data"] if p["Name"] != "Visibility"]
    save(path, data)
    print(f"ok: {widget_name} now has ID {new_id} and default visibility")


def retarget_blueprint(path, row_name, package, asset):
    data = load(path)
    rows = data["Exports"][0]["Table"]["Data"]
    hits = [r for r in rows if r["Name"] == row_name]
    if len(hits) != 1:
        raise SystemExit(f"error: expected one row {row_name}, found {len(hits)}")
    props = [p for p in hits[0]["Value"] if p["Name"] == "BlueprintPath"]
    soft_path = props[0]["Value"][0]["Value"]["AssetPath"]
    soft_path["PackageName"] = package
    soft_path["AssetName"] = asset
    for name in (package, asset):
        if name not in data["NameMap"]:
            data["NameMap"].append(name)
    save(path, data)
    print(f"ok: row {row_name} BlueprintPath is now {package}.{asset}")


def make_row_visible(path, row_name):
    data = load(path)
    rows = data["Exports"][0]["Table"]["Data"]
    hits = [r for r in rows if r["Name"] == row_name]
    if len(hits) != 1:
        raise SystemExit(f"error: expected one row {row_name}, found {len(hits)}")
    flags = [p for p in hits[0]["Value"] if p["Name"] == "bVisibleInUi"]
    if len(flags) != 1:
        raise SystemExit(f"error: row {row_name} has no bVisibleInUi field")
    # IsZero tells the writer that the value is the default. Clear it, or the true value is not written.
    flags[0]["IsZero"] = False
    flags[0]["Value"] = True
    save(path, data)
    print(f"ok: row {row_name} has bVisibleInUi true")


def main(argv):
    if len(argv) == 5 and argv[1] == "stats":
        clone_stats_row(argv[2], argv[3], argv[4])
    elif len(argv) == 5 and argv[1] == "planner":
        retarget_widget(argv[2], argv[3], argv[4])
    elif len(argv) == 6 and argv[1] == "blueprint":
        retarget_blueprint(argv[2], argv[3], argv[4], argv[5])
    elif len(argv) == 4 and argv[1] == "visible":
        make_row_visible(argv[2], argv[3])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
