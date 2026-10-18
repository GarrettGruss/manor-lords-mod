"""Turn metrics into JSON and Markdown, and find the domains over a limit."""
from statistics import median


def sampled(value, n: int, low_sample_n: int) -> dict:
    """Every reported value carries its sample count."""
    return {"value": value, "n": n, "low_sample": n < low_sample_n}


def git_report(changes: dict, lifetimes: dict, unmapped_share, unknown: dict, config: dict) -> dict:
    low = config["low_sample_n"]
    domains = {}
    for domain, entry in sorted(changes.items()):
        life = lifetimes.get(domain, {"lifetimes_days": [], "no_origin": 0})
        days = life["lifetimes_days"]
        domains[domain] = {
            "feat": entry["feat"],
            "fix": entry["fix"],
            "churn": entry["churn"],
            "fix_feat_ratio": sampled(entry["fix_feat_ratio"], entry["feat"], low),
            "cfr": sampled(entry["cfr"], entry["feat"], low),
            "bug_lifetime_days": sampled(median(days) if days else None, len(days), low),
            "no_origin": life["no_origin"],
            "fix_commits": entry["fix_commits"],
        }
    return {"window_days": config["cfr"]["window_days"], "unmapped_churn_share": unmapped_share,
            "unknown_domains": unknown, "domains": domains}


def runs_report(metrics: dict, skipped: list[str], config: dict) -> dict:
    low = config["low_sample_n"]
    domains = {}
    for domain, entry in sorted(metrics["domains"].items()):
        domains[domain] = {
            "tests": entry["tests"], "runs": entry["runs"], "other": entry["other"],
            "failures": entry["failures"], "flaky": entry["flaky"], "no_commit": entry["no_commit"],
            "flaky_rate": sampled(entry["flaky_rate"], entry["runs"], low),
            "mttf_hours": sampled(entry["mttf_hours"], len(entry["up_hours"]), low),
            "mttr_hours": sampled(entry["mttr_hours"], len(entry["repair_hours"]), low),
        }
    tests = {
        test: {key: entry[key] for key in ("domain", "runs", "failures", "flaky", "mttf_hours", "mttr_hours")}
        for test, entry in metrics["tests"].items()
    }
    return {"skipped": skipped, "domains": domains, "tests": tests}


def over_limits(git: dict, runs: dict | None, config: dict) -> list[str]:
    limits = config["thresholds"]
    flags = []
    for domain, entry in git["domains"].items():
        cfr = entry["cfr"]
        if cfr["value"] is not None and cfr["n"] >= limits["min_samples"] and cfr["value"] > limits["cfr"]:
            flags.append(f"{domain}: change failure rate {cfr['value']:.2f} > {limits['cfr']} (n={cfr['n']})")
    for domain, entry in (runs or {}).get("domains", {}).items():
        flaky = entry["flaky_rate"]
        if flaky["value"] is not None and flaky["n"] >= limits["min_samples"] and flaky["value"] > limits["flaky"]:
            flags.append(f"{domain}: flaky rate {flaky['value']:.2f} > {limits['flaky']} (n={flaky['n']})")
    share = git["unmapped_churn_share"]
    if share is not None and share > limits["unmapped_churn"]:
        flags.append(f"unmapped churn share {share:.2f} > {limits['unmapped_churn']}: extend the domain map")
    return flags


def fmt(cell: dict, digits: int = 2) -> str:
    if cell["value"] is None:
        return f"- (n={cell['n']})"
    mark = " low sample" if cell["low_sample"] else ""
    return f"{cell['value']:.{digits}f} (n={cell['n']}{mark})"


def git_markdown(report: dict) -> str:
    lines = [
        f"## Git history (window {report['window_days']} days)", "",
        "| Domain | feat | fix | fix:feat | CFR | Bug lifetime (days) | no origin | churn |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for domain, e in report["domains"].items():
        lines.append(f"| {domain} | {e['feat']} | {e['fix']} | {fmt(e['fix_feat_ratio'])} | {fmt(e['cfr'])} "
                     f"| {fmt(e['bug_lifetime_days'], 1)} | {e['no_origin']} | {e['churn']} |")
    share = report["unmapped_churn_share"]
    lines += ["", f"Unmapped churn share: {'-' if share is None else f'{share:.2f}'}"]
    if report["unknown_domains"]:
        lines.append("Domains with no capability folder: " + ", ".join(sorted(report["unknown_domains"])))
    return "\n".join(lines)


def runs_markdown(report: dict) -> str:
    lines = [
        "## Test runs", "",
        "| Domain | tests | runs | real failures | flaky | flaky rate | MTTF (h) | MTTR (h) | other |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for domain, e in report["domains"].items():
        lines.append(f"| {domain} | {e['tests']} | {e['runs']} | {e['failures']} | {e['flaky']} | {fmt(e['flaky_rate'])} "
                     f"| {fmt(e['mttf_hours'], 1)} | {fmt(e['mttr_hours'], 1)} | {e['other']} |")
    if report["skipped"]:
        lines += ["", "Skipped files:"] + [f"- {item}" for item in report["skipped"]]
    return "\n".join(lines)


def assess_markdown(date: str, flags: list[str], git: dict, runs: dict | None) -> str:
    parts = [f"# Reliability assessment {date}", "", "## Over a limit", ""]
    parts += [f"- {flag}" for flag in flags] or ["- none"]
    parts += ["", git_markdown(git)]
    if runs is not None:
        parts += ["", runs_markdown(runs)]
    return "\n".join(parts) + "\n"
