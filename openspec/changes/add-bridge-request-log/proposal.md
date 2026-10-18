# Proposal: Add bridge request log

Issue: #270. Legacy source: `docs/harness/01-ue4ss-bridge/README.md` (plan step 5, "Hardening and harness integration").

## Why
Spec 01 plans "log each request (id, verb, target, duration) to HarnessLog for the run record". The backfill found that the code does not do it (`openspec/changes/archive/2026-10-18-backfill-living-specs/notes/h1-report.md`). The bridge Lua mod only prints, and `UE4SS.log` is buffered. After a failed run an agent cannot see which bridge calls ran.

## What Changes
- The bridge Lua mod writes one `HarnessLog` line per request.
- A fake game test checks the line for a read, a failure and an eval request.
- The other plan items of step 5 are done or dropped: atomic writes, unique ids and timeouts are built; "wipe `bridge\` at launch" is replaced by a fresh bridge folder in each run folder (see `harness/ue4ss-bridge`).

## Non-goals
- A request log of the MCP server (Python side).
- HTTP mode of the MCP server (the code is stdio only).
- Rate limits in the bridge.

## Legacy folders
`docs/harness/01-ue4ss-bridge/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `harness/ue4ss-bridge`: a new requirement for the request log.

## Impact
`mod/UEBridge/scripts/main.lua` is vendored code with marked patches. Add the change as a patch `P<n>` in `vendor/ue4ss-bridge/PATCHES.md`. The log must not slow the request loop (one line per request).
