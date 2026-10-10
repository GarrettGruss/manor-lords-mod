"""Install harness paks in preflight and remove them in teardown (`run.py --pak`, spec 10 U4).

The cleanup is its own phase with always_run, so a crash, a timeout or a failed earlier phase still removes the paks.
"""

from __future__ import annotations

from pathlib import Path

from . import paks
from .game import GameInstall
from .runfolder import write_config
from .runner import Phase, PhaseContext, PhaseFailed

PAK_PHASE_NAME = "paks-remove"
SHA_PREFIX_CHARS = 12


def pak_summary_entry(name: str, sha256: str) -> str:
    return f"{name}:{sha256[:SHA_PREFIX_CHARS]}"


def install_paks(install: GameInstall, ctx: PhaseContext, names: list[str], work_dir: Path) -> None:
    """Install each pak. The name is stored first, so the cleanup phase knows what to try to remove."""
    installed: list[str] = ctx.state.setdefault("paks_installed", [])
    entries = ctx.config.setdefault("environment", {}).setdefault("paks", [])
    for name in names:
        installed.append(name)
        source = paks.built_pak_path(work_dir, name)
        if not source.is_file():
            raise PhaseFailed(f"pak {name!r} is not built: {source}. Run pakmod.py build {name} first.")
        try:
            target = paks.install_pak(source, install.root, paks.pak_file_name(name))
        except paks.PakError as error:
            raise PhaseFailed(f"pak {name!r}: {error}") from error
        entries.append(pak_summary_entry(name, paks.sha256_of(target)))
    write_config(ctx.run, ctx.config)


def _remove_paks(install: GameInstall):
    def run(ctx: PhaseContext) -> str | None:
        names = ctx.state.get("paks_installed", [])
        try:
            removed = paks.remove_listed(install.root, names)
        except paks.PakError as error:
            raise PhaseFailed(f"could not remove the paks {names}: {error}. Run pakmod.py remove --all") from error
        if removed:
            raise PhaseFailed(f"{removed} pak(s) were changed after install and were NOT removed. Run pakmod.py list")
        return f"paks removed: {names}" if names else None

    return run


def remove_paks_phase(install: GameInstall) -> Phase:
    return Phase(PAK_PHASE_NAME, _remove_paks(install), 30, always_run=True)
