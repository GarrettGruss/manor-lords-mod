# Changelog

All notable changes to this project are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `HarnessLog` shared Lua module. It writes a log file that flushes on each line.
- `HarnessLogTest` mod to check that the log works.
- `harness/deploy.ps1` to copy mods into the UE4SS `Mods` folder and enable them.
- Spec `docs/specs/01-ue4ss-bridge/` with a review checklist.
- Spec `docs/specs/02-save-autoload/` for the save auto-load and ready signal.
- Jmap findings for the game reflection data, in `docs/specs/02-save-autoload/implementation-notes/`.
- `CLAUDE.md` with project rules, including one feature branch for each spec and Sonnet for subagents.
- Security review of ue4ss-bridge, with required patches P1 to P7.
- Vendored `ue4ss-bridge` 1.2.1 (upstream a5eae1c): the `UEBridge` Lua mod in `mod/UEBridge/` and the MCP server in `mcp/ue4ss_bridge/`. See `vendor/ue4ss-bridge/PATCHES.md`.
- Project MCP config `.mcp.json` (stdio) and `.claude/settings.json`. Eval is denied. Risky bridge tools ask first.

### Changed
- Vendored bridge: raw Lua eval is off by default, and it is gated in the Python server too.
- Vendored bridge: the bridge folder follows `HARNESS_RUN_DIR`.
- MCP dependencies are locked with hashes (`mcp/requirements.in` and `mcp/requirements.txt`) and installed with uv.

### Fixed
- Vendored bridge: the poller no longer stays busy forever after a failed reply. Large responses and limits are capped. `dump` needs `allow_writes`.
- Vendored bridge: a nil property or function name no longer crashes the game. It returns an error.
