"""Clone one row of an unpacked data table JSON and change fields (spec 29 spike).

Why a script: a new row needs the same edit every time (copy, rename, add to the name map, set fields).
Usage (paths are absolute; the JSON comes from `pakmod.py tojson`):
  uv run python harness/tools/clone_table_row.py <json> <source row> <new row> [--set field=value ...] [--array field=1,2,3 ...] [--names field=a,b ...]
--set changes a number, bool or string field. --array replaces an int array field. --names replaces a name array field (it needs one element to copy; an empty list is allowed).
The JSON file is changed in place. The table is named in the JSON, so the tool works for every row table.
"""
import argparse
import copy
import json


def find_property(row: dict, field: str) -> dict:
    for prop in row["Value"]:
        if prop["Name"] == field:
            return prop
    raise SystemExit(f"error: field {field!r} not found in row {row['Name']!r}")


def convert(old, text: str, type_name: str = ""):
    if "FloatPropertyData" in type_name or "DoublePropertyData" in type_name:
        return float(text)
    if isinstance(old, bool):
        return text.lower() in ("1", "true")
    if isinstance(old, int):
        return int(text)
    if isinstance(old, float):
        return float(text)
    return text


def set_scalar(row: dict, field: str, text: str) -> None:
    prop = find_property(row, field)
    prop["Value"] = convert(prop["Value"], text, prop["$type"])


def set_int_array(row: dict, field: str, text: str) -> None:
    prop = find_property(row, field)
    template = copy.deepcopy(prop["Value"][0]) if prop["Value"] else None
    numbers = [int(item) for item in text.split(",") if item.strip()]
    if numbers and template is None:
        raise SystemExit(f"error: array {field!r} is empty; the tool cannot copy an element")
    elements = []
    for index, number in enumerate(numbers):
        element = copy.deepcopy(template)
        element["Name"] = str(index)
        element["Value"] = number
        elements.append(element)
    prop["Value"] = elements


def set_name_array(row: dict, field: str, text: str) -> None:
    prop = find_property(row, field)
    names = [item for item in text.split(",") if item.strip()]
    if not names:
        prop["Value"] = []
        return
    if not prop["Value"]:
        raise SystemExit(f"error: array {field!r} is empty; the tool cannot copy an element")
    template = prop["Value"][0]
    elements = []
    for index, name in enumerate(names):
        element = copy.deepcopy(template)
        element["Name"] = str(index)
        element["Value"] = name
        elements.append(element)
    prop["Value"] = elements


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json")
    parser.add_argument("source")
    parser.add_argument("new")
    parser.add_argument("--set", action="append", default=[])
    parser.add_argument("--array", action="append", default=[])
    parser.add_argument("--names", action="append", default=[])
    args = parser.parse_args()
    with open(args.json, encoding="utf-8") as handle:
        data = json.load(handle)
    rows = data["Exports"][0]["Table"]["Data"]
    names = [row["Name"] for row in rows]
    if args.new in names:
        raise SystemExit(f"error: row {args.new} already exists")
    if args.source not in names:
        raise SystemExit(f"error: source row {args.source} not found")
    clone = copy.deepcopy(rows[names.index(args.source)])
    clone["Name"] = args.new
    for item in args.set:
        field, _, text = item.partition("=")
        set_scalar(clone, field, text)
    for item in args.array:
        field, _, text = item.partition("=")
        set_int_array(clone, field, text)
    for item in args.names:
        field, _, text = item.partition("=")
        set_name_array(clone, field, text)
        for name in text.split(","):
            if name and name not in data["NameMap"]:
                data["NameMap"].append(name)
    rows.append(clone)
    if args.new not in data["NameMap"]:
        data["NameMap"].append(args.new)
    with open(args.json, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    print(f"ok: row {args.new} cloned from {args.source}; {len(rows)} rows")


if __name__ == "__main__":
    main()
