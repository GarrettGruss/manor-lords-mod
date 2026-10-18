"""Find the commits that a fix repairs: the last edits of the lines that the fix removes or changes."""
import re
from dataclasses import dataclass
from pathlib import Path

from .domains import DomainMap
from .gitlog import DAY_S, Commit, git

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+")


@dataclass(frozen=True)
class Origin:
    domain: str
    sha: str
    time: float


def old_line_ranges(repo: Path, fix: Commit) -> dict[str, list[tuple[int, int]]]:
    """Old file path -> (start, count) ranges that the fix removes or changes."""
    diff = git(repo, "diff", "-U0", "--no-renames", f"{fix.sha}^", fix.sha)
    ranges: dict[str, list[tuple[int, int]]] = {}
    path = None
    in_header = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            in_header, path = True, None
            continue
        # A removed line such as "-- comment" looks like a header line, so headers are read only before the first hunk.
        if in_header and line.startswith("--- "):
            path = None if line == "--- /dev/null" else line[6:]
        if line.startswith("@@"):
            in_header = False
        hunk = HUNK.match(line)
        if hunk and path:
            count = 1 if hunk.group(2) is None else int(hunk.group(2))
            if count:
                ranges.setdefault(path, []).append((int(hunk.group(1)), count))
    return ranges


def blame_origins(repo: Path, fix: Commit, domain_map: DomainMap) -> list[Origin]:
    """One origin per (domain, commit). Ignored files give none. A fix with no parent gives none."""
    try:
        ranges = old_line_ranges(repo, fix)
    except RuntimeError:
        return []
    origins = set()
    for path, spans in ranges.items():
        domain = domain_map.domain_of(path)
        if domain is None:
            continue
        args = [arg for start, count in spans for arg in ("-L", f"{start},+{count}")]
        porcelain = git(repo, "blame", "--porcelain", *args, f"{fix.sha}^", "--", path)
        origins |= {Origin(domain, sha, time) for sha, time in _porcelain_commits(porcelain)}
    return sorted(origins, key=lambda origin: origin.time)


def _porcelain_commits(porcelain: str) -> list[tuple[str, float]]:
    """(sha, author time) pairs. The time follows the first header line of each commit."""
    commits, sha = [], None
    for line in porcelain.splitlines():
        parts = line.split()
        if len(parts) >= 3 and len(parts[0]) == 40 and all(c in "0123456789abcdef" for c in parts[0]):
            sha = parts[0]
        elif line.startswith("author-time ") and sha:
            commits.append((sha, float(parts[1])))
    return commits


def origins_by_fix(repo: Path, commits: list[Commit], config: dict, domain_map: DomainMap) -> dict[str, list[Origin]]:
    fix_types = set(config["commit_types"]["fix"])
    return {commit.sha: blame_origins(repo, commit, domain_map) for commit in commits if commit.type in fix_types}


def lifetimes_by_domain(commits: list[Commit], origins: dict[str, list[Origin]]) -> dict[str, dict]:
    """Bug lifetime per fix and domain: from the newest origin in that domain to the fix."""
    result: dict[str, dict] = {}
    for commit in commits:
        if commit.sha not in origins:
            continue
        newest: dict[str, float] = {}
        for origin in origins[commit.sha]:
            newest[origin.domain] = max(newest.get(origin.domain, 0.0), origin.time)
        for domain in commit.domains:
            entry = result.setdefault(domain, {"lifetimes_days": [], "no_origin": 0})
            if domain in newest:
                entry["lifetimes_days"].append((commit.time - newest[domain]) / DAY_S)
            else:
                entry["no_origin"] += 1
    return result
