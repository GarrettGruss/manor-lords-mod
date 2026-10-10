# Spec 01: ue4ss-bridge live control channel

Status: draft (nothing installed yet). Roadmap phase: 2 (live control channel).

## Goal
Give the agent an on-demand, structured way to query and drive the running
Manor Lords process (inspect objects, read/write properties, call UFunctions,
hot reload Lua) without editing a mod and restarting the game for each question.

## Non-goals
- Not the run orchestrator (launch, kill, summary.json). That is a later spec.
- Not telemetry sampling. That is a mod-side feature that writes via HarnessLog.
- Not multiplayer or remote access. Localhost, single-player only.

## Background
ue4ss-bridge (github.com/littleRabbit94/ue-bridge, `pip`/`uvx ue4ss-bridge`) has
two halves:
1. A Lua mod in `ue4ss\Mods\` polls `ue4ss\bridge\request.json` every ~50 ms,
   executes the request on the game thread, and writes `response.json`.
2. A Python MCP server (stdio, or HTTP on `127.0.0.1:8930`) exposes tools:
   inspect objects, set properties, call UFunctions, eval Lua, streams,
   snapshots, hot reload.

It has not been verified on Manor Lords. Everything below is conditional on the
security review (see `review-checklist.md`) passing.

## Environment facts (verified on this machine)
- UE4SS: experimental build `v3.0.1-1164-g5e627997`, new layout.
- Install root: `...\Manor Lords\ManorLords\Binaries\Win64\` holds `dwmapi.dll`
  and `ue4ss\` (`UE4SS.dll`, `UE4SS-settings.ini`, `Mods\`).
- Engine: UE 5.5.4 (from the jmap filename).
- Lua `require` of shared modules works as `shared\<Name>\<Name>.lua`.
- `UE4SS.log` is not live; use HarnessLog (`ue4ss\harness\mod.log`) for streaming.
- Deploy path: `harness\deploy.ps1` copies `mod\` into `ue4ss\Mods\`.

## Plan

### Step 1: Isolated review (no game install)
- Fetch the package source into a scratch directory (not the game dir, not the repo).
  Run any Python on it with `-I`.
- Review every Lua and Python file against `review-checklist.md`.
- Output: `docs/specs/01-ue4ss-bridge/implementation-notes/review-report.md` with verdict
  (approve / approve with patches / reject) and a list of required patches.
- Gate: no unresolved High findings.

### Step 2: Vendor and patch
- Copy the reviewed Lua mod into `mod/UEBridge/` and the MCP server into `mcp/ue4ss_bridge/`.
  The folder must be named `UEBridge`. The pinned upstream commit is in `vendor/ue4ss-bridge/VERSION`.
- Apply the required patches. Each one is marked `PATCH P<n> (harness)` in the code and listed in
  `vendor/ue4ss-bridge/PATCHES.md`.
- Adapt paths for the new layout (`ue4ss\bridge\`), and make the bridge
  directory configurable via `HARNESS_RUN_DIR` when set, so each run has its
  own request/response files.
- Set `allow_eval = false` by default; enabling it requires an explicit,
  local, uncommitted override.
- Deploy with `harness\deploy.ps1`, which also enables it in `mods.txt`.

### Step 3: MCP server setup
- Create `.venv`, install the pinned MCP server package version.
- Run HTTP bound to `127.0.0.1` only (never `0.0.0.0`), or stdio.
- Register in project `.mcp.json`. Do not auto-approve eval tools.

### Step 4: Smoke tests (game running, a save loaded)
1. `ue4ss-bridge hello` returns a response.
2. Inspect a known object (e.g. the GameInstance or world).
3. Read one property, set it, read it back, confirm the change is visible in game.
4. Call one harmless UFunction.
5. Edit a Lua file, hot reload, confirm new behaviour.
6. Kill the game mid-request; confirm the client times out cleanly and the
   next launch starts with wiped bridge folders.
- Gate: all six pass, and each failure mode returns a structured error.

### Step 5: Hardening and harness integration
- Wipe `bridge\` at launch (done by the run launcher, planned spec 03).
- Verify atomic writes (`.tmp` then rename), unique request IDs, per-request timeouts.
- Rate and iteration limits are enforced by the orchestrator, not the bridge.
- Log each request (id, verb, target, duration) to HarnessLog for the run record.
- Document the tool list and limits in `harness/README.md`.

## Design rules (carried over)
- UObjects only on the game thread; the bridge must queue to it.
- Localhost only, single-player only.
- Responses are bounded in size; large dumps go to files, not responses.
- Bridge failures are results, never harness crashes.

## Open questions
- Does the bridge assume the old `Mods\` layout or `xinput`-style paths?
- Does `ExecuteInGameThread` queueing happen per request or per poll, and what
  happens when the game is paused or at the main menu (no ticking world)?
- Which verbs exist for calling UFunctions with struct/array parameters?
- What are the MCP server's Python version and dependency pins?
- Does hot reload interact with `EnableAutoReloadingLuaMods` (currently 0)?

## Acceptance criteria
- Review report exists and is approved.
- The agent can, via MCP only, read a live property, change it, and call a
  UFunction, with timeouts and error results behaving as specified.
- A fresh clone plus `deploy.ps1` plus documented setup reproduces the install.
