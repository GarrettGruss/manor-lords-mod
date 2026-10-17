"""Install a save into the game's save folder under a free slot name, and remove it again (spec 06, part D).

Why this exists: the game lists and loads saves only from the user's REAL save folder, and only names `saveGame_<n>` up to
the highest number there (docs/harness/06-dev-loop-and-fixtures/implementation-notes/fixture-load-bug.md). The slot name the game
uses comes from the `saveSlot` value inside `<slot>_descr.sav`, not from the file name. So an install copies the files under the
next free name and rewrites `saveSlot` in the copied descriptor.

Safety rules, enforced here:
- An install writes only new files. It refuses when any target file exists.
- Each install is written to a ledger with the SHA-256 of every file it wrote.
- An uninstall deletes only ledger files whose hash still matches. A changed or missing file is reported, never deleted.
"""

from __future__ import annotations

import json
import os
import re
import struct
import time
from dataclasses import dataclass
from pathlib import Path

import psutil

from .environment import sha256_of_file
from .runfolder import WaitLock
from .shared import SHARED_RUNS

LEDGER_PATH = SHARED_RUNS / ".installed-slots.json"  # one ledger for all worktrees: they share the save folder
SLOT_NAME = re.compile(r"^saveGame_(\d+)(?:_descr\.sav|\.sav|\.png|_coat_\d+\.png)$")
REQUIRED_SUFFIXES = (".sav", "_descr.sav")
DESCRIPTOR_SUFFIX = "_descr.sav"
STR_PROPERTY = b"StrProperty\x00"


SAVES_LOCK_TIMEOUT_S = 180  # a guarded save holds the lock for its whole save (spec 24), which can take a minute


def saves_lock(ledger_path: Path | None = None) -> WaitLock:
    """The lock for every change to the user's save folder and the ledger. Parallel runs (spec 11) share both."""
    return WaitLock((ledger_path or LEDGER_PATH).with_name(".saves.lock"), timeout_s=SAVES_LOCK_TIMEOUT_S)


def _this_process() -> dict:
    return {"owner_pid": os.getpid(), "owner_started": psutil.Process().create_time()}


def has_live_owner(entry: dict) -> bool:
    """True if another run that is still alive owns the entry. An old entry without an owner counts as left over."""
    pid = entry.get("owner_pid")
    if pid is None or pid == os.getpid():
        return False
    try:
        return psutil.Process(pid).create_time() == entry.get("owner_started")  # the start time rules out a reused pid
    except psutil.Error:
        return False


def harness_file_names(save_dir: Path, ledger_path: Path | None = None) -> set[str]:
    """Names of the files that the ledger lists for `save_dir`: saves of the harness, not of the user."""
    return {name for entry in read_ledger(ledger_path) if Path(entry["save_dir"]) == Path(save_dir) for name in entry["files"]}


class SlotError(RuntimeError):
    """An install or uninstall could not be done safely. The message says why."""


# ---- the descriptor ----

def _fstring(text: str) -> bytes:
    """An Unreal FString: int32 length with the null, then the ASCII text and a null."""
    raw = text.encode("ascii") + b"\x00"
    return struct.pack("<i", len(raw)) + raw


def rewrite_str_property(data: bytes, name: str, value: str) -> bytes:
    """Replace the value of the one tagged StrProperty `name` in a saved object, and fix its size field.

    Layout seen in `_descr.sav` (game 0.8.111): FString name, FString "StrProperty", 4 zero bytes, int32 size (4 + value length),
    one byte, FString value. The file has no total size field, so the value may change its length.
    """
    tag = _fstring(name) + _fstring(STR_PROPERTY[:-1].decode("ascii"))
    first = data.find(tag)
    if first < 0 or data.find(tag, first + 1) >= 0:
        raise SlotError(f"the descriptor must hold exactly one StrProperty {name!r}")
    size_at = first + len(tag) + 4
    (size,) = struct.unpack_from("<i", data, size_at)
    value_at = size_at + 4 + 1
    (length,) = struct.unpack_from("<i", data, value_at)
    if size != 4 + length or length < 1 or data[value_at + 4 + length - 1] != 0:
        raise SlotError(f"unexpected layout of StrProperty {name!r} (size {size}, length {length})")
    new_value = _fstring(value)
    return (data[:size_at] + struct.pack("<i", len(new_value)) + data[size_at + 4:value_at]
            + new_value + data[value_at + 4 + length:])


def read_str_property(data: bytes, name: str) -> str:
    tag = _fstring(name) + _fstring(STR_PROPERTY[:-1].decode("ascii"))
    first = data.find(tag)
    if first < 0:
        raise SlotError(f"the descriptor has no StrProperty {name!r}")
    value_at = first + len(tag) + 4 + 4 + 1
    (length,) = struct.unpack_from("<i", data, value_at)
    return data[value_at + 4:value_at + 4 + length - 1].decode("ascii")


