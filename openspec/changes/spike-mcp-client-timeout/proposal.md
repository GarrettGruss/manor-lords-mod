# Proposal: Spike MCP client timeout

Issue: #282. Legacy source: `openspec/changes/archive/2026-10-15-legacy-05-agent-tools/README.md` ("Open questions") and `openspec/changes/archive/2026-10-15-legacy-05-agent-tools/implementation-notes/build-notes.md`.

## Why
The `manor-harness` tools use start and poll. `wait_for_run` waits up to 45 s per call (hard cap 50 s). The value 45 s is a guess. The real timeout of the Claude Code MCP client was never measured. If the client times out earlier, every `wait_for_run` call fails. The legacy note says: "Lower the default if the client times out."

## What Changes
- Measure the client timeout with a test tool call of known length.
- Keep 45 s if it is safe. Otherwise change the default and the hard cap in the tool code.

## Non-goals
- New tools.
- A long blocking call (the design already avoids it).

## Legacy folders
`openspec/changes/archive/2026-10-15-legacy-05-agent-tools/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None now. A changed default changes the requirement on `wait_for_run` in `harness/agent-tools` in the implementation pull request.

## Impact
Needs a real Claude Code session with `.mcp.json` loaded. It does not need the game (a fake wait works).
