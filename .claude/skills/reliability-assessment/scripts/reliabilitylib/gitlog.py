"""Read commits from git and compute counts, churn and change failure rate per domain."""
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .domains import DomainMap, UNMAPPED

DAY_S = 86400.0


@dataclass
class Commit:
    sha: str
    time: float
    subject: str
    type: str | None = None
    churn: dict[str, int] = field(default_factory=dict)  # domain -> lines added plus removed

    @property
    def domains(self) -> set[str]:
        return set(self.churn)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def read_commits(repo: Path, rev: str, config: dict, domain_map: DomainMap) -> list[Commit]:
    """Non-merge commits of `rev`, oldest first. Ignored paths add no churn and no domain."""
    raw = git(repo, "log", "--no-merges", "--no-renames", "--numstat", "--format=%x00%H%x1f%at%x1f%s", rev)
    pattern = re.compile(config["commit_types"]["pattern"])
    commits = []
    for block in raw.split("\x00")[1:]:
        header, _, body = block.partition("\n")
        sha, time, subject = header.split("\x1f", 2)
        match = pattern.match(subject)
        commit = Commit(sha, float(time), subject, match.group("type") if match else None)
        for line in body.splitlines():
            _add_numstat_line(commit, line, domain_map)
        commits.append(commit)
    commits.reverse()
    return commits


def _add_numstat_line(commit: Commit, line: str, domain_map: DomainMap) -> None:
    parts = line.split("\t")
    if len(parts) != 3:
        return
    added, removed, path = parts
    domain = domain_map.domain_of(path)
    if domain is None:
        return
    # Binary files show "-" for both counts.
    lines = (int(added) if added.isdigit() else 0) + (int(removed) if removed.isdigit() else 0)
    commit.churn[domain] = commit.churn.get(domain, 0) + lines


def failed_feats(commits: list[Commit], origins: dict, window_s: float) -> set[tuple[str, str]]:
    """(domain, feat sha) pairs whose lines a later fix changed in that domain within the window."""
    times = {commit.sha: commit.time for commit in commits}
    failed = set()
    for fix_sha, fix_origins in origins.items():
        for origin in fix_origins:
            if origin.sha in times and times[fix_sha] - origin.time <= window_s:
                failed.add((origin.domain, origin.sha))
    return failed


def change_metrics(commits: list[Commit], origins: dict, config: dict) -> dict[str, dict]:
    """`origins` maps a fix sha to the commits it repairs (see blame.py)."""
    feat_types = set(config["commit_types"]["feat"])
    fix_types = set(config["commit_types"]["fix"])
    failed = failed_feats(commits, origins, config["cfr"]["window_days"] * DAY_S)
    stats: dict[str, dict] = {}
    for commit in commits:
        for domain in commit.domains:
            entry = stats.setdefault(domain, {"feat": [], "fix": [], "churn": 0})
            entry["churn"] += commit.churn[domain]
            if commit.type in feat_types:
                entry["feat"].append(commit)
            elif commit.type in fix_types:
                entry["fix"].append(commit)
    return {domain: _summarize(domain, entry, failed) for domain, entry in stats.items()}


def _summarize(domain: str, entry: dict, failed_pairs: set) -> dict:
    feats, fixes = entry["feat"], entry["fix"]
    failed = sum(1 for feat in feats if (domain, feat.sha) in failed_pairs)
    return {
        "feat": len(feats),
        "fix": len(fixes),
        "fix_feat_ratio": len(fixes) / len(feats) if feats else None,
        "churn": entry["churn"],
        "cfr": failed / len(feats) if feats else None,
        "cfr_failed": failed,
        "fix_commits": [f"{fix.sha[:10]} {fix.subject}" for fix in fixes],
    }


def unmapped_share(commits: list[Commit]) -> float | None:
    total = sum(sum(commit.churn.values()) for commit in commits)
    unmapped = sum(commit.churn.get(UNMAPPED, 0) for commit in commits)
    return unmapped / total if total else None
