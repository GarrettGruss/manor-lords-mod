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

## Start race found in the real test
- What happened: two quick `run_scenario` calls both started a launcher. The tool only read `runs/.lock`, and `run.py` takes that lock later.
  One launcher lost the lock and failed with "Run lock ... is held by process N". The tool reported `failed_to_start` for it.
- Fix: `run_scenario` now claims a start slot before it starts a process. The claim is the file `runs/.active-launcher.json`,
  created with exclusive create (mode `x`). It holds `run_id`, `pid` and `started`. The launcher pid is written right after `Popen` (`.tmp` + `os.replace`).
- A second call is refused at once with an error that names the active run id. A stale claim is replaced once.
  A claim is live while its launcher pid is alive, or, before the pid is known, for 10 s. If `Popen` fails, the claim is removed.
- `run.py` is not changed, so it does not release the claim. A dead launcher pid is the release rule.
- `game_status` shows `active_run_id`. `stop_game` refuses while a live claim exists.
- Tests added: second call refused, stale claim replaced, live claim refuses, `Popen` failure releases the claim, status and stop, two threads (one starts).

## Real check with the game (2026-10-10)
Ran the tool functions with the real game from this worktree (not a Claude Code session):
- `run_scenario("time-advance")` returned in 0.07 s with `status: started`.
- A second `run_scenario` call at once was refused: "A launcher is already starting or running (run ...). Use wait_for_run ...". The race is fixed.
- `wait_for_run` reported `running` with the phase (`boot`, then `scenario`) and then the finished summary after 55 s (summary 1.3 KB).
- `list_screenshots` listed `screenshots/start.png` and `screenshots/end.png`. `read_log` returned the tail of `mod.log`. `game_status` showed no game and no lock after the run.
- The default run cap shown by the tool was 20 and is now 100, like `run.py`.

Still not checked: a real Claude Code session that lists and calls the tools (needs a new session so that `.mcp.json` is loaded), and a run that survives the MCP server closing.

## Check in a real Claude Code session (2026-10-10)
A fresh headless Claude Code session (`claude -p`, version 2.1.296, model Sonnet) was started in the repo with
`--mcp-config .mcp.json --strict-mcp-config` and only the read-only tools allowed:
`mcp__manor-harness__list_scenarios`, `game_status` and `list_runs`.

Result: the `manor-harness` server started from `.mcp.json` (stdio, `PYTHONPATH=mcp;harness` worked on Windows), the session found and
called all three tools, and the answers were correct (the scenario list, "game not running, no lock, 72 of 100 runs used",
and the 3 newest runs with their verdicts and durations). So the registration, the permissions (read-only tools allowed) and the
server work in a real client.

Two defects were found and fixed:
- `list_scenarios` showed no descriptions. It read the function docstring. It now uses the registry summary.
- `list_scenarios` listed the hidden test scenarios (selftest-*, probe-actions). They are now hidden, and `run_scenario` refuses them
  as unknown. Three tests cover this (`test_harness_tools_scenarios.py`).

Not checked: `run_scenario` and `stop_game` in a real client (they ask for permission, so a headless session cannot approve them),
and a client time limit for long calls (the start and poll design avoids long calls).

## `run_scenario` in a real client (2026-10-10)
A second headless session was asked to start `smoke` with `run_scenario`, then `wait_for_run` and `read_summary`, with those three tools
passed in `--allowedTools`. `run_scenario` was refused ("permission has not been granted"): `.claude/settings.json` puts `run_scenario`
in `ask`, and a headless session has nobody who can approve it. This is the intended permission design (the tool starts the game),
so it was not bypassed. The start and poll flow itself was checked with a real run through the tool functions (see above).
To try it in an interactive Claude Code session, approve the `run_scenario` prompt once. To allow it for unattended work, move
`mcp__manor-harness__run_scenario` from `ask` to `allow` in `.claude/settings.json`. That is the user's decision.
