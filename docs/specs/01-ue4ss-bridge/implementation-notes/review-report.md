# ue4ss-bridge review report

Date: 2026-10-09. Reviewer: Claude subagent. Method: read-only. Nothing was installed, imported or run.

## Verdict: APPROVE WITH PATCHES

No malicious code was found. The code does what it says. But the defaults are unsafe for our use
(eval and writes are ON), and a few gaps must be patched before we vendor it. All patches are small.

## What was reviewed

- Repo: github.com/littleRabbit94/ue-bridge (clone origin). pyproject says the source is `.../ue4ss-bridge` (same project, renamed).
- Git commit reviewed: `a5eae1cec9c6283a6259571140668ed118b2db8b` (HEAD, 2026-09-16, version 1.2.1, NOT on PyPI).
- Latest tag: v1.2.0 = commit `b7dd1450088d510e767fcd5276cc87980340acac`. Its code equals the PyPI sdist.
- PyPI: `ue4ss-bridge` has ONE release, 1.2.0. Wheel and sdist were both checked.
- Scratch dirs (outside repo and game): `scratchpad\ue-bridge-src` (git), `scratchpad\ue-bridge-pypi` (wheel, sdist, extracted copies).

### Git vs PyPI comparison
- sdist 1.2.0 `main.lua`, `json.lua`, `settings.lua`, `server.py`, `pyproject.toml` match git tag v1.2.0 (md5 equal, line endings ignored).
- The wheel holds only the Python package (no Lua mod). Wheel `server.py` equals the sdist copy.
- Git HEAD (1.2.1) vs wheel 1.2.0, Python: version string and docstring text only. No logic change.
- Git HEAD (1.2.1) vs 1.2.0, Lua: one fix. Property walks skip nil entries (`eachProperty`, main.lua:140). No new I/O, no new verbs.
- The Lua mod is NOT in the PyPI wheel. We must vendor the Lua from git (commit above).
- The wheel files use CRLF line endings; harmless.

### File list (git HEAD, 15 tracked files)
- `ue4ss/UEBridge/scripts/main.lua` (1341 lines) - the Lua mod
- `ue4ss/UEBridge/scripts/json.lua` (165) - pure Lua JSON, no I/O
- `ue4ss/UEBridge/scripts/settings.lua` (23) - settings
- `ue4ss/UEBridge/mod.toml` (14) - manifest (`schema = 1`, id `ue4ss-bridge`, order 400)
- `ue4ss_bridge/server.py` (809) - MCP server and CLI
- `ue4ss_bridge/__init__.py`, `__main__.py` (3 lines each)
- `tools/build-release.py` (101) - makes a release zip; not needed by us
- `stub/ue-bridge/pyproject.toml`, `stub/ue-bridge/README.md` - empty stub package that depends on `ue4ss-bridge>=1.2.0`
- `pyproject.toml`, `README.md`, `CHANGELOG.md`, `LICENSE`, `.gitignore`
- Git history once contained `__pycache__/*.pyc` files and the old `HFBridge`/`ue_bridge` names. They are gone at HEAD.

### Python and dependencies
- `requires-python >= 3.10`. Build backend: hatchling (build time only).
- Runtime dependency: `mcp>=1.8,<2` (one dependency, range not pinned to an exact version).
- Console scripts: `ue4ss-bridge` and `ue-bridge`, both `ue4ss_bridge.server:main`.
- No `setup.py`, no `.pth`, no post-install hooks. Pass.
- The `mcp` package and its transitive dependencies were NOT reviewed.

## Findings

### High
H1. Dangerous defaults. `allow_eval = true` and `allow_writes = true` (main.lua:52, settings.lua:15,20).
   With eval on, any request can run any Lua in the game process, including `os.execute` and `io.popen`
   (the eval env is `setmetatable({...}, {__index=_G})`, main.lua:1224-1233). Spec Step 2 requires default off. Patch P1.
H2. Eval is gated in the Lua mod only. The Python server always registers `eval_lua` (server.py:412-427)
   and has no flag of its own. Checklist C item "same server-side flag" FAILS. A hand-written
   request.json also skips the server. The Lua gate itself is sound (see trace below). Patch P2 plus a client deny rule.

Both are fixed by small patches. The gate "no unresolved High" is met once P1 and P2 are applied.

