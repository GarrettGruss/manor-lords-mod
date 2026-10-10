# Smoke test log

Date: 2026-10-09. Game build: UE 5.5.4. UEBridge 1.2.1 with patches P1 to P7. Map: `Jagged_Cliffs`.
Tests were run with the CLI and the Python `one()` helper, not through Claude Code MCP tools.

## Results

| Test | Result | Notes |
|---|---|---|
| UEBridge loads | pass | `UE4SS.log`: `v1.2.1 ready (protocol 3 ...) eval=false writes=true`. |
| 1. `hello` | pass | Bridge folder `ue4ss\bridge` was created. `allow_eval` is false. |
| 2. Inspect objects | pass | `world` and `objects` returned live objects, for example `RTSMultiEngineCPP` (`RTSGameManager`) and 5 `PawnCPP`. |
| 3. Read a property | pass, value unclear | `silver`, `influence` and `kingsFavour` on the player pawn all read `0`. This may be correct for this game state. It is not checked. |
| 3. Write a property | not run | A write changes the user's game. Needs the user's approval. |
| 4. Call a UFunction | FAIL: game crash | See below. |
| 5. Hot reload | not run | |
| 6. Kill mid-request | not run | |

## Crash during test 4

I called `getGameSpeed` on the player pawn through `one("call", ...)`.
I used the field name `fname`. The bridge expects `function`. The Lua code then did `obj[nil]`.

Stack (top frames): `Lua::get_string()` ->
`UObjectBase::prepare_to_handle()` -> UObject `__index` metamethod -> Lua `pcall`.
Error: `EXCEPTION_ACCESS_VIOLATION reading address 0x0`.
Report: `%LOCALAPPDATA%\ManorLords\Saved\Crashes\UECC-Windows-AD5B93D24DFBF871C32FBBA910794D2C_0000`.

Cause: UE4SS reads a null string pointer when a UObject is indexed with a nil key.
The upstream bridge passes the name through without a check. A mistake by a caller can crash the game.
The MCP tool schema would have required `function`. I bypassed the schema.

Fix: patch P8. `get`, `set` and `call` now refuse a name that is not a non-empty string.

## Findings for the harness
- A crash is a result. The server reported it well: "the game crashed during this call", the request in flight, and the crash report path.
- Any code that indexes a UObject with an untrusted key must check the type first. This applies to our own mods too.
- Call the bridge through the MCP tools, not through `one()`, so the tool schemas protect us.
- `lastop.log` held the last request (`batch[1] call`). It helped to find the failing call.

## Next
- Redeploy with P8. Relaunch the game. Repeat test 4 with the correct field name.
- Ask the user before test 3 (write) and before any test that changes game state.
