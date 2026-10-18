"""Test helpers: a temporary git repository with fixed commit times, and a base config."""
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

DAY = 86400
T0 = 1_700_000_000

BASE_CONFIG = {
    "domains": [
        {"glob": "features/{name}/**", "domain": "mod/{name}"},
        {"glob": "core/**", "domain": "core"},
    ],
    "ignore": ["docs/**"],
    "commit_types": {"pattern": r"^(?P<type>\w+)(\([^)]*\))?!?:", "feat": ["feat"], "fix": ["fix"]},
    "cfr": {"window_days": 14},
    "low_sample_n": 3,
    "thresholds": {"cfr": 0.3, "flaky": 0.2, "min_samples": 5, "unmapped_churn": 0.15},
    "report_dir": "reports",
    "runs": {
        "glob": "runs/*/summary.json",
        "fields": {"time": "started", "test": "scenario", "verdict": "verdict", "commit": "git"},
        "pass": ["pass"],
        "fail": ["fail", "crash"],
        "test_files": {"globs": ["features/*/tests/*.py"], "name_pattern": r"^NAME = \"([^\"]+)\"", "stem_replace": ["_", "-"]},
    },
}


def config(**changes) -> dict:
    result = copy.deepcopy(BASE_CONFIG)
    result.update(changes)
    return result


class TempRepo:
    def __init__(self):
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.git("config", "core.autocrlf", "false")

    def cleanup(self):
        self._dir.cleanup()

    def git(self, *args, time=None):
        env = dict(os.environ)
        if time is not None:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"@{int(time)} +0000"
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True, env=env)

    def write(self, path: str, text: str):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")

    def commit(self, subject: str, files: dict[str, str], day: float):
        for path, text in files.items():
            self.write(path, text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", subject, time=T0 + day * DAY)

    def run(self, run_id: str, scenario: str, verdict: str, hour: float, commit: str | None = "abc"):
        data = {"scenario": scenario, "verdict": verdict, "started": T0 + hour * 3600}
        if commit:
            data["git"] = commit
        self.write(f"runs/{run_id}/summary.json", json.dumps(data))
