"""The guarded harness save (spec 24, plan step 2). The only harness code that makes the game write a save.

The game writes saves into the user's REAL save folder, also when a run has a private LOCALAPPDATA.
A probe once overwrote the user's `saveGame_9` this way. So a harness save does this, in order:

1. Choose the next free slot `saveGame_<N>` (the same rule as fixtures). Refuse if any file of it exists.
2. Copy the whole save folder to a backup folder outside the game folder. Check the copy by hash.
3. Send the named command `save_game` to the mod. The mod calls the game save function. It refuses an existing slot too.
4. Wait until the new files are complete and stop changing.
5. Compare the folder with the snapshot. Only files of the new slot may be new. Any other change is a failure:
   restore the changed or removed files from the backup and raise.
6. Write the new files to the slot ledger, so the run end (or the next run) deletes them. A scenario may keep them.
"""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path
from typing import Callable

from . import fixtures, saveslots

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKUP_ROOT = REPO_ROOT / "runs" / "save-backups"
KEPT_BACKUPS = 5
SAVE_TIMEOUT_S = 30.0
POLL_S = 0.2
STABLE_POLLS = 2
MAX_LABEL = 40
LABEL = re.compile(r"^[A-Za-z0-9 _\-]+$")
NEW_SLOT_FILE = r"^{slot}(?:_descr\.sav|\.sav|\.png|_coat_\d+\.png)$"


class SaveGuardError(RuntimeError):
    """The harness save did not meet the safety rules. The message says what happened and what was restored."""


# ---- backup ----

def backup_folder(save_dir: Path, backup_root: Path = BACKUP_ROOT, kept: int = KEPT_BACKUPS,
                  now: Callable[[], float] = time.time) -> Path:
    """Copy `save_dir` to a new folder in `backup_root`, check the copy by hash, and delete the oldest backups."""
    if not save_dir.is_dir():
        raise SaveGuardError(f"the save folder does not exist: {save_dir}")
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(now()))
    target = backup_root / f"saves-{stamp}"
    counter = 1
    while target.exists():  # two saves in one second
        counter += 1
        target = backup_root / f"saves-{stamp}-{counter}"
    shutil.copytree(save_dir, target)
    problems = fixtures.describe_difference(fixtures.snapshot_user_files(save_dir), fixtures.snapshot_user_files(target))
    if problems:
        raise SaveGuardError(f"the backup {target} does not match the save folder: {'; '.join(problems[:10])}")
    _prune_backups(backup_root, kept)
    return target


def _prune_backups(backup_root: Path, kept: int) -> None:
    backups = sorted(p for p in backup_root.iterdir() if p.is_dir() and p.name.startswith("saves-"))
    for old in backups[:-kept]:
        shutil.rmtree(old)


# ---- the check ----

def judge(before: dict[str, str], after: dict[str, str], slot: str) -> tuple[list[str], list[str]]:
    """Return (damaged existing file names, unexpected new file names). The new slot files are expected."""
    pattern = re.compile(NEW_SLOT_FILE.format(slot=re.escape(slot)))
    damaged = [name for name in before if after.get(name) != before[name]]
    unexpected = [name for name in after if name not in before and not pattern.match(name)]
    return damaged, unexpected


def restore(backup: Path, save_dir: Path, names: list[str]) -> list[str]:
    """Copy files back from the backup. Return the names that could not be restored."""
    failed = []
    for name in names:
        source = backup / name
        try:
            if not source.is_file():
                raise OSError("not a file in the backup")
            shutil.copy2(source, save_dir / name)
        except OSError as error:
            failed.append(f"{name} ({error})")
    return failed


def check_and_restore(save_dir: Path, before: dict[str, str], backup: Path, slot: str) -> dict[str, str]:
    """Raise SaveGuardError if the folder changed in a way other than the new slot files. Return the new slot files."""
    after = fixtures.snapshot_user_files(save_dir)
    damaged, unexpected = judge(before, after, slot)
    if damaged or unexpected:
        message = f"the harness save broke the rules for slot {slot}."
        if damaged:
            failed = restore(backup, save_dir, damaged)
            message += f" Existing files changed or removed: {damaged}; restored from {backup}"
            message += f" (NOT restored: {failed})." if failed else "."
        if unexpected:
            message += f" Unexpected new files (left in place): {unexpected}."
        raise SaveGuardError(message)
    return {name: digest for name, digest in after.items() if name not in before}


def wait_for_slot(save_dir: Path, slot: str, timeout_s: float, sleep: Callable[[float], None],
                  monotonic: Callable[[], float]) -> None:
    """Wait until `<slot>.sav` exists and the whole folder is unchanged for STABLE_POLLS polls."""
    started = monotonic()
    last, stable = None, 0
    while True:
        current = fixtures.snapshot_user_files(save_dir)
        stable = stable + 1 if current == last else 0
        last = current
        if f"{slot}.sav" in current and stable >= STABLE_POLLS:
            return
        if monotonic() - started > timeout_s:
            raise SaveGuardError(f"timeout: {slot}.sav did not appear and settle within {timeout_s:.0f} s")
        sleep(POLL_S)


# ---- the action ----

def choose_slot(save_dir: Path) -> str:
    slot = saveslots.next_free_slot(save_dir)
    pattern = re.compile(rf"^{re.escape(slot)}(?:[._]|$)")
    existing = [p.name for p in save_dir.iterdir() if pattern.match(p.name)] if save_dir.is_dir() else []
    if existing:
        raise SaveGuardError(f"refused: files of slot {slot} exist already: {existing}")
    return slot


def check_label(label: str) -> str:
    if not LABEL.match(label) or len(label) > MAX_LABEL:
        raise SaveGuardError(f"bad save label {label!r}: use letters, digits, space, '-' and '_' only, up to {MAX_LABEL} characters")
    return label


def save_game(save_dir: Path, send: Callable[..., dict], label: str, keep: bool = False, backup_root: Path = BACKUP_ROOT,
              ledger_path: Path | None = None, timeout_s: float = SAVE_TIMEOUT_S, sleep: Callable[[float], None] = time.sleep,
              monotonic: Callable[[], float] = time.monotonic, now: Callable[[], float] = time.time) -> dict:
    """Make one guarded save. `send(command, **fields)` sends a named command to the mod and returns its answer.

    Returns {"slot", "files" (name to SHA-256), "backup", "kept", "user_files"}. Raises SaveGuardError on any rule break.
    """
    check_label(label)
    slot = choose_slot(save_dir)
    backup = backup_folder(save_dir, backup_root, now=now)
    before = fixtures.snapshot_user_files(save_dir)
    try:
        send("save_game", slot=slot, name=f"harness {label}")
        wait_for_slot(save_dir, slot, timeout_s, sleep, monotonic)
    except BaseException:
        _check_after_failure(save_dir, before, backup, slot, label, ledger_path)
        raise
    files = check_and_restore(save_dir, before, backup, slot)
    if not keep:
        saveslots.record_saved(save_dir, slot, label, files, ledger_path)
    return {"slot": slot, "files": files, "backup": str(backup), "kept": keep, "user_files": len(before)}


def _check_after_failure(save_dir: Path, before: dict[str, str], backup: Path, slot: str, label: str,
                         ledger_path: Path | None) -> None:
    """After a refused command or a timeout: still restore damage, and register stray slot files for cleanup."""
    files = check_and_restore(save_dir, before, backup, slot)  # raises with the damage, which hides the first error
    if files:
        saveslots.record_saved(save_dir, slot, label, files, ledger_path)
