"""Generate the policy menu art set with genimage, then save small copies for the mod.

Usage: uv run python harness/tools/make_policy_art.py [--only ID,ID] [--size 256]

Full-size originals go to runs/genimage/policy/ (git-ignored).
Resized PNGs go to mod/PolicyMenu/art/ (committed). Names follow the policy id.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import genimage  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ORIGINALS = REPO / "runs" / "genimage" / "policy"
ART = REPO / "mod" / "PolicyMenu" / "art"

STYLE = ("Square game UI icon for a medieval city builder. Muted, earthy, hand-painted style like a 14th-century "
         "manuscript illumination, dark brown ink outline, aged parchment background with a thin double-line border, "
         "no text, no letters, subject centered and filling most of the square, flat lighting. Subject: ")

# Policy id -> subject. Ids and meanings come from spec 16 policies.md (DT_PolicyTypes).
POLICIES = {
    1: "Hardship: a thin peasant tightening a rope belt beside an almost empty grain sack",
    2: "Hunting grounds: a longbow and a deer antler crossed over a forest edge",
    3: "Craftsmanship: a carpenter's hammer, chisel and a finely carved wooden chair leg",
    4: "Night watch: a lantern hanging on a spear beside a town gate at night",
    6: "Light punishment: wooden stocks in a village square",
    7: "Bathhouse pleasures: a wooden bathtub with steam and a towel",
    8: "Weekly mass: a small stone church bell tower with a ringing bell",
    9: "Smallholdings: a small fenced vegetable plot beside a timber cottage",
    10: "Clean water: a stone village well with a wooden bucket of clear water",
    11: "Small land tax: a small stack of silver coins on a blank folded parchment with a red wax seal, the parchment has no writing",
    12: "Strict fasting: an empty wooden bowl and a loaf of bread with a slice cut away",
    13: "Forest preservation: an oak tree with a wooden fence around it and a raised palm",
    14: "Tithe: a sheaf of wheat being placed into a church basket",
    15: "Coinage: a coin die and hammer striking a silver penny",
    16: "Guild brotherhoods: three craftsmen's tools tied together with a ribbon under a guild banner",
    17: "Public weapons ban: a sword and an axe crossed out by a chained lock",
    18: "Purchase privilege: a royal charter scroll with a wax seal and a coin purse",
}

PANEL_PROMPT = ("Wide background panel for a medieval game menu: aged parchment sheet with torn edges, faint ink border "
                "with celtic knot corners, empty center, no text, no letters, even soft lighting, 16:9.")


def make_one(name: str, prompt: str, size: tuple[int, int]) -> Path:
    original = ORIGINALS / f"{name}.png"
    if not original.exists():
        genimage.generate(genimage.DEFAULT_MODEL, prompt, original, 1)
    ART.mkdir(parents=True, exist_ok=True)
    small = ART / f"{name}.png"
    with Image.open(original) as image:
        image.convert("RGB").resize(size, Image.LANCZOS).save(small, optimize=True)
    return small


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="comma-separated policy ids, or 'panel'")
    parser.add_argument("--size", type=int, default=256, help="icon edge in pixels")
    args = parser.parse_args()
    wanted = set(args.only.split(",")) if args.only else None
    for policy_id, subject in POLICIES.items():
        if wanted is None or str(policy_id) in wanted:
            path = make_one(f"policy_{policy_id}", STYLE + subject, (args.size, args.size))
            print(f"policy {policy_id}: {path.name} {path.stat().st_size} bytes")
    if wanted is None or "panel" in wanted:
        path = make_one("panel", PANEL_PROMPT, (1024, 576))
        print(f"panel: {path.name} {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
