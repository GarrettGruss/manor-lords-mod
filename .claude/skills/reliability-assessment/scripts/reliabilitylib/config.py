"""Load and check the config file. There are no built-in defaults: every constant comes from the file."""
import json
from pathlib import Path


class ConfigError(Exception):
    pass


# Key path -> expected type. A key under an optional section is only required when the section exists.
REQUIRED = {
    "domains": list,
    "ignore": list,
    "commit_types.pattern": str,
    "commit_types.feat": list,
    "commit_types.fix": list,
    "cfr.window_days": (int, float),
    "low_sample_n": int,
    "thresholds.cfr": (int, float),
    "thresholds.flaky": (int, float),
    "thresholds.min_samples": int,
    "thresholds.unmapped_churn": (int, float),
    "report_dir": str,
}
RUNS_REQUIRED = {
    "runs.glob": str,
    "runs.fields.time": str,
    "runs.fields.test": str,
    "runs.fields.verdict": str,
    "runs.fields.commit": str,
    "runs.pass": list,
    "runs.fail": list,
    "runs.test_files.globs": list,
    "runs.test_files.name_pattern": str,
    "runs.test_files.stem_replace": list,
}


def load_config(path: Path) -> dict:
    try:
        config = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"config file not found: {path}")
    except json.JSONDecodeError as error:
        raise ConfigError(f"config file is not valid JSON: {path}: {error}")
    check_config(config)
    return config


def check_config(config: dict) -> None:
    for key, expected in REQUIRED.items():
        _check_key(config, key, expected)
    if "runs" in config:
        for key, expected in RUNS_REQUIRED.items():
            _check_key(config, key, expected)
    if "capabilities_dir" in config and not isinstance(config["capabilities_dir"], str):
        raise ConfigError("config key 'capabilities_dir' must be a string")
    for index, entry in enumerate(config["domains"]):
        if not isinstance(entry, dict) or not isinstance(entry.get("glob"), str) or not isinstance(entry.get("domain"), str):
            raise ConfigError(f"config key 'domains[{index}]' must have the strings 'glob' and 'domain'")


def _check_key(config: dict, key: str, expected) -> None:
    value = config
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ConfigError(f"config key '{key}' is missing")
        value = value[part]
    # bool is a subclass of int, but a bool is never a valid number here.
    if isinstance(value, bool) or not isinstance(value, expected):
        raise ConfigError(f"config key '{key}' has the wrong type: {type(value).__name__}")
