# Where a run records its test scenario

Checked 2026-10-18 (task 1.1).

- `runs/<id>/summary.json` and `config.json` hold only the scenario name (`"scenario": "noop"`), not the file path.
- The name comes from `NAME = "..."` in the scenario file, or from the module name with `_` replaced by `-` (`harness/runlib/scenario.py`, `_register_module`).
- Scenario files: `harness/scenarios/*.py` and `mod/*/scenarios/**/*.py`.

Decision: the config gets `runs.test_files` (`globs`, `name_pattern`, `stem_replace`). The script scans those files to map a name to a path, and the path goes through the domain map. A run of a deleted test scenario is `unmapped`.
