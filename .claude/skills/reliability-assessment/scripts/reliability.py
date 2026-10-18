"""Reliability metrics per domain.

Usage:
  reliability.py git    [--config FILE] [--repo DIR] [--rev REV] [--json FILE]
  reliability.py runs   [--config FILE] [--repo DIR] [--json FILE]
  reliability.py assess [--config FILE] [--repo DIR] [--rev REV] [--date YYYY-MM-DD]
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reliabilitylib import blame, gitlog, report, runs  # noqa: E402
from reliabilitylib.config import ConfigError, load_config  # noqa: E402
from reliabilitylib.domains import DomainMap  # noqa: E402

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "reliability.json"


def build_git_report(repo: Path, rev: str, config: dict) -> dict:
    domain_map = DomainMap(config, repo)
    commits = gitlog.read_commits(repo, rev, config, domain_map)
    origins = blame.origins_by_fix(repo, commits, config, domain_map)
    changes = gitlog.change_metrics(commits, origins, config)
    lifetimes = blame.lifetimes_by_domain(commits, origins)
    return report.git_report(changes, lifetimes, gitlog.unmapped_share(commits), domain_map.unknown, config)


def build_runs_report(repo: Path, config: dict) -> dict | None:
    if "runs" not in config:
        return None
    domain_map = DomainMap(config, repo)
    loaded, skipped = runs.load_runs(repo, config)
    metrics = runs.run_metrics(loaded, runs.domain_lookup(repo, config, domain_map))
    return report.runs_report(metrics, skipped, config)


def write_json(path: str | None, data) -> None:
    if path:
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_assessment(repo: Path, config: dict, day: str, git: dict, run_report: dict | None) -> Path:
    flags = report.over_limits(git, run_report, config)
    out_dir = repo / config["report_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    data = {"date": day, "over_limits": flags, "git": git, "runs": run_report}
    _write_atomic(out_dir / f"{day}.json", json.dumps(data, indent=2))
    markdown_path = out_dir / f"{day}.md"
    _write_atomic(markdown_path, report.assess_markdown(day, flags, git, run_report))
    return markdown_path


def _write_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reliability metrics per domain.")
    parser.add_argument("command", choices=["git", "runs", "assess"])
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--repo", default=".")
    parser.add_argument("--rev", default="HEAD")
    parser.add_argument("--json", help="also write the report as JSON to this file")
    parser.add_argument("--date", default=date.today().isoformat())
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    try:
        config = load_config(Path(args.config))
        if args.command == "git":
            data = build_git_report(repo, args.rev, config)
            print(report.git_markdown(data))
        elif args.command == "runs":
            data = build_runs_report(repo, config)
            if data is None:
                raise ConfigError("the config has no 'runs' section, so there is no run report")
            print(report.runs_markdown(data))
        else:
            data = None
            path = write_assessment(repo, config, args.date, build_git_report(repo, args.rev, config), build_runs_report(repo, config))
            print(path.read_text(encoding="utf-8"))
        write_json(args.json, data)
    except ConfigError as error:
        print(f"config error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
