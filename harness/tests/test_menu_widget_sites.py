"""Rule test (change add-mod-menu-access-rule): only the base menu (Scripts/core/menu.lua) makes a mod menu widget.

A menu that calls AddToViewport or WidgetBlueprintLibrary itself would have its own bottom bar button, backdrop and
click blocking. The base menu owns those parts. This test scans every Lua file of the pack mod, like test_save_call_sites.py.
"""

import re
import tempfile
import unittest
from pathlib import Path

import fakegame_path  # noqa: F401
from test_fakegame_modstate import find_pack_mod

WIDGET_CALLS = re.compile(r"AddToViewport|WidgetBlueprintLibrary")
BASE_MENU = "core/menu.lua"


def is_comment(line: str) -> bool:
    return line.lstrip().startswith("--")


def find_sites(scripts: Path) -> list[str]:
    found = []
    for path in sorted(scripts.rglob("*.lua")):
        relative = path.relative_to(scripts).as_posix()
        if relative == BASE_MENU:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if WIDGET_CALLS.search(line) and not is_comment(line):
                found.append(f"{relative}:{number}: {line.strip()[:100]}")
    return found


class MenuWidgetSiteTests(unittest.TestCase):
    def test_only_the_base_menu_makes_a_menu_widget(self):
        self.assertEqual(find_sites(find_pack_mod() / "Scripts"), [], "a menu makes its own widget; use core/menu.lua")

    def test_the_base_menu_exists_and_makes_widgets(self):
        text = (find_pack_mod() / "Scripts" / BASE_MENU).read_text(encoding="utf-8")
        self.assertIn("AddToViewport", text)

    def test_the_check_finds_a_planted_call_and_skips_comments(self):
        with tempfile.TemporaryDirectory() as folder:
            scripts = Path(folder)
            (scripts / "features").mkdir()
            (scripts / "features" / "bad.lua").write_text("widget:AddToViewport(5)\n", encoding="utf-8")
            (scripts / "features" / "ok.lua").write_text("-- AddToViewport is named in a comment\n", encoding="utf-8")
            (scripts / "core").mkdir()
            (scripts / "core" / "menu.lua").write_text("widget:AddToViewport(1)\n", encoding="utf-8")
            self.assertEqual(len(find_sites(scripts)), 1)


if __name__ == "__main__":
    unittest.main()