### Medium
M1. The bridge folder cannot follow `HARNESS_RUN_DIR`. Lua reads `bridge_dir` only from settings.lua (main.lua:82).
   Python reads `UE4SS_BRIDGE_DATA_DIR` (server.py:139,143). The two sides can disagree. Patch P1/P3.
M2. The mod folder name is hard coded: `Mods\UEBridge` (main.lua:37). The spec plan uses `mod/ue4ss-bridge/`.
   With another folder name, `require("json")` and `settings.lua` fail. Deploy the folder as `UEBridge`.
M3. Stuck poller. `busy = true` is set before `ExecuteInGameThread` (main.lua:1273, 1297). It is cleared
   only inside the callback, after an unprotected `respond(...)` (main.lua:1278-1280, 1302-1303). If the
   callback never runs (no ticking game thread) or `respond`/`json.encode` throws, `busy` stays true and
   every later request is ignored until restart. Patch P4.
M4. Late execution after a client timeout. Python gives up after 15 s (server.py:268-324), but the Lua side
   may still run the request later (for example `set`). The client sees an error, but the write may still happen.
   Callers must re-read state after a timeout.
M5. Responses are not size bounded. Structured ops are marked PREENCODED (main.lua:1151) and skip the
   200-item cap. `objects`, `types`, `events`, `subclasses` use a client `limit` with no maximum
   (main.lua:656, 668, 690, 1016). Strings are not cut. Python reads the whole file (server.py:298).
   Spec rule "responses bounded" is only partly met. Patch P5.
M6. `dump` is not gated by `allow_writes` (main.lua:1141, BATCH_OPS main.lua:1191). It writes files
   (usmap, jmap, headers, SDK) into the ue4ss folder. It can fill the disk and freeze the game for minutes. Patch P6.
M7. File IPC has no authentication. Any process of the same user that can write to the bridge folder can
   drive the game (and run Lua if eval is on). This is the same risk level as any code running as the user.
   Mitigation: eval off; per-run bridge dir; stdio only.

### Low
L1. README says "No background daemon or subprocess execution" (README, Security section). The Python server runs
   `powershell Get-CimInstance` (server.py:86) and `tasklist` (server.py:188). Arguments are fixed lists,
   no shell. The docs are wrong; the code is OK.
L2. A bad request JSON gets response id `"?"` (main.lua:1328). The Python client ignores it as stale
   (server.py:303-305) and waits for the timeout. Only matters for hand-written requests.
L3. Request pick-up is read then remove (main.lua:1323-1325). A second writer in that gap loses its
   request. The Python client guards with a 10 s "unconsumed" check (server.py:276-283). OK for one client.
L4. `writeAtomic` removes the target before the rename (main.lua:118-119). The client tolerates a missing or
   half-read file (server.py:296-301). Acceptable.
L5. Client-supplied Lua patterns (`list_types`, `inspect_object`, `list_subclasses`) run on the game
   thread (main.lua:347, 678, 718). A slow pattern can hang the game. Only syntax is validated (main.lua:335).
L6. `eval_lua` takes an agent-supplied `timeout` with no upper bound (server.py:413). `dump` uses 600 s.
L7. `call_function` cannot pass object, by-reference or out parameters (see Q3). JSON `null` in `args` is
   dropped, which shifts later arguments (`table.unpack` of a decoded list, main.lua:652; json.lua:137).
L8. Process discovery picks the first running UE exe with `ue4ss` beside it (server.py:155-160). With two
   UE games open it may pick the wrong one. Fix: always set `UE4SS_BRIDGE_GAME_DIR` or `UE4SS_BRIDGE_DATA_DIR`.
L9. Python reads crash reports from `%LOCALAPPDATA%\<Project>\Saved\Crashes` (server.py:224-247)
   and returns the ErrorMessage text to the agent. Read only.
L10. `mod.toml` (`schema = 1`, `[[lua]] source = "."`) is a mod-manager manifest. The release script leaves it
   out and uses `enabled.txt` (build-release.py header). Unknown if our UE4SS build reads it. Ignore it; use `mods.txt`.
L11. Provenance is thin: one author ("Rabbit", 34 commits, repo started 2026-09-02, one PyPI release,
   MIT). GitHub stars, issues and release history could NOT be read (the API call returned nothing). Treat as unknown.

## Checklist answers

### A. Provenance
- Owner, stars, issues, releases, license: PARTIAL. Owner littleRabbit94; MIT (LICENSE, "Copyright (c) 2026 Rabbit");
  tags v1.0.0, v1.1.0, v1.2.0; PyPI has only 1.2.0. Stars, issues, activity: UNKNOWN. Single author.
