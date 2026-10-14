"""Print the fields of building rows side by side, to find what differs. Static study for issue 94."""

import json
import sys


def property_text(prop):
    value = prop.get("Value")
    text = json.dumps(value, default=str)
    if isinstance(value, list) and value and isinstance(value[0], dict) and "Name" in value[0]:
        text = ";".join(f"{p['Name']}={json.dumps(p.get('Value'), default=str)[:80]}" for p in value)
    return text[:300]


def load_rows(path):
    data = json.load(open(path, encoding="utf-8"))
    table = data["Exports"][0]["Table"]["Data"]
    return {str(row["Name"]): {p["Name"]: property_text(p) for p in row["Value"]} for row in table}


def main():
    path = sys.argv[1]
    names = sys.argv[2:]
    rows = load_rows(path)
    missing = [n for n in names if n not in rows]
    if missing:
        raise SystemExit(f"rows not found: {missing}; sample: {list(rows)[:5]}")
    keys = sorted(set().union(*(rows[n].keys() for n in names)))
    for key in keys:
        values = [rows[n].get(key, "-") for n in names]
        flag = "DIFF" if len(set(values)) > 1 else "same"
        print(f"{flag} {key} | " + " | ".join(values))


if __name__ == "__main__":
    main()
