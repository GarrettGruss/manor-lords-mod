"""Spec 33. Re-cook an old pak that holds a Meshy mesh so that it uses the game material instance.

Steps: unpack the old pak, delete the old material and the unused textures of the mesh folder, copy the cooked
`MI_Meshy`, mesh and three textures from the UE workspace, then build with `pakmod.py build`.
Usage: uv run python harness/tools/recook_meshy_pak.py <old pak> <new name> <mesh folder, e.g. OxShed>
The new pak is written to <work_dir>/out/<new name>_P.pak. The old pak is not changed.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "harness" / "pakmod.local.json"
COOKED = Path("C:/Users/garre/development/mlm-ue/ManorLords/Saved/Cooked/Windows/ManorLords/Content/HarnessMod")
KEEP_STEMS = ("MI_Meshy", "texture_0", "texture_0_normal", "texture_0_roughness")
EXTENSIONS = (".uasset", ".uexp", ".ubulk")
REMOVE_STEMS = ("Material_001", "texture_0_emission", "texture_0_metallic")


def fail(message: str) -> None:
    sys.exit("recook_meshy_pak: " + message)


def unpack(repak: str, old_pak: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    subprocess.run([repak, "unpack", "-q", "-o", str(target), str(old_pak)], check=True)


def swap_files(target: Path, mesh_folder: str) -> None:
    folder = target / "ManorLords" / "Content" / "HarnessMod" / mesh_folder
    if not folder.is_dir():
        fail("mesh folder not in the pak: " + str(folder))
    for stem in REMOVE_STEMS:
        for extension in EXTENSIONS:
            (folder / (stem + extension)).unlink(missing_ok=True)
    cooked = COOKED / mesh_folder
    for stem in KEEP_STEMS:
        found = [cooked / (stem + extension) for extension in EXTENSIONS if (cooked / (stem + extension)).is_file()]
        if not found:
            fail("cooked file missing: " + str(cooked / stem))
        for source in found:
            shutil.copy2(source, folder / source.name)


def main() -> None:
    if len(sys.argv) != 4:
        fail("usage: recook_meshy_pak.py <old pak> <new name> <mesh folder>")
    old_pak, name, mesh_folder = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    target = Path(config["work_dir"]) / name
    unpack(config["repak"]["path"], old_pak, target)
    swap_files(target, mesh_folder)
    subprocess.run([sys.executable, str(REPO / "harness" / "tools" / "pakmod.py"), "build", name], check=True)


main()