- Pin commit and compare PyPI to git: PASS. Commit `a5eae1cec9c6283a6259571140668ed118b2db8b`; sdist = tag v1.2.0;
  HEAD differs by one Lua fix and docstrings. The Python at HEAD is not on PyPI.
- Dependencies: PASS with note. One dependency, `mcp>=1.8,<2`, not exact. Pin it in a lock file.
- No install-time hooks: PASS (no setup.py, no .pth, hatchling only).

### B. Lua mod
- Dangerous functions: PASS with note. No `os.execute`, `io.popen` or `loadstring` in the mod code. `load` is used only in
  `runEval` (main.lua:1233, eval-gated). `loadfile` reads settings.lua (main.lua:55-56, a local file). `dofile(MOD_PATH)` is
  the reload (main.lua:1311, fixed path). `require` only loads `json` and `UEHelpers` (main.lua:41-42).
- Network use: PASS. No socket, HTTP or `ffi` use anywhere in `ue4ss/`.
- File access confined to the bridge dir: PASS for bridge I/O (paths listed below). Caveat: `bridge_dir` can point anywhere via
  settings.lua, and `dump` writes through UE4SS into the ue4ss folder.
- Atomic writes, tolerant readers: PASS (L4). Lua writes `response.tmp` then renames. Python writes `request.tmp` then `os.replace`.
- Unique IDs, echoed, stale ignored: PASS. `uuid4().hex[:12]` (server.py:285); echoed (main.lua:1247); stale ids skipped (server.py:303-305). See L2.
- `allow_eval=false` truly disables eval: PASS. Trace below.
- UObject access inside `ExecuteInGameThread`: PASS for batch and eval (main.lua:1275, 1299) and watch (main.lua:975).
  `ping` and `hello` do not touch UObjects.
- Bounded poll loop, handler errors cannot kill the poller: PARTIAL. `handle` is pcall-wrapped (main.lua:1331) and
  batch ops are pcall-fenced (main.lua:1211), but see M3.
- Response size bounds, no unbounded graph walks: PARTIAL. Depth 6 and 200 items (main.lua:127-128) for `encodeValue`;
  diff rows cap 500 (main.lua:482); event ring 2000 (main.lua:832). See M5. `types` and `subclasses` walk all UObjects (0.4-1.5 s per the docstrings).
- Behaviour when the world is nil: PASS by design, UNKNOWN in practice. Errors come back as results
  ("no live instance of ...", "no world to trace in", main.lua:315, 782). `world` returns partial data. Needs the smoke test at the main menu.

### C. Python MCP server
- Binds only 127.0.0.1 or stdio: PASS. `build_server(host="127.0.0.1")` (server.py:369) and `main` never passes a host (server.py:803).
  There is no `--host` option. No CORS settings. The default transport is stdio.
- Auth gaps / browser-to-localhost: PASS for stdio, RISK for `--http`. HTTP on 127.0.0.1:8930/mcp has no
  token. A web page could try to reach it (DNS rebinding). Protection depends on the `mcp` version (not verified). Use stdio.
- Input validation, paths constrained: PARTIAL. The agent gives no file paths. `dump.kind` is a whitelist
  (main.lua:1131-1143). Object refs go to `StaticFindObject`. Limits are not clamped (M5).
- Timeouts and clean errors: PASS. Every request has a timeout (default 15 s; 3 s hello; 30 s heavy ops; 60 s batch; 600 s dump)
  and returns a `BridgeError` text (server.py:308-324), with crash details when the process died (server.py:250).
- No telemetry or outbound calls: PASS for this package (only `powershell`, `tasklist` and local files). The `mcp` library was not reviewed.
- Eval gated by the same server flag: FAIL (H2). Only the Lua flag exists.

