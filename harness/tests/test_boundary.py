"""Boundary test (spec 22): the harness must not name the mod that it tests.

The harness finds mods only by path (mod/<Name>/) and by mod.json. A mod name in harness code would tie the harness to one mod
and block a later move of the harness to its own repo.
"""

import tempfile
import unittest
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parents[1]
CODE_SUFFIXES = {".py", ".lua", ".ps1"}
SKIPPED_PARTS = {"__pycache__", "baselines", "fixtures"}
# Split, so that this file does not name the mod itself.
FORBIDDEN = ("Invasion" + "Mod",)


def code_files(base: Path) -> list[Path]:
    return sorted(p for p in base.rglob("*") if p.suffix in CODE_SUFFIXES and not SKIPPED_PARTS & set(p.parts))


def find_violations(base: Path) -> list[str]:
    found = []
    for path in code_files(base):
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            found += [f"{path.relative_to(base).as_posix()}:{number} names {name}" for name in FORBIDDEN if name.lower() in line.lower()]
    return found


class BoundaryTests(unittest.TestCase):
    def test_harness_code_does_not_name_the_mod(self):
        violations = find_violations(HARNESS_DIR)
        self.assertEqual(violations, [], "harness code must find mods by path and mod.json only:\n  " + "\n  ".join(violations))

    def test_the_check_finds_a_planted_name_in_python_and_lua(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "a.py").write_text(f"x = '{FORBIDDEN[0]}'\n", encoding="utf-8")
            (Path(folder) / "b.lua").write_text(f"-- {FORBIDDEN[0].lower()}\n", encoding="utf-8")
            (Path(folder) / "c.py").write_text("x = 'OtherMod'\n", encoding="utf-8")
            self.assertEqual(len(find_violations(Path(folder))), 2)


if __name__ == "__main__":
    unittest.main()
