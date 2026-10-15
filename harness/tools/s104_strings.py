"""Find strings (ASCII and UTF-16LE) in the game executable that match a regex (spec 18, issue #104). Read only.

Usage: s104_strings.py <regex> [--max N]
Prints the offset and the full string around each match (up to 120 characters).
"""
import re
import sys
from pathlib import Path

EXE = Path("C:/Program Files (x86)/Steam/steamapps/common/Manor Lords/ManorLords/Binaries/Win64/ManorLords-Win64-Shipping.exe")
CONTEXT = 60


def print_around(offset, length):
    with EXE.open("rb") as handle:
        handle.seek(offset)
        chunk = handle.read(length)
    for text in re.findall(rb"[\x20-\x7e]{3,}", chunk):
        print(text.decode("ascii"))


def main():
    if sys.argv[1] == "--at":
        print_around(int(sys.argv[2], 16), int(sys.argv[3]))
        return
    pattern = sys.argv[1]
    limit = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 80
    data = EXE.read_bytes()
    ascii_regex = re.compile(rb"[\x20-\x7e]{0,%d}(?:%s)[\x20-\x7e]{0,%d}" % (CONTEXT, pattern.encode(), CONTEXT), re.IGNORECASE)
    wide_regex = re.compile(rb"(?:[\x20-\x7e]\x00){0,%d}(?:%s)(?:[\x20-\x7e]\x00){0,%d}" % (CONTEXT, "".join(c + "\x00" for c in pattern).encode(), CONTEXT), re.IGNORECASE)
    seen = set()
    count = 0
    for label, regex in (("ascii", ascii_regex), ("utf16", wide_regex)):
        for match in regex.finditer(data):
            text = match.group(0).decode("latin1" if label == "ascii" else "utf-16le", errors="replace")
            if text in seen:
                continue
            seen.add(text)
            print(label, hex(match.start()), text)
            count += 1
            if count >= limit:
                return


main()