### D. Compatibility
- New `ue4ss\` layout: PASS. Paths come from `IterateGameDirectories()` Win64 + `\ue4ss` (main.lua:28-37); bridge at `ue4ss\bridge`.
  The mod folder must be named `UEBridge` (M2). README says it was verified on UE 5.5.4 (Dawnwalker). Manor Lords: UNVERIFIED.
- Bridge dir configurable: PARTIAL. Lua: `settings.lua` `bridge_dir`. Python: `UE4SS_BRIDGE_DATA_DIR`. No env var on the Lua side. Patch P1.
- Lua/API assumptions: UNKNOWN until the smoke test. It uses `LoopAsync`, `ExecuteInGameThread`, `RegisterHook`, `UnregisterHook`,
  `StaticFindObject`, `FindFirstOf`, `FindAllOf`, `ForEachUObject`, `IterateGameDirectories`, `DumpUSMAP`, `DumpJMAP`,
  `GenerateUHTCompatibleHeaders`, `GenerateSDK`, `DumpAllActors`, `DumpAllObjects`, `DumpStaticMeshes`, and the shared `UEHelpers`.
  Names were not checked against our build `v3.0.1-1164-g5e627997`. It needs Lua 5.4 features (`math.type`, `utf8`, `load` with env).
- Hot reload vs `EnableHotReloadSystem` / `EnableAutoReloadingLuaMods`: PASS by design. `reload_mod` is the mod's own `dofile` plus a
  generation counter that retires the old poll loop (main.lua:1307-1313, 1321). It does not use the UE4SS reload system. See Q5.
- Windows path handling: PASS. Backslashes are doubled in Lua strings (main.lua:37-40, 55); bridge files use `/` (main.lua:83-85). No single-backslash escapes.

### E. Verdict items
- Findings with severity and file:line: done above.
- Patches with diff: below (applied in Step 2, recorded in `mod/ue4ss-bridge/PATCHES.md`).
- Decision: approve with patches.

## allow_eval trace (how it is enforced)
1. Load: `SETTINGS.allow_eval` defaults to true (main.lua:52); settings.lua overrides it (main.lua:62-64).
2. If `allow_writes` is false, `allow_eval` is forced false (main.lua:76-80).
3. Request path: the poller reads request.json (main.lua:1323) then calls `handle` (1255). `ping`, `hello`, `batch` return before the eval check.
4. For `op == "eval"`: if `not SETTINGS.allow_eval`, it responds with an error and returns (main.lua:1288-1296). Only after that does it call `runEval` (1300).
5. `runEval` is the only place where `load` runs request text (main.lua:1233). No other op reaches it.
6. Batch ops (BATCH_OPS, main.lua:1158-1196) have no eval, `load` or `dofile` of request text. `reload` runs `dofile` on the fixed `MOD_PATH` only.
7. Residual risk: with `allow_writes = true`, `call` (any UFunction by name), `console` (UE console command) and `hook` still work. They are not Lua eval, but they are powerful.
   `UEB.settings` is a live table visible to eval (main.lua:303), but eval cannot start while the flag is off.
8. Server side: no gate (H2). Settings are re-read only on `reload` or game restart; the `reload` op is allowed even with eval off.
Conclusion: the Lua gate is correct and cannot be bypassed through the request protocol.

## MCP tools (26, server.py)
bridge_status (386), eval_lua (412), world_info (430), find_object (435), find_objects (440), list_types (445),
list_subclasses (450), targeted_actor (465), watch_property (480), hook_function (505), poll_events (523),
list_streams (538), stop_stream (543), inspect_object (548), snapshot_object (561), diff_object (576),
list_snapshots (598), forget_snapshot (603), reload_mod (608), list_functions (618), get_property (623),
set_property (628), batch (638), call_function (674), console_command (679), dump (684).

Gate by tool:
- Needs allow_eval (and so allow_writes): eval_lua.
- Needs allow_writes: set_property, call_function, console_command, hook_function, and `batch` entries of those ops.
- Not gated but heavy: dump (M6), list_types, list_subclasses, targeted_actor.
- Read-only: all others.

CLI verbs (same server): ping, hello, eval, world, reload, props, snapshot, diff, snapshots, forget, funcs, objects, types, subclasses, target, watch, hook, events, streams, unwatch, console, status.

## Lua verbs
Top-level request ops (main.lua:1255-1305): `ping`, `hello`, `batch`, `eval`.
Batch ops (BATCH_OPS, main.lua:1158): hello, reload, world, get, set, call, props, funcs, snapshot, diff, snapshots, forget, objects, types, subclasses, target, watch, hook, events, streams, unwatch, console, dump, find.
Helper table `UEB` (for eval): resolve, props, snapshot, diff, snapshots, forget, funcs, get, set, call, objects, types, subclasses, target, watch, hook, events, streams, unwatch, console, world, hello, dump, reload, encode, trace, version, protocol, settings.

## Filesystem paths used
Lua (inside the game):
- Reads: `<Win64>\ue4ss\Mods\UEBridge\scripts\main.lua` (dofile), `...\scripts\json.lua`, `...\scripts\settings.lua`, `...\UEBridge\settings.lua` (old fallback), and `UEHelpers` from UE4SS shared Lua.
- Reads and removes: `<ue4ss>\bridge\request.json` (or `bridge_dir`).
- Writes: `<ue4ss>\bridge\response.tmp`, `response.json`, `lastop.log` (300-byte trace line; may hold the first 300 chars of eval code).
- UE4SS dumpers write into the `ue4ss` folder (usmap, jmap, headers, SDK, actor and object lists).

Python (outside the game):
- Reads, writes and deletes `<ue4ss>\bridge\request.json`, `request.tmp`, `response.json`; reads `lastop.log`; creates the folder (server.py:268-275).
- Reads `%LOCALAPPDATA%\<Project>\Saved\Crashes\*\CrashContext.runtime-xml` (server.py:224-247).
- Env vars read: `UE4SS_BRIDGE_GAME_DIR`, `UE4SS_BRIDGE_DATA_DIR`, old `UE_BRIDGE_GAME_DIR`, `UE_BRIDGE_DATA_DIR`, `LOCALAPPDATA`.
- Subprocesses: `powershell -NoProfile -Command Get-CimInstance Win32_Process ...` (server.py:86) and `tasklist /FI "IMAGENAME eq <exe>.exe" /NH /FO CSV` (server.py:188).

## Network endpoints
- Outbound: none in this package.
- Inbound: only with `--http`: `http://127.0.0.1:8930/mcp` (streamable HTTP; port from `--port`; host fixed to 127.0.0.1). Stdio mode opens no port.
- The Lua mod opens no sockets.

