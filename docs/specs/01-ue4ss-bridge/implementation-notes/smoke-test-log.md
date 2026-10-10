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

## Run 2 (after patch P8)

Same game build. A new game session, same map. The pawn path changes in each session, so read it with `world` first.

| Test | Result | Notes |
|---|---|---|
| 4. Call a UFunction | pass | `getGameSpeed` on the player pawn returned `1`. |
| 4b. Call with a wrong argument count | pass (clean error) | `getGameSpeedID` returned `UFunction expected 1 parameters, received 0`. The function has an out parameter. `call_function` cannot pass out parameters (review finding L7). |
| 4c. Call a function that does not exist | pass (clean error) | `attempt to call a TrivialObject value`. See the finding below. |
| P8: call with no function name | pass | Error `call needs a non-empty string name, got nil`. The game did not crash. This is the input that crashed it in run 1. |
| P8: get with no name | pass | Error `get needs a non-empty string name, got nil`. |
| 5. Reload | pass | `reload` gave generation 2, and `hello` worked afterwards. The log shows a second `ready` line. This reloads UEBridge only, not other mods. |
| 3. Write a property | not run | Needs user approval. |
| 6. Kill the game mid-request | not run | Needs the user to agree to a forced game exit. |

## Findings from run 2
- `obj["noSuchFunction"]` does not return nil. It returns a `TrivialObject`. The upstream check `if fn == nil` in `UEB.call` never fires for a wrong name.
  The call still fails with a clear error and no crash. A better message is a possible later patch. It is not needed now.
- `reload` keeps the game running and the bridge answers again within about 2 seconds.
- The pawn path (`MyPawnCPP_BP3_C_<number>`) changes between sessions. Never store it. Look it up with `world` or `objects`.

## Run 2, remaining tests

| Test | Result | Notes |
|---|---|---|
| 3. Write a property | pass | Read `RTSMultiEngineCPP.gameSpeed` = 1. Set it to 2. The result showed `previous 1, current 2`. A read-back gave 2. `PawnCPP:getGameSpeed` also returned 2, so the change reached the pawn. Then I set it back to 1 and checked: 1 and 1. The restore ran in a `finally` block. |
| 6. Kill the game mid-request | pass | Sent `types` (a slow request that walks all objects). Killed the game 0.25 s later with `taskkill /F`. |

### Test 6 details
- The in-flight request returned an error after 15.08 s, which is the client timeout. The message was:
  `the game crashed during this call (the process is gone). in flight: batch[1] types. no crash report was written; the process may have been closed instead.`
  The message names the request and says why. It does not hang.
- A new request (`hello`) after the kill also failed after 15.08 s: `request never picked up: the game is not running.`
- Only `lastop.log` was left in `ue4ss\bridge\`. The client removed its own `request.json`.
- The server could not tell a forced exit from a crash. It said "crashed or closed" in the same message. The harness must check the process state itself.

### Findings
- The client waits the full timeout (15 s) even when the game process is already gone. The harness should check that the process is alive before it sends a request, and use short timeouts.
- After a kill, the next game launch still has to clear `ue4ss\bridge\`. A leftover `request.json` from a dead game could run in the new game. The server treats a request older than 10 s as stale, but the launcher must also wipe the folder (spec 03).
- The `class_name` field is required for `objects`. A wrong field name gives a clean error here, not a crash.

## Status of the six smoke tests
All six pass: hello, inspect, read/write, call a function, reload, kill mid-request.
Not yet checked: that Claude Code loads `.mcp.json` and lists the MCP tools, and the struct-argument case from the open questions.
The game is closed now (killed by test 6).
