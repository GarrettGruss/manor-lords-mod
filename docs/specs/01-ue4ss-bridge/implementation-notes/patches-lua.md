# Lua patches (P1, P4, P5, P6)

Files: `mod/UEBridge/scripts/main.lua`, `mod/UEBridge/scripts/settings.lua`.
Source: review patches in `review-report.md`. Each changed region has a `-- PATCH P<n> (harness)` comment.
Line numbers are for the patched files.

## P1 Safe defaults, bridge dir from environment
- `main.lua:52-53`: `SETTINGS.allow_eval` default is now `false`.
- `settings.lua:15-16`: `allow_eval = false`. `settings.lua` also documents `HARNESS_RUN_DIR`.
- `main.lua:83-90`: bridge dir is `<HARNESS_RUN_DIR>/bridge` (backslashes become `/`, trailing `/` removed).
  Fallbacks: `settings.bridge_dir`, then `<ue4ss>\bridge`. `os.getenv` is checked with `type()` and called with `pcall`.
- `main.lua:92-117`: new `ensureBridgeDir()`. The original code never created the folder.
  It tests a write, then tries `os.execute('mkdir ...')` under `pcall`, and logs an error if the folder still does not exist.

Not verified:
- `os.getenv` and `os.execute` exist in the UE4SS Lua build. The code survives their absence, but then the folder must be created by the launcher.
- `os.execute` may flash a console window. The launcher should create the folder, so this is only a fallback.
- Python side must use the same folder (`UE4SS_BRIDGE_DATA_DIR`). Not part of this patch.

## P4 Self-healing `busy`
- `main.lua:1277-1278`: `busy, busySince` and `BUSY_RECOVER_SECONDS = 120`.
- `main.lua:1302-1310`: new `respondAndClearBusy`. It calls `respond` under `pcall`, tries an `encode:` error response if that fails, and always clears `busy`.
- Batch callback (`main.lua:1331-1337`) and eval callback (`main.lua:1355-1360`) set `busySince` and use the helper.
- Poller (`main.lua:1379-1383`): after 120 s busy, it logs and clears `busy`.

Not verified: behavior when the game thread is really blocked. `os.time()` has 1 s resolution, which is fine for 120 s.
A late callback that runs after recovery will still write a response and clear `busy`; this can overlap with a newer request. Accepted risk.

## P5 Limit clamp and response cap
- `main.lua:160-162`: `MAX_LIMIT = 500`, `MAX_BODY_BYTES = 1000000`.
- Clamp in `UEB.objects` (691), `UEB.types` (703), `UEB.subclasses` (725), `UEB.events` (1053).
  Non-numeric limits now fall back to the old defaults instead of failing.
- `respond` (`main.lua:1289-1297`): if the encoded body is over the cap, it is replaced by an error response
  ("response too large ... use a smaller limit"), keeping the request id.

Not verified: the Python server may read `result` only; it must handle `ok=false` with `error`. Other ops (not in the four listed) can still return large bodies, but the body cap covers them.

## P6 Gate `dump`
- `main.lua:1176`: `requireWrites("dump")` is the first line of `UEB.dump`.

Not verified: that the batch op reports the `requireWrites` error cleanly for `dump`. Same helper as `set`/`call`.

## Verification status
No Lua interpreter (`lua`, `luajit`, `luac`) exists on this machine. No syntax check was run. The edits were re-read by hand only.
Nothing was run in the game. No runtime verification is claimed.
