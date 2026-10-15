"""Search the game jmap for property, function and class names (spec 18, issue #104). Read only.

Usage: s104_jmap.py <regex> [--owner <regex>]
Prints "owner | kind | name | type" for each match. The jmap path is read from the game folder.
"""
import json
import re
import sys
from pathlib import Path

JMAP_DIR = Path("C:/Program Files (x86)/Steam/steamapps/common/Manor Lords/ManorLords/Binaries/Win64/ue4ss")
MAX_LINES = 100000


def find_jmap():
    matches = sorted(JMAP_DIR.glob("*.jmap"))
    if not matches:
        raise SystemExit(f"no jmap in {JMAP_DIR}")
    return matches[0]


def type_text(prop):
    text = str(prop.get("type", ""))
    for key in ("struct", "class", "enum", "inner", "value_prop", "key_prop", "property_class", "property_struct"):
        if key in prop and isinstance(prop[key], (str, dict)):
            text += f" {key}={prop[key] if isinstance(prop[key], str) else prop[key].get('type', '')}"
    return text


def main():
    pattern = re.compile(sys.argv[1], re.IGNORECASE)
    owner_pattern = re.compile(sys.argv[sys.argv.index("--owner") + 1], re.IGNORECASE) if "--owner" in sys.argv else None
    data = json.loads(find_jmap().read_text(encoding="utf8"))
    printed = 0
    for path, obj in data["objects"].items():
        owner = path.rsplit(".", 1)[-1]
        if owner_pattern and not owner_pattern.search(owner):
            continue
        if pattern.search(owner) and not owner_pattern:
            print(owner, "| object |", obj.get("type"), "| super", obj.get("super_struct"))
            printed += 1
        for prop in obj.get("properties", []):
            if pattern.search(str(prop.get("name"))):
                print(owner, "| prop |", prop.get("name"), "|", type_text(prop))
                printed += 1
        for func in obj.get("functions", []) if isinstance(obj.get("functions"), list) else []:
            if pattern.search(str(func.get("name"))):
                params = [p.get("name") for p in func.get("properties", [])]
                print(owner, "| func |", func.get("name"), "|", params)
                printed += 1
        if printed >= MAX_LINES:
            print("... truncated")
            break


main()
