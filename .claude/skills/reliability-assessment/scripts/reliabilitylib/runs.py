"""Read test run results and compute MTTF, MTTR and flaky failures per test and per domain."""
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median

from .domains import DomainMap, UNMAPPED

HOUR_S = 3600.0
PASS, FAIL, OTHER = "pass", "fail", "other"


@dataclass
class Run:
    test: str
    time: float
    outcome: str
    commit: str | None
    flaky: bool = False


def parse_time(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()


def load_runs(repo: Path, config: dict) -> tuple[list[Run], list[str]]:
    """All runs sorted by time, and the paths of files that could not be read."""
    runs_config = config["runs"]
    fields = runs_config["fields"]
    runs, skipped = [], []
    for path in sorted(Path(repo).glob(runs_config["glob"])):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            runs.append(Run(
                test=str(data[fields["test"]]),
                time=parse_time(data[fields["time"]]),
                outcome=_outcome(data.get(fields["verdict"]), runs_config),
                commit=data.get(fields["commit"]) or None,
            ))
        except (OSError, ValueError, KeyError, TypeError) as error:
            skipped.append(f"{path}: {type(error).__name__}: {error}")
    runs.sort(key=lambda run: run.time)
    return runs, skipped


def _outcome(verdict, runs_config: dict) -> str:
    if verdict in runs_config["pass"]:
        return PASS
    if verdict in runs_config["fail"]:
        return FAIL
    return OTHER


def test_paths(repo: Path, config: dict) -> dict[str, str]:
    """Test name -> repository-relative file path, from the name pattern in each file or from the file name."""
    files_config = config["runs"]["test_files"]
    pattern = re.compile(files_config["name_pattern"], re.MULTILINE)
    old, new = files_config["stem_replace"]
    names = {}
    for glob in files_config["globs"]:
        for path in sorted(Path(repo).glob(glob)):
            match = pattern.search(path.read_text(encoding="utf-8", errors="replace"))
            name = match.group(1) if match else path.stem.replace(old, new)
            names[name] = path.relative_to(repo).as_posix()
    return names


def mark_flaky(runs: list[Run]) -> None:
    """A failure is flaky when the next counted run of the same test is a pass on the same commit."""
    by_test: dict[str, list[Run]] = {}
    for run in runs:
        if run.outcome != OTHER:
            by_test.setdefault(run.test, []).append(run)
    for timeline in by_test.values():
        for current, following in zip(timeline, timeline[1:]):
            if current.outcome == FAIL and following.outcome == PASS and current.commit and current.commit == following.commit:
                current.flaky = True


def failure_intervals(timeline: list[Run]) -> tuple[list[float], list[float]]:
    """Up times (first pass of a streak to the next real failure) and repair times (first real failure to the next pass), in hours."""
    up, repair = [], []
    streak_start, streak_outcome = None, None
    for run in timeline:
        if run.outcome == OTHER or run.flaky:
            continue
        if run.outcome == streak_outcome:
            continue
        if streak_start is not None:
            (up if streak_outcome == PASS else repair).append((run.time - streak_start) / HOUR_S)
        streak_start, streak_outcome = run.time, run.outcome
    return up, repair


def run_metrics(runs: list[Run], domain_of_test) -> dict[str, dict]:
    """Metrics per test, each with its domain, plus a summary per domain."""
    mark_flaky(runs)
    tests: dict[str, dict] = {}
    for test in sorted({run.test for run in runs}):
        timeline = [run for run in runs if run.test == test]
        tests[test] = _test_entry(timeline, domain_of_test(test))
    domains: dict[str, dict] = {}
    for test, entry in tests.items():
        _add_to_domain(domains.setdefault(entry["domain"], _empty_domain()), entry)
    for entry in domains.values():
        _finish_domain(entry)
    return {"tests": tests, "domains": domains}


def _test_entry(timeline: list[Run], domain: str) -> dict:
    up, repair = failure_intervals(timeline)
    counted = [run for run in timeline if run.outcome != OTHER]
    return {
        "domain": domain,
        "runs": len(counted),
        "other": len(timeline) - len(counted),
        "failures": sum(1 for run in counted if run.outcome == FAIL and not run.flaky),
        "flaky": sum(1 for run in counted if run.flaky),
        "no_commit": sum(1 for run in counted if run.outcome == FAIL and not run.commit),
        "up_hours": up,
        "repair_hours": repair,
        "mttf_hours": median(up) if up else None,
        "mttr_hours": median(repair) if repair else None,
    }


def _empty_domain() -> dict:
    return {"tests": 0, "runs": 0, "other": 0, "failures": 0, "flaky": 0, "no_commit": 0, "up_hours": [], "repair_hours": []}


def _add_to_domain(domain: dict, test: dict) -> None:
    domain["tests"] += 1
    for key in ("runs", "other", "failures", "flaky", "no_commit", "up_hours", "repair_hours"):
        domain[key] += test[key]


def _finish_domain(domain: dict) -> None:
    domain["mttf_hours"] = median(domain["up_hours"]) if domain["up_hours"] else None
    domain["mttr_hours"] = median(domain["repair_hours"]) if domain["repair_hours"] else None
    domain["flaky_rate"] = domain["flaky"] / domain["runs"] if domain["runs"] else None


def domain_lookup(repo: Path, config: dict, domain_map: DomainMap):
    paths = test_paths(repo, config)

    def domain_of_test(test: str) -> str:
        path = paths.get(test)
        return (domain_map.domain_of(path) or UNMAPPED) if path else UNMAPPED

    return domain_of_test
