"""Compare two bridge `props` dumps (JSON files from s94_bridge.py) and print the properties whose value differs.

    uv run python harness/tools/s94_propdiff.py a.json b.json
"""

import json
import re
import sys


def load(path):
    text = open(path, encoding="utf-8").read()
    props = json.loads(text[text.index("["):])[0]["result"]["properties"]
    return {prop["name"]: json.dumps(prop["value"], sort_keys=True) for prop in props}


def normalise(text):
    return re.sub(r'"address": \d+|_\d{6,}', "", text)


def main(argv):
    left, right = load(argv[0]), load(argv[1])
    for name in sorted(set(left) | set(right)):
        a, b = normalise(left.get(name, "-")), normalise(right.get(name, "-"))
        if a != b:
            print(f"{name}\n   A: {a[:260]}\n   B: {b[:260]}")


if __name__ == "__main__":
    main(sys.argv[1:])
