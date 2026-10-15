"""Spike #65 helper: edit the unpacked JSON of buildingStats and castlePlanner for the manor module pak.

Why a script: the edit is a clone of a row and a widget change, and must be repeatable.
The input and output JSON files are under the git-ignored pakmod work folder. Run it from the repo root:
  uv run python harness/tools/s65_edit_json.py stats <json> <source row> <new row>
  uv run python harness/tools/s65_edit_json.py planner <json> <widget name> <new id>
  uv run python harness/tools/s65_edit_json.py blueprint <json> <row> <package path> <class name>
  uv run python harness/tools/s65_edit_json.py meshpath <json> <row> <package> <asset>   (issue 90 round 6)
  uv run python harness/tools/s65_edit_json.py visible <json> <row>
  uv run python harness/tools/s65_edit_json.py enum <json> <row> <enum field> <value>   (issue 94: buildingFunction Siege -> Default)
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


def set_enum_field(path, row_name, field, value):
    data = load(path)
    rows = data["Exports"][0]["Table"]["Data"]
    hits = [r for r in rows if r["Name"] == row_name]
    if len(hits) != 1:
        raise SystemExit(f"error: expected one row {row_name}, found {len(hits)}")
    fields = [p for p in hits[0]["Value"] if p["Name"] == field and "EnumType" in p]
    if len(fields) != 1:
        raise SystemExit(f"error: row {row_name} has no enum field {field}")
    before = fields[0]["Value"]
    fields[0]["IsZero"] = False
    fields[0]["Value"] = value
    if value not in data["NameMap"]:
        data["NameMap"].append(value)
    save(path, data)
    print(f"ok: row {row_name} {field}: {before} -> {value}")


def set_number_field(path, row_name, field, text):
    """Issue 104: set a Byte, Int or Float field, or a Vector2D field written as X,Y. Clears IsZero."""
    data = load(path)
    row = find_row(data["Exports"][0]["Table"]["Data"], row_name)
    hits = [p for p in row["Value"] if p["Name"] == field]
    if len(hits) != 1:
        raise SystemExit(f"error: row {row_name} needs exactly one field {field}, found {len(hits)}")
    prop = hits[0]
    prop["IsZero"] = False
    if "Vector2D" in prop.get("StructType", ""):
        x, y = (float(part) for part in text.split(","))
        inner = prop["Value"][0]
        inner["IsZero"] = False
        inner["Value"]["X"], inner["Value"]["Y"] = x, y
    elif isinstance(prop["Value"], int) and not isinstance(prop["Value"], bool):
        prop["Value"] = int(float(text))
    elif isinstance(prop["Value"], float):
        prop["Value"] = float(text)
    else:
        raise SystemExit(f"error: field {field} is not a number or Vector2D")
    save(path, data)
    print(f"ok: row {row_name} {field} = {text}")


def find_row(rows, name):
    hits = [r for r in rows if r["Name"] == name]
    if len(hits) != 1:
        raise SystemExit(f"error: expected one row {name}, found {len(hits)}")
    return hits[0]


def copy_field(path, source, target, field, factor):
    """Issue 90: give the Lv3 row the cost list and tech list of a working Lv1 row. Amounts are scaled by factor."""
    data = load(path)
    rows = data["Exports"][0]["Table"]["Data"]
    src_props = [p for p in find_row(rows, source)["Value"] if p["Name"] == field]
    if len(src_props) != 1:
        raise SystemExit(f"error: row {source} has no field {field}")
    new_prop = copy.deepcopy(src_props[0])
    for node in walk(new_prop):
        if isinstance(node, dict) and node.get("Name") == "amt":
            node["Value"] = max(1, round(node["Value"] * factor))
    target_props = find_row(rows, target)["Value"]
    index = [p["Name"] for p in target_props].index(field)
    target_props[index] = new_prop
    save(path, data)
    print(f"ok: row {target} field {field} copied from row {source}, amounts x{factor}")


def walk(node):
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def clone_mesh_row(path, source, new, package, asset):
    """Issue 90: add a DT_BuildingMeshPathData row for a module row, with its own mesh path."""
    data = load(path)
    rows = data["Exports"][0]["Table"]["Data"]
    if new in [r["Name"] for r in rows]:
        raise SystemExit(f"error: row {new} already exists")
    clone = copy.deepcopy(find_row(rows, source))
    clone["Name"] = new
    paths = [n["AssetPath"] for n in walk(clone) if isinstance(n, dict) and "AssetPath" in n]
    if len(paths) != 1:
        raise SystemExit(f"error: expected one soft path in row {source}, found {len(paths)}")
    paths[0]["PackageName"] = package
    paths[0]["AssetName"] = asset
    rows.append(clone)
    for name in (new, package, asset):
        if name not in data["NameMap"]:
            data["NameMap"].append(name)
    save(path, data)
    print(f"ok: row {new} cloned from {source} with mesh {package}.{asset}")


def set_mesh_path(path, row_name, package, asset):
    """Issue 90 round 6: point an existing DT_BuildingMeshPathData row at another mesh."""
    data = load(path)
    rows = data["Exports"][0]["Table"]["Data"]
    paths = [n["AssetPath"] for n in walk(find_row(rows, row_name)) if isinstance(n, dict) and "AssetPath" in n]
    if len(paths) != 1:
        raise SystemExit(f"error: expected one soft path in row {row_name}, found {len(paths)}")
    before = f"{paths[0]['PackageName']}.{paths[0]['AssetName']}"
    paths[0]["PackageName"] = package
    paths[0]["AssetName"] = asset
    for name in (package, asset):
        if name not in data["NameMap"]:
            data["NameMap"].append(name)
    save(path, data)
    print(f"ok: row {row_name} mesh {before} -> {package}.{asset}")


def main(argv):
    if len(argv) == 7 and argv[1] == "copyfield":
        copy_field(argv[2], argv[3], argv[4], argv[5], float(argv[6]))
    elif len(argv) == 6 and argv[1] == "meshpath":
        set_mesh_path(argv[2], argv[3], argv[4], argv[5])
    elif len(argv) == 7 and argv[1] == "meshrow":
        clone_mesh_row(argv[2], argv[3], argv[4], argv[5], argv[6])
    elif len(argv) == 5 and argv[1] == "stats":
        clone_stats_row(argv[2], argv[3], argv[4])
    elif len(argv) == 5 and argv[1] == "planner":
        retarget_widget(argv[2], argv[3], argv[4])
    elif len(argv) == 6 and argv[1] == "blueprint":
        retarget_blueprint(argv[2], argv[3], argv[4], argv[5])
    elif len(argv) == 6 and argv[1] == "setnum":
        set_number_field(argv[2], argv[3], argv[4], argv[5])
    elif len(argv) == 4 and argv[1] == "visible":
        make_row_visible(argv[2], argv[3])
    elif len(argv) == 6 and argv[1] == "enum":
        set_enum_field(argv[2], argv[3], argv[4], argv[5])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
