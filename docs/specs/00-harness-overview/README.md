# Spec 00: Harness overview and roadmap

Status: draft. This spec holds the plan for all other specs. Update it when a spec is finished or changes.

## Purpose
Let an AI agent develop and test Manor Lords mods in a loop, with no human in the loop:
edit the mod, deploy it, run the game, read the result, and repeat.

**Main objective:** the agent changes a mod and, within about 2 to 3 minutes, gets a trustworthy result (pass, fail or crash) with evidence.

## What "90% of testing" means
For each mod feature:
1. The spec states its acceptance criteria as measurable game state (ranges, not exact values).
2. At least one scenario checks each criterion, and the agent can run it alone.
3. The agent reads `summary.json` and decides what to do next. It opens logs and screenshots only if needed.

A criterion counts as "automated" when a scenario checks it. The target is that **at least 90% of the acceptance criteria of each feature are automated**.
The remaining criteria are for the human: how the feature looks and feels, balance, and the final review of a pull request.
Each feature spec lists which criteria are automated and which are human.

## Test layers (fast to slow)

| Layer | What it checks | Speed | Status |
|---|---|---|---|
| 0. Syntax | Lua files compile (`harness/tests/lua_syntax.py`) | seconds | built |
| 1. Mock tests | mod logic against a fake game API (`harness/tests/boot_state_machine.py`) | seconds | built for HarnessBoot. A reusable kit is planned (spec 06) |
| 2. Live probe | read, set and call things in a running game through the bridge | seconds per query | built (specs 01 and 02) |
| 3. Scenario run | cold start, load save, run a scenario, collect results, stop the game | 1 to 2 min | spec 03, in progress |
| 4. Regression suite | many scenarios and saves, compared with baseline ranges | minutes to hours | spec 08 |
| 5. Human | look and feel, balance, final review | n/a | stays with the user |

An agent uses the fastest layer that can answer its question. It moves to a slower layer only when it must.

## Roadmap

| Spec | Name | Goal | Status |
|---|---|---|---|
| 01 | ue4ss-bridge | Live control channel into the running game | done (PR 1) |
| 02 | save-autoload | Load a fixed save and report ready, with the game paused | done (PR 2). Open: save copy, dialog test |
| 03 | run-launcher | One command makes one run folder with `summary.json` | in progress |
| 04 | telemetry-and-assertions | Sample game state, assert ranges, define the scenario format, control game time | planned |
| 05 | agent-tools | MCP tools so the agent drives the harness directly | planned |
| 06 | dev-loop-and-fixtures | Hot reload without a game restart, a reusable mock kit, several test saves | planned |
| 07 | feature-test-kit | Helpers to give resources, place buildings, trigger events, advance time | planned |
| 08 | regression-suite | Run many scenarios and saves, compare with baselines, find flaky tests | planned |
| 09 | asset-mods | Pak editing and repacking for changes that Lua cannot reach | only if a feature needs it |

Order and reasons:
- 03 comes first: every later spec needs a run folder and a summary.
- 04 next: without telemetry and assertions a run cannot say pass or fail for a feature.
- 05 can start after 03 and 04 work by hand. It is the step that lets the agent work without the user starting commands.
- 06 and 07 are the main work for the 90% goal. 06 makes iteration fast. 07 lets a scenario create the situation that a feature needs.
- 08 comes when there are enough scenarios to protect against regressions.

### Gate for each spec
A spec is done when its acceptance criteria are met and the notes in `implementation-notes/` record the evidence.
Then update the status here and in the changelog.

## Feature workflow (what an agent does for a new mod feature)
1. Write or update the feature spec in `docs/specs/<NN>-<name>/` with acceptance criteria as measurable game state. Mark each criterion automated or human.
2. Check what the game exposes: search the jmap, and probe through the bridge. Record the names in `implementation-notes/`.
3. Write the mod code. Test the logic at layer 1 (mock), with a syntax check at layer 0.
4. Try it live at layer 2: deploy, reload, and query the running game.
5. Write the scenario for each automated criterion. Run it at layer 3. Read `summary.json`.
6. Fix and repeat. Run the scenario several times to see if it is flaky.
7. Run the regression suite (layer 4) before the pull request.
8. In the pull request: show the summary evidence, list the human criteria, and note what was not verified.

## Principles
- Assert ranges, not exact values. The simulation is not deterministic.
- A crash is a result with logs. It is not a harness failure.
- Each run uses its own folder. No state is shared between runs.
- The summary comes first. Logs and screenshots are for follow-up.
- Every wait has a time limit. A run that hangs is a timeout result.
- Repeat runs to measure flakiness (as the 10-launch series did). Do not trust one pass.
- The harness never writes to the user's saves. Saves are copied or read only.
- Safety rails stay on: an iteration cap, a run lock, and the uninstall script (`harness/uninstall.ps1`) as a kill switch.
- Keep a run short (under 3 minutes) so the loop stays fast.
- Record findings in the spec's `implementation-notes/`. A finding that changes a decision updates the spec in the same commit.

## What is verified today (see the specs for evidence)
- The bridge reads and writes game state and calls functions (spec 01). Some limits: no object-reference or out parameters, and a nil name once crashed the game (fixed by patch P8).
- A cold start loads `saveGame_0` and reaches a paused game in 42 to 44 s, 10 of 10 runs (spec 02).
- The game does not close on request. The harness stops it with a kill.
- The game restarts its clock once after our first pause. The harness holds the pause (spec 02).
- A direct launch of the game executable passes environment variables, so each run can have its own folder (spec 03).
- Game state is readable: calendar, region approval, public order, wealth, food, population, player silver, letters (`InBox`).

## Main risks and unknowns

| Risk | Effect | Plan |
|---|---|---|
| Core simulation logic is not reflected (only state and some functions are) | Some features can only be checked through their effects | Write criteria as state ranges. Use hooks on reflected functions where they exist |
| Actions that need UI clicks (placing a building, for example) may have no callable function | The kit (spec 07) cannot create some situations | Search the jmap for the function behind each UI action. Fall back to save fixtures that already contain the situation |
| A game update changes hooks or names | Scenarios break | Pin the game build. Record the build in each summary. Disable auto-update |
| Screenshots may not show the game when it is behind another window | Visual checks fail | Test `mss` in spec 03. Keep the game window in front during runs |
| The game restarts its clock after a load, and the cause is unknown | The pause can fail in a new case | Hold the pause and check the clock. Find the cause later (optional) |
| Steam must be running for a direct launch | A run fails to start | Spec 03 checks it in `preflight` and fails with a clear message |
| Agent cost grows with many runs | Budget | Use the fastest layer, cap iterations, use Sonnet for agent work (see `CLAUDE.md`) |

## Open decisions
- Which features will be built first? The scenarios in spec 04 and the kit in spec 07 should fit them.
- Which test saves are needed (famine, raid, trade, many buildings)? Who creates them, and how are they stored without writing to the user's saves?
- Should a nightly regression run be started by a scheduled task? This needs an unlocked desktop session.
- Is a second machine or user account for the game worth it, so the harness does not take over the user's screen?

## Acceptance criteria
- Each spec in the roadmap exists, and its status here matches its real state.
- For every feature spec, at least 90% of the criteria are marked automated, or the reason is written down.
- A new agent can follow the "Feature workflow" with no help from the user, using the harness commands and tools.
