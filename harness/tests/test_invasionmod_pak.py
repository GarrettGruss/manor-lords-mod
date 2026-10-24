"""A mod with features ships one pak, named like the mod, that holds the table rows and all widgets
(change update-single-mod-pak). The test reads the committed pak with repak when it is installed.
"""

import json
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPAK = Path("C:/Program Files/repak_cli/bin/repak.exe")


def feature_mods() -> list[Path]:
    return [m.parent for m in sorted((REPO / "mod").glob("*/mod.json"))
            if "features" in json.loads(m.read_text(encoding="utf-8"))]


class SingleModPakTest(unittest.TestCase):
    def test_manifest_names_one_pak_like_the_mod(self):
        for mod in feature_mods():
            manifest = json.loads((mod / "mod.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pak"], {"name": mod.name, "source": "file"}, mod.name)

    def test_only_one_pak_is_committed(self):
        for mod in feature_mods():
            self.assertEqual([p.name for p in (mod / "paks").glob("*.pak")], [f"{mod.name}_P.pak"], mod.name)

    def test_widget_assets_have_one_owner(self):
        for mod in feature_mods():
            seen: set[str] = set()
            for asset in (mod / "data").glob("*/assets/**/*.uasset"):
                self.assertNotIn(asset.name, seen, f"{asset.name} has two owners")
                seen.add(asset.name)

    @unittest.skipUnless(REPAK.exists(), "repak is not installed")
    def test_pak_holds_every_widget_asset_and_table(self):
        for mod in feature_mods():
            listing = subprocess.run([str(REPAK), "list", str(mod / "paks" / f"{mod.name}_P.pak")],
                                     capture_output=True, text=True, check=True).stdout
            assets = {p.name for p in (mod / "data").glob("*/assets/**/*") if p.is_file()}
            self.assertTrue(any(name.startswith("WBP_") for name in assets))
            for name in assets:
                self.assertIn("/" + name, listing)
            self.assertIn("DT_GameSetupPresets.uasset", listing)


if __name__ == "__main__":
    unittest.main()