## Answers to the spec's open questions
1. Old `Mods\` layout or `xinput` paths? Neither is assumed. It builds `<Win64>\ue4ss\...` from `IterateGameDirectories()` (main.lua:28-37), which fits the new layout. The mod folder must be `UEBridge` (M2).
2. `ExecuteInGameThread` per request or per poll? Per request. The poller (LoopAsync, 50 ms, async thread) reads the file, then queues one `ExecuteInGameThread` job for `batch` or `eval` (main.lua:1275, 1299). `hello` and `ping` run on the poll thread. `busy` blocks the next poll until the job ends. Paused game, main menu, loading screen: UNKNOWN. If the job does not run, the poller stalls (M3) and the client times out with "picked up but no response" (server.py:321). Needs the smoke test.
3. Verbs for UFunctions with struct/array params? Only `call` (`call_function`): `fn(obj, table.unpack(args))` with JSON args (main.lua:647-653). JSON objects and arrays become Lua tables, so struct and array inputs may work. No object-reference arguments, no out-parameters, `null` is dropped (L7). Return values are encoded (structs by reflection, TArrays to lists). Struct params are UNTESTED; the mod itself only passes tables in `LineTraceSingle` (main.lua:789). `eval_lua` is the fallback if allowed.
4. Python version and pins? `>=3.10`; one dependency `mcp>=1.8,<2`. No exact pins. We will pin (P7).
5. Hot reload and `EnableAutoReloadingLuaMods` (0)? The bridge does not use UE4SS hot reload. `reload_mod` re-runs only UEBridge itself (main.lua:1310) and re-reads its settings. It does not reload our other mods. For our mods use the UE4SS hot reload key (`EnableHotReloadSystem`), or an eval `dofile`, or a restart. With auto reload = 0 there is no interaction. If it were on, UE4SS would recreate the Lua state and the `UEB_GENERATION` guard (main.lua:1308) handles a double load. Untested.

## Required patches
Apply when vendoring into `mod/ue4ss-bridge/UEBridge/`. Record in `PATCHES.md`. Line numbers are for commit a5eae1c.

P1 (H1, M1) Safe defaults, and read the bridge dir from the environment:
```diff
--- a/ue4ss/UEBridge/scripts/main.lua
+++ b/ue4ss/UEBridge/scripts/main.lua
@@ -52 +52 @@
-local SETTINGS = { enabled = true, poll_ms = 50, allow_eval = true, allow_writes = true, bridge_dir = nil }
+local SETTINGS = { enabled = true, poll_ms = 50, allow_eval = false, allow_writes = true, bridge_dir = nil }
@@ -82 +82,3 @@
-local DIR = SETTINGS.bridge_dir or (UE4SS_DIR .. "\\bridge")
+-- HARNESS_RUN_DIR (set by the run launcher) wins; forward slashes only.
+local envDir = os.getenv("HARNESS_RUN_DIR")
+local DIR = (envDir and envDir ~= "" and (envDir:gsub("\\", "/") .. "/bridge")) or SETTINGS.bridge_dir or (UE4SS_DIR .. "\\bridge")
```
Also set `allow_eval = false` in `scripts/settings.lua`. Enabling eval then needs a local, uncommitted edit of `settings.lua`
(keep the committed file at false; use an untracked override). The Python side must use
`UE4SS_BRIDGE_DATA_DIR=%HARNESS_RUN_DIR%\bridge` (set in `.mcp.json` env or by the launcher). Both sides must use the same folder.
Check that `os.getenv` exists in the UE4SS Lua build.

P2 (H2) Server-side eval gate. Register `eval_lua` only when `UE4SS_BRIDGE_ALLOW_EVAL=1`:
```diff
--- a/ue4ss_bridge/server.py
+++ b/ue4ss_bridge/server.py
@@ -412 +412,2 @@
-    @mcp.tool(name="eval_lua")
-    def eval_lua_tool(code: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
+    if os.environ.get("UE4SS_BRIDGE_ALLOW_EVAL") == "1":
+      @mcp.tool(name="eval_lua")
+      def eval_lua_tool(code: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
```
Re-indent the body, and cap the timeout with `min(timeout, 60)`. Also add `mcp__ue4ss-bridge__eval_lua` to the Claude Code `deny` list.
The PyPI wheel cannot be patched in place, so vendor `server.py` from the pinned commit (recommended), or rely on the deny rule plus the Lua gate.

P3 (M2) Deploy the folder as `UEBridge` (make `deploy.ps1` copy `mod\ue4ss-bridge\UEBridge` to `Mods\UEBridge`). No code change.

P4 (M3) Make `busy` self-healing:
```diff
-local busy = false
+local busy, busySince = false, 0
 ...  (poller, near main.lua:1321)
-    if busy then return false end
+    if busy then
+        if os.time() - busySince < 120 then return false end
+        busy = false   -- game thread never answered; recover
+    end
 ...  (set busySince = os.time() wherever busy = true; protect respond)
-            if ok then respond(req.id, true, result, {}, nil, started)
-            else respond(req.id, false, nil, {}, tostring(result), started) end
-            busy = false
+            local okR, errR = pcall(respond, req.id, ok, ok and result or nil, {}, (not ok) and tostring(result) or nil, started)
+            if not okR then pcall(respond, req.id, false, nil, {}, "encode: " .. tostring(errR), started) end
+            busy = false
```
Apply the same pcall change to the eval callback (main.lua:1299-1304).

P5 (M5) Clamp limits: `limit = math.min(tonumber(limit) or 100, 500)` in `UEB.objects`, `UEB.types`, `UEB.subclasses`, `UEB.events`.
Add a hard cap (for example 1 MB) on the encoded body in `respond`; above it, return an error result.

P6 (M6) Add `requireWrites("dump")` as the first line of `UEB.dump` (main.lua:1141), or remove the `dump` op and tool.

P7 Pinning (no code change):
- Use `ue4ss-bridge==1.2.0` with hashes (`--require-hashes`), or the vendored `server.py`.
- Create a lock file for `mcp` and its dependencies. Review the `mcp` version if HTTP is ever used.
- Run stdio only. Do not use `--http`.
- Set `UE4SS_BRIDGE_GAME_DIR` or `UE4SS_BRIDGE_DATA_DIR` so it cannot attach to another game (L8).
- In `.mcp.json`, do not auto-approve `eval_lua`, `set_property`, `call_function`, `console_command`, `hook_function`, `dump`.

## Still to do (outside this review)
- Vendor the Lua from commit `a5eae1c` into `mod/ue4ss-bridge/` with the patches; write `VERSION` and `PATCHES.md`.
- Re-read the patched Lua diff once.
- Run the six smoke tests. In particular test: main menu with no world; paused game; kill mid-request; the `HARNESS_RUN_DIR` path; a call with a struct argument.
- Confirm the API names exist in UE4SS `v3.0.1-1164-g5e627997`. A good load logs `[UEBridge] v1.2.1 ready` in UE4SS.log.
