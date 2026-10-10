# Spec 05: Agent tools (MCP server for the harness)

Status: draft. Roadmap phase: 7 (see `docs/specs/00-harness-overview/README.md`).

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

| Tool | What it does | Result size |
|---|---|---|
| `list_scenarios` | names and descriptions from `harness/scenarios/` | small |
| `run_scenario(name, fixture=None)` | starts `harness/run.py` as a subprocess, waits up to the scenario limit plus 5 min, returns the one-line result and the summary | under 4 KB |
| `read_summary(run_id="latest")` | returns `summary.json` | under 4 KB |
| `list_runs(limit=10)` | run id, verdict, scenario, duration, for the newest runs | small |
| `read_log(run_id, name, tail=100)` | the last lines of `mod.log`, `UE4SS.log`, or `boot.json` of a run (a fixed list of names, no free paths) | capped at 20 KB |
| `read_telemetry(run_id, last=20)` | the last samples of `telemetry.jsonl` | capped |
| `list_screenshots(run_id)` | paths of the screenshots of a run (the agent opens them with the file tools) | small |
| `game_status` | is the game running, which run holds the lock, how many runs are left under the cap | small |
| `stop_game` | stops a stray game process (the same code as the preflight in spec 03) | small |

Rules:
- `run_scenario` takes the run lock. A second call while a run is active returns an error at once, not a wait.
- Run folders are found only under `runs/`. The tools reject ids and names that contain path parts (`..`, slashes).
- `read_log` and `read_telemetry` return text as data. A log can hold game text. The server never treats it as instructions.
- Timeouts everywhere. A run that exceeds its limit returns a `timeout` result, and the server kills the subprocess tree.
- The tools do not start the game in other ways, and do not write outside `runs/`.

Permissions (`.claude/settings.json`):
- Read-only tools (`list_scenarios`, `read_summary`, `list_runs`, `read_log`, `read_telemetry`, `list_screenshots`, `game_status`): `allow`.
- `run_scenario` and `stop_game`: `ask` by default, because they start or kill the game. The user can move them to `allow` for unattended work.
  The iteration cap in spec 03 limits the cost of an unattended loop.

## Plan
1. Write the server with the tool functions as plain Python (testable without MCP). Unit tests with fake run folders.
2. Wrap them as MCP tools. Test the server over stdio with a small MCP client in the tests.
3. Register in `.mcp.json` and `.claude/settings.json`. Check in Claude Code that the tools list. (Needs a session restart or `/mcp`: record what was verified.)
4. Run one scenario through the tool in a real session.
5. Write `harness/README.md` usage and update the roadmap.

## Open questions
- Does Claude Code accept an MCP call that runs for 3 minutes? Is there a client timeout? If it is short, `run_scenario` must start the run and return at once, and the agent polls with `read_summary`.
- How should an agent open screenshots? The file tools can read PNG files, so only paths are needed.

## Acceptance criteria
- All tools have unit tests, including path rejection and the lock behaviour.
- A stdio client test lists the tools and calls `list_scenarios` and `read_summary`.
- One real scenario is started and read back through the tools, and the game is not running afterwards.
- No tool returns more than 20 KB.
