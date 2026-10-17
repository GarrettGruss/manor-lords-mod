"""Game slots: several copies of the game that can run at the same time (spec 11).

Slot 0 is the normal game folder. Slots 1 to 3 are the folders that harness/install.ps1 built and listed in
slots/.install/slots.json. A slot is only a game folder: the run lock, the deploy and the process search use its root.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .game import GameInstall, _default_root
from .shared import SHARED_ROOT

SLOTS_DIR = SHARED_ROOT / "slots"  # harness/install.ps1 builds them once, in the main checkout
MAX_SLOT = 3
# Screen tiles for 1280x720 windows on a 2560x1440 screen. Slot n uses tile n, so windows do not cover each other.
TILES = ((0, 0), (1280, 0), (0, 720), (1280, 720))


class SlotError(RuntimeError):
    """A slot is unknown or its state file is broken. The message says which."""


@dataclass(frozen=True)
class GameSlot:
    number: int
    root: Path

    def install(self) -> GameInstall:
        return GameInstall(root=self.root, steam_root=_default_root())

    @property
    def tile(self) -> tuple[int, int]:
        return TILES[self.number]


def _state_dir(slots_dir: Path | None) -> Path:
    return (slots_dir or SLOTS_DIR) / ".install"


def settings_installed(slots_dir: Path | None = None) -> bool:
    """True if install.ps1 wrote the harness settings (windowed 1280x720), so windows can be placed in tiles."""
    return (_state_dir(slots_dir) / "settings.json").is_file()


# The game writes this settings file of the user's save folder when its settings differ. install.ps1 backs it up and
# uninstall.ps1 restores it, so the save check of a run leaves it out while the harness settings are installed.
INSTALL_MANAGED_SAVE_FILES = frozenset({"rtsSettings.sav"})


def install_managed_save_files(slots_dir: Path | None = None) -> frozenset[str]:
    return INSTALL_MANAGED_SAVE_FILES if settings_installed(slots_dir) else frozenset()


def installed_slots(slots_dir: Path | None = None, game_root: Path | None = None) -> list[GameSlot]:
    """Slot 0 and every slot in slots.json whose game executable exists, in slot order."""
    slots = [GameSlot(0, game_root or _default_root())]
    state_path = _state_dir(slots_dir) / "slots.json"
    if not state_path.is_file():
        return slots
    try:
        entries = json.loads(state_path.read_text(encoding="utf-8-sig"))["slots"]
    except (ValueError, KeyError) as error:
        raise SlotError(f"slot state file is broken: {state_path}: {error}") from error
    for entry in sorted(entries, key=lambda item: int(item["slot"])):
        slot = GameSlot(int(entry["slot"]), Path(entry["root"]))
        if 1 <= slot.number <= MAX_SLOT and slot.install().exe.is_file():
            slots.append(slot)
    return slots


def get_slot(number: int, slots_dir: Path | None = None, game_root: Path | None = None) -> GameSlot:
    for slot in installed_slots(slots_dir, game_root):
        if slot.number == number:
            return slot
    raise SlotError(f"slot {number} is not installed. Run harness/install.ps1, or use slot 0 (the game folder).")
