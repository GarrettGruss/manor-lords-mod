# Spec 05: Agent tools (MCP server for the harness)

Status: done. Code, 46 tests, a real run through the tool functions, and a check in a real Claude Code session (list_scenarios, game_status and list_runs through `.mcp.json`) are done. Roadmap phase: 7 (see `docs/harness/00-harness-overview/README.md`).

## Goal
An agent drives the harness through MCP tools. It runs a scenario, reads the summary, and reads logs, without shell commands.
The tools are small, return short results, and have safe limits.

## Non-goals
- Replacing the bridge MCP server (spec 01). That server stays for live probing.
- New harness features. The tools call what specs 03 and 04 provide.

## Background
- `python harness/run.py --scenario <name>` runs one iteration and writes `runs/<id>/summary.json` (spec 03).
- The bridge MCP server (`.mcp.json`, server `ue4ss-bridge`) already exists. Its risky tools ask first (`.claude/settings.json`).
- The MCP library is pinned in `mcp/requirements.txt` (`mcp==1.30.0`), installed in `.venv`.
- A run takes 1 to 3 minutes. An MCP call must not hang for that long without a limit.

## Design
A new stdio MCP server `mcp/harness_tools/` (server name `manor-harness`), registered in `.mcp.json`.

A run takes 1 to 3 minutes and a client may time out on a long MCP call. So the tools use start and poll.
`run_scenario` returns at once. The agent calls `wait_for_run` until it gets the summary.

| Tool | What it does | Result size |
|---|---|---|
| `list_scenarios` | names and descriptions from the scenario registry (`runlib/scenario.py`) | small |
| `run_scenario(name)` | starts `harness/run.py --scenario <name> --run-id <id>` as a detached background process. Returns `{"status": "started", "run_id": ...}` at once | small |
| `wait_for_run(run_id, seconds=45)` | waits up to `seconds` (hard cap 50) for `summary.json`. Returns the summary, or `{"status": "running", "phase": ..., "elapsed_s": ...}` | under 4 KB |
| `read_summary(run_id="latest")` | returns `summary.json` | under 4 KB |
| `list_runs(limit=10)` | run id, verdict, scenario, duration, for the newest runs | small |
| `read_log(run_id, name, tail=100)` | the last lines of `mod.log`, `UE4SS.log`, `boot.json`, `scenario.log`, `scenario.json`, `launcher.log` or `config.json` (a fixed list of names, no free paths) | capped at 20 KB |
| `read_telemetry(run_id, last=20)` | the last samples of `telemetry.jsonl`. A clear error if the file is missing | capped |
| `list_screenshots(run_id)` | paths of the screenshots of a run, relative to the run folder (the agent opens them with the file tools) | small |
| `game_status` | is the game running, which run holds the lock, how many runs are left under the cap | small |
| `stop_game` | stops a stray game process (`runlib.game.stop_processes`). Refuses while a run holds the lock | small |

Rules:
- `run_scenario` refuses with an error result, at once, if a live process holds `runs/.lock` or the scenario name is unknown.
  The lock itself is taken by `run.py` in the background process. The tool only reads it. If `run.py` refuses, `wait_for_run` returns `failed_to_start` with the launcher log.
- The background process writes its output to `runs/.launcher-<run_id>.log` (the run folder does not exist yet at start). `read_log` reads it as `launcher.log`.
  On Windows it starts in a new process group with no console window.
- Run folders are found only under `runs/`. Run ids and names must match `[A-Za-z0-9_-]{1,64}`, so `..`, slashes and drive letters are rejected. Every path is resolved and checked to be inside `runs/`.
- `read_log` and `read_telemetry` return text as data, inside a JSON field. A log can hold game text. The server never treats it as instructions.
- Every result is under 20 KB. A cut is marked (`truncated`).
- The run time limits are owned by `run.py` (spec 03). The tools never wait longer than 50 s in one call.
- The tools do not start the game in other ways, and do not write outside `runs/`.
- `phase` in the running result is a hint from the files in the run folder. The launcher writes no live phase file.

Permissions (`.claude/settings.json`):
- Read-only tools (`list_scenarios`, `read_summary`, `list_runs`, `read_log`, `read_telemetry`, `list_screenshots`, `game_status`): `allow`.
- `run_scenario` and `stop_game`: `ask` by default, because they start or kill the game. The user can move them to `allow` for unattended work.
  The iteration cap in spec 03 limits the cost of an unattended loop.

## Plan
1. Write the server with the tool functions as plain Python (testable without MCP). Unit tests with fake run folders. Done.
2. Wrap them as MCP tools. Test the server over stdio with a small MCP client in the tests. Done.
3. Register in `.mcp.json` and `.claude/settings.json`. Check in Claude Code that the tools list. (Needs a session restart or `/mcp`: record what was verified.)
4. Run one scenario through the tool in a real session.
5. Write `harness/README.md` usage and update the roadmap.

## Open questions
- Does Claude Code accept an MCP call that runs for 3 minutes? Not tested. Decision: do not depend on it. Use start and poll, and keep every call under 50 s.
  Still to check: the real client timeout, and whether 45 s per `wait_for_run` call is safe.
- How should an agent open screenshots? The file tools can read PNG files, so only paths are needed.
- Do the tools list in a real Claude Code session, and does a real run work through `run_scenario`? Not checked yet (see `implementation-notes/build-notes.md`).

## Acceptance criteria
- All tools have unit tests, including path rejection and the lock behaviour.
- A stdio client test lists the tools and calls `list_scenarios` and `read_summary`.
- One real scenario is started and read back through the tools, and the game is not running afterwards.
- No tool returns more than 20 KB.
