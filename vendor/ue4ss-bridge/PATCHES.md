# Patches to upstream ue4ss-bridge

Base: upstream commit a5eae1c (see `VERSION`). Reason for each patch: `openspec/changes/archive/2026-10-15-legacy-01-ue4ss-bridge/implementation-notes/review-report.md`.
Each changed place in the code has a comment `PATCH P<n> (harness)`. Search for it to find all changes.

| Patch | File | Change |
|---|---|---|
| P1 | `mod/UEBridge/scripts/main.lua`, `settings.lua` | `allow_eval` is off by default. The bridge folder follows `HARNESS_RUN_DIR`. The folder is created if missing. |
| P4 | `mod/UEBridge/scripts/main.lua` | `busy` clears itself after 120 s. A failed reply cannot leave `busy` set. |
| P5 | `mod/UEBridge/scripts/main.lua` | Result limits are at most 500. A response over 1,000,000 bytes becomes an error. |
| P6 | `mod/UEBridge/scripts/main.lua` | `dump` needs `allow_writes`. |
| P2 | `mcp/ue4ss_bridge/server.py` | `eval_lua` and the CLI `eval` verb work only if `UE4SS_BRIDGE_ALLOW_EVAL=1`. The eval timeout is at most 60 s. |
| P8 | `mod/UEBridge/scripts/main.lua` | `get`, `set` and `call` refuse a name that is not a non-empty string. A nil name crashed the game (see `smoke-test-log.md`). |
| P9 | `mod/UEBridge/scripts/main.lua` | One `HarnessLog` line per request (id, verb, target, duration, error text). It holds no property value and no Lua source. |
| P3 | none | The Lua mod lives in `mod/UEBridge/`, so `harness/deploy.ps1` deploys it as `Mods\UEBridge`. |
| P7 | `pyproject.toml` and `uv.lock` (was `mcp/requirements.txt`), `.mcp.json`, `.claude/settings.json` | `mcp` is pinned. Stdio only. All tools of both project MCP servers are allowed without a prompt (user decision 2026-10-12); the game-side `allow_writes` and `allow_eval` settings and `UE4SS_BRIDGE_ALLOW_EVAL` still decide what runs. |

## Known limits of the patches
- In-game tests so far: see `openspec/changes/archive/2026-10-15-legacy-01-ue4ss-bridge/implementation-notes/smoke-test-log.md`. No Lua interpreter exists on the dev machine, so the Lua is checked only by reading it and by running it in the game.
- It is not checked that `os.getenv` and `os.execute` exist in the UE4SS Lua build. The code guards against both missing.
- P4: if the 120 s recovery fires and the old job finishes later, that job can clear `busy` while a newer request runs. This is rare and not fixed.
- A request can still run after the client timed out (review finding M4). After a timeout, read the state again.
- `mcp==1.30.0` is not tested with this server. Upstream was written for `>=1.8,<2`.
- `.mcp.json` uses relative paths. Claude Code must start from the repo root.
