"""Read one version section from a Keep a Changelog file (spec 19)."""

from __future__ import annotations

import re
from pathlib import Path

HEADING = re.compile(r"^##\s+\[?([^\]\s]+)\]?(?:\s+-\s+(.*))?\s*$")


class ChangelogError(Exception):
    """The changelog has no usable section for the version."""


def section_for(text: str, version: str) -> str | None:
    """The body of the section `## [version] - date`, or None. The body is not empty."""
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if match and match.group(1) == version:
            start = index + 1
            break
    if start is None:
        return None
    body = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    text_body = "\n".join(body).strip()
    return text_body or None


def release_notes(changelog: Path, version: str) -> str:
    """The notes for a release. Raise ChangelogError when the file or the section is missing."""
    if not changelog.is_file():
        raise ChangelogError(f"{changelog} does not exist. Add a Keep a Changelog file.")
    notes = section_for(changelog.read_text(encoding="utf-8"), version)
    if notes is None:
        raise ChangelogError(f"{changelog} has no section '## [{version}] - <date>' with content. Add one before the release.")
    return notes
