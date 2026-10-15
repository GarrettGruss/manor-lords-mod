"""Print every field that differs between rows of the vanilla buildingStats JSON (issue #90).

Usage: uv run python harness/tools/s90_row_diff.py <buildingStats.json> <row> <row> [<row> ...]
Prints a table: field, then the value of each row. Equal fields are skipped.
Reads the file only.
"""
import json
import sys


def flatten(prop: dict, prefix: str = "") -> dict[str, str]:
    name = prefix + prop["Name"]
    value = prop.get("Value")
    if isinstance(value, list) and value and isinstance(value[0], dict) and "Name" in value[0]:
        flat: dict[str, str] = {}
        for child in value:
            flat.update(flatten(child, name + "."))
        return flat
    if isinstance(value, list):
        items = [json.dumps(item.get("Value", item), sort_keys=True)[:80] if isinstance(item, dict) else str(item)
                 for item in value]
        return {name: "[" + ", ".join(items) + "]"}
    if isinstance(value, dict):
        return {name: json.dumps(value, sort_keys=True)}
    return {name: str(value)}


def row_fields(table: list[dict], row: str) -> dict[str, str]:
    for entry in table:
        if entry["Name"] == row:
            fields: dict[str, str] = {}
            for prop in entry["Value"]:
                fields.update(flatten(prop))
            return fields
    sys.exit(f"row not found: {row}")


def main() -> None:
    if len(sys.argv) < 4:
        sys.exit("usage: s90_row_diff.py <buildingStats.json> <row> <row> [<row> ...]")
    with open(sys.argv[1], encoding="utf-8") as handle:
        asset = json.load(handle)
    table = asset["Exports"][0]["Table"]["Data"]
    rows = sys.argv[2:]
    data = {row: row_fields(table, row) for row in rows}
    for field in data[rows[0]]:
        values = [data[row].get(field, "<missing>") for row in rows]
        if len(set(values)) > 1:
            print(field, " | ".join(v[-90:] for v in values))


if __name__ == "__main__":
    main()
