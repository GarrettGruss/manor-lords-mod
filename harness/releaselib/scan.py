"""Scan a release zip (spec 19): no harness-only module and no AES key."""

from __future__ import annotations

import zipfile
from pathlib import Path

from .files import HARNESS_ONLY, hard_requires

MIN_KEY_CHARS = 16  # a shorter text is not a key. It would match by chance.


def read_key(key_file: Path) -> str:
    """The key text from the file. Never print the result."""
    if not key_file.is_file():
        raise FileNotFoundError(f"AES key file not found: {key_file}")
    key = key_file.read_text(encoding="utf-8").strip()
    if len(key) < MIN_KEY_CHARS:
        raise ValueError(f"{key_file} does not hold a key (too short)")
    return key


def _key_forms(key: str) -> list[bytes]:
    """The key as text, as UTF-8 and as UTF-16, in the case it has and in lower and upper case."""
    forms: list[bytes] = []
    for variant in {key, key.lower(), key.upper(), key.removeprefix("0x"), key.removeprefix("0x").lower()}:
        forms += [variant.encode("utf-8"), variant.encode("utf-16-le")]
    return forms


def scan_bytes(name: str, data: bytes, key: str) -> list[str]:
    """The problems for one file: the key text in it. The key is not part of the message."""
    return [f"the AES key text is in {name}"] if any(form in data for form in _key_forms(key)) else []


def scan_zip(zip_path: Path, key: str | None) -> list[str]:
    """Return the list of problems. An empty list means the zip is clean. The key is never part of a message."""
    problems: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            parts = info.filename.split("/")
            stem = {part.removesuffix(".lua") for part in parts}
            for module in sorted(stem & HARNESS_ONLY):
                problems.append(f"harness-only module {module} is in the zip: {info.filename}")
            data = archive.read(info)
            if key:
                problems += scan_bytes(info.filename, data, key)
            if info.filename.endswith(".lua"):
                needs = hard_requires(data.decode("utf-8", errors="replace")) & HARNESS_ONLY
                for module in sorted(needs):
                    problems.append(f"{info.filename} requires the harness-only module {module}")
    return problems