# ---- slot names ----

def next_free_slot(save_dir: Path) -> str:
    """`saveGame_<max+1>`. The load screen lists numbers only up to the highest slot, so a higher gap is not used."""
    numbers = [int(m[1]) for p in save_dir.iterdir() if (m := SLOT_NAME.match(p.name))] if save_dir.is_dir() else []
    return f"saveGame_{max(numbers, default=-1) + 1}"


# ---- the ledger ----

def read_ledger(path: Path | None = None) -> list[dict]:
    path = path or LEDGER_PATH  # looked up at call time, so tests can point it to a temp file
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _write_ledger(entries: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# ---- install and uninstall ----

@dataclass(frozen=True)
class Installed:
    slot: str
    label: str
    files: dict  # file name -> SHA-256 of the written file
    save_dir: str

    def as_dict(self) -> dict:
        return {"slot": self.slot, "label": self.label, "files": self.files, "save_dir": self.save_dir,
                "installed": int(time.time()), **_this_process()}


def install(save_dir: Path, sources: dict[str, Path], label: str, ledger_path: Path | None = None) -> Installed:
    """Copy the slot files `sources` (suffix -> path) into `save_dir` under the next free slot name."""
    ledger_path = ledger_path or LEDGER_PATH
    for needed in REQUIRED_SUFFIXES:
        if needed not in sources:
            raise SlotError(f"the save has no file for {needed}")
    slot = next_free_slot(save_dir)
    targets = {suffix: save_dir / f"{slot}{suffix}" for suffix in sources}
    existing = [path.name for path in targets.values() if path.exists()]
    if existing:
        raise SlotError(f"refused to install: these files exist already: {existing}")
    contents = {suffix: path.read_bytes() for suffix, path in sources.items()}
    descriptor = rewrite_str_property(contents[DESCRIPTOR_SUFFIX], "saveSlot", slot)
    contents[DESCRIPTOR_SUFFIX] = rewrite_str_property(descriptor, "saveName", f"harness {label}")
    written: dict[str, str] = {}
    entries = read_ledger(ledger_path)
    record = Installed(slot, label, written, str(save_dir))
    entries.append(record.as_dict())
    _write_ledger(entries, ledger_path)  # first: an install that stops half way can still be removed
    for suffix, target in targets.items():
        with open(target, "xb") as handle:  # "x": never overwrite
            handle.write(contents[suffix])
        written[target.name] = sha256_of_file(target)
        entries[-1]["files"] = dict(written)
        _write_ledger(entries, ledger_path)
    return Installed(slot, label, dict(written), str(save_dir))


def uninstall(record: dict) -> dict:
    """Delete the files of one ledger record whose hash still matches. Return what was removed and what was kept."""
    save_dir = Path(record["save_dir"])
    removed, kept = [], []
    for name, digest in record["files"].items():
        path = save_dir / name
        if not path.exists():
            kept.append(f"{name} (missing)")
        elif sha256_of_file(path) != digest:
            kept.append(f"{name} (changed, not deleted)")
        else:
            path.unlink()
            removed.append(name)
    return {"slot": record["slot"], "removed": removed, "kept": kept}


def uninstall_slot(slot: str, ledger_path: Path | None = None) -> dict:
    """Uninstall one slot of the ledger and drop it from the ledger."""
    ledger_path = ledger_path or LEDGER_PATH
    entries = read_ledger(ledger_path)
    matches = [entry for entry in entries if entry["slot"] == slot]
    if not matches:
        raise SlotError(f"slot {slot!r} is not in the ledger {ledger_path}")
    result = uninstall(matches[0])
    _write_ledger([entry for entry in entries if entry is not matches[0]], ledger_path)
    return result


def uninstall_all(save_dir: Path, ledger_path: Path | None = None) -> list[dict]:
    """Uninstall every ledger slot of `save_dir` (for example copies left by a --keep-open run). Other entries stay.

    Entries of another run that is still alive stay too: it runs in another game slot at the same time (spec 11).
    """
    ledger_path = ledger_path or LEDGER_PATH
    entries = read_ledger(ledger_path)
    mine = [entry for entry in entries if Path(entry["save_dir"]) == Path(save_dir) and not has_live_owner(entry)]
    if not mine:
        return []
    results = [uninstall(entry) for entry in mine]
    _write_ledger([entry for entry in entries if entry not in mine], ledger_path)
    return results


def record_saved(save_dir: Path, slot: str, label: str, files: dict, ledger_path: Path | None = None) -> None:
    """Put files that the game wrote (a harness save, spec 24) into the ledger, so the run end or the next run deletes them."""
    ledger_path = ledger_path or LEDGER_PATH
    entries = read_ledger(ledger_path)
    entries.append(Installed(slot, label, dict(files), str(save_dir)).as_dict())
    _write_ledger(entries, ledger_path)
