"""Build the release zip in game-folder layout (spec 19)."""

from __future__ import annotations

import zipfile
from pathlib import Path

from .files import mod_files

MODS_PREFIX = "ManorLords/Binaries/Win64/ue4ss/Mods"
PAK_PREFIX = "ManorLords/Content/Paks/~mods"
PAK_FOLDER = "paks"  # inside mod/<Name>/
SOURCE_FOLDERS = (PAK_FOLDER, "ue", "art")  # not part of the Lua mod folder in the zip (ue: UE project sources of the pak; art: image sources for UE)
PAK_SIZE_WARNING_BYTES = 10 * 1024 * 1024  # a bigger pak gets a warning (not a failure)


def pak_size_warning(name: str, size: int) -> str | None:
    if size <= PAK_SIZE_WARNING_BYTES:
        return None
    return (f"WARNING: pak {name} is {size / (1024 * 1024):.1f} MB, over the {PAK_SIZE_WARNING_BYTES // (1024 * 1024)} MB limit "
            "for a plain git file. Consider Git LFS before you commit it.")

ZIP_DATE = (2026, 1, 1, 0, 0, 0)  # fixed, so the same files give the same zip bytes


class BuildError(Exception):
    """The zip cannot be built."""


def zip_name(manifest: dict) -> str:
    return f"{manifest['name']}-v{manifest['version']}.zip"


def tag_name(manifest: dict) -> str:
    return f"{manifest['name'].lower()}-v{manifest['version']}"


def readme_text(manifest: dict, shared: list[str], has_pak: bool) -> str:
    name, tested = manifest["name"], manifest["tested"]
    pak_lines = ""
    if has_pak:
        pak_lines = (f"  ManorLords\\Content\\Paks\\~mods\\{manifest['pak']['name']}_P.pak\n")
    return f"""{name} {manifest['version']}
{manifest['description']}

Tested with
  Manor Lords {tested['game']} (Steam build {tested['game_build']})
  RE-UE4SS {tested['ue4ss']} (the experimental build with the ue4ss folder layout)

Install
  1. Install RE-UE4SS in the game folder (dwmapi.dll and a ue4ss folder next to ManorLords-Win64-Shipping.exe).
  2. Close the game.
  3. Unpack this zip into the Manor Lords folder (the folder that holds ManorLords\\). Keep the folder names.
     It adds:
  ManorLords\\Binaries\\Win64\\ue4ss\\Mods\\{name}\\
{''.join(f'  ManorLords\\Binaries\\Win64\\ue4ss\\Mods\\shared\\{module}\\' + chr(10) for module in shared)}{pak_lines}  4. Start the game. The mod loads by itself (enabled.txt).

Uninstall
  Delete the folders and files listed above. Do not delete the folder Mods\\shared if other mods use it.

This is a pre-release for play testers. Back up your saves first. The mod does not write saves.
"""


def _add(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def committed_pak_path(manifest: dict, repo_root: Path) -> Path:
    """Where a committed pak lives: pak.path, else mod/<Name>/paks/<pak>_P.pak."""
    pak = manifest["pak"]
    return (repo_root / (pak.get("path") or f"mod/{manifest['name']}/paks/{pak['name']}_P.pak")).resolve()


def find_pak(manifest: dict, repo_root: Path, pak_dir: Path | None) -> Path:
    """The pak file named by the manifest. Raise BuildError with a clear message when it is missing."""
    pak = manifest["pak"]
    if pak["source"] == "file":
        path = committed_pak_path(manifest, repo_root)
        if not path.is_file():
            raise BuildError(f"committed pak {path} does not exist. Build it (pakmod.py build {pak['name']}), copy it there and commit it.")
        return path
    if pak_dir is None:
        raise BuildError(f"pak source is build: give the folder that holds {pak['name']}_P.pak with --pak-dir (output of pakmod.py build)")
    matches = sorted(pak_dir.rglob(f"{pak['name']}_P.pak"))
    if not matches:
        raise BuildError(f"{pak['name']}_P.pak not found under {pak_dir}. Run: uv run python harness/tools/pakmod.py build {pak['name']}")
    return matches[-1]


def build_zip(manifest: dict, mod_root: Path, shared: list[str], out_dir: Path, repo_root: Path, pak_dir: Path | None = None) -> Path:
    """Write out_dir/<Name>-v<version>.zip. Return its path."""
    name = manifest["name"]
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / zip_name(manifest)
    temporary = target.with_suffix(".zip.tmp")  # write a temporary file, then rename
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for path in mod_files(mod_root / name):
                if path.relative_to(mod_root / name).parts[0] in SOURCE_FOLDERS:
                    continue  # the pak goes to Content/Paks/~mods; the UE sources stay in the repo
                _add(archive, f"{MODS_PREFIX}/{name}/{path.relative_to(mod_root / name).as_posix()}", path.read_bytes())
            _add(archive, f"{MODS_PREFIX}/{name}/enabled.txt", b"")
            for module in shared:
                for path in mod_files(mod_root / "shared" / module):
                    _add(archive, f"{MODS_PREFIX}/shared/{module}/{path.relative_to(mod_root / 'shared' / module).as_posix()}", path.read_bytes())
            if manifest.get("pak"):
                _add(archive, f"{PAK_PREFIX}/{manifest['pak']['name']}_P.pak", find_pak(manifest, repo_root, pak_dir).read_bytes())
            _add(archive, "README.txt", readme_text(manifest, shared, bool(manifest.get("pak"))).replace("\n", "\r\n").encode("utf-8"))
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    temporary.replace(target)
    return target
