# Build notes: agent tools (spec 05)

## What was built
- `mcp/harness_tools/tools.py`: the tool functions as plain Python. They take `runs_root` and `repo_root`.
- `mcp/harness_tools/server.py` and `__main__.py`: a FastMCP stdio server `manor-harness`. One wrapper per tool. Read-only tools have `readOnlyHint`.
  `wait_for_run` is an async wrapper that waits in a thread, so the server stays responsive.
- `.mcp.json`: server entry with `PYTHONPATH=mcp;harness` (`harness` is needed for `runlib`).
- `.claude/settings.json`: eight read-only tools in `allow`. `run_scenario` and `stop_game` in `ask`. The `ue4ss-bridge` entries are unchanged.
- `harness/README.md`: section "Agent tools". `CHANGELOG.md`: one entry.

## Decisions
- Start and poll, because a client may time out on a long call. `run_scenario` starts `harness/run.py` detached
  (new process group, no console window on Windows) and returns the run id. Output goes to `runs/.launcher-<id>.log`.
- `run_scenario` only reads the lock. `run.py` takes it. A tiny gap exists between the check and the lock. If two starts race,
  `run.py` itself refuses the second one, and `wait_for_run` reports `failed_to_start` with the launcher log.
- The registry in `runlib/scenario.py` is imported in-process. If the import fails, the list is empty.
- `phase` in a running result is a guess from `config.json`, `boot.json`, `ready.marker` and `scenario.json`. The launcher writes no live phase file.
- Results are dicts with `ok`. Errors are `{"ok": false, "error": ...}`, not MCP protocol errors.
- `max_runs` for `game_status` comes from the newest `config.json`, else 20 (the `run.py` default).
- Run ids and names: `[A-Za-z0-9_-]{1,64}`. This also blocks hidden names such as `.lock`.

## Tests
- `harness/tests/test_harness_tools_tools.py` (35 tests, 1 may skip if symlinks are not allowed) and `test_harness_tools_mcp.py` (1 test).
- Run: `.venv\Scripts\python.exe -m unittest discover -s harness/tests -p "test_harness_tools*.py"`.
- Covered: each tool on temp run folders; bad ids, names, paths and a symlink out of `runs/`; lock refusal (live and stale lock);
  size caps; start and poll with a stub launcher (returns in under 0.9 s, the process is alive, the summary appears later);
  failed start; `stop_game` refusal; a stdio client that lists the 10 tools, checks read-only hints, and calls `list_scenarios`, `read_summary` and a rejected id.
- Result: 36 tests, 35 pass, 1 skipped. The skipped one is the symlink test: this machine does not allow symlinks without privilege, so that case is not verified.
- The existing `test_runlib*.py` suite ran in the worktree: one failure, `StalePreflightTest.test_missing_save_fails`. The cause is that the worktree has no `.venv`, so
  preflight fails on "venv not found" before the save check. It is not caused by this change.
- Python prints a `ResourceWarning` about the detached subprocess in the tests. It is expected: the server never waits for the launcher.

## NOT verified
- A real Claude Code session that lists the tools, and permissions that behave as set in `.claude/settings.json`.
- A real run through `run_scenario` with the real `run.py` and the game. Only a stub launcher was used.
- The client timeout of a long MCP call. 45 s per `wait_for_run` is a guess. Lower the default if the client times out.
- Behaviour of the detached process when Claude Code closes the server in the middle of a run. A run should continue (new process group), but this is not tested.
- `.mcp.json` `PYTHONPATH` with `;` as separator was not tested through Claude Code. The stdio test used the same two paths.
