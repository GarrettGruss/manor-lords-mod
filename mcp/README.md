# ue4ss-bridge MCP server

Vendored from upstream commit a5eae1c with harness patches. See
`docs/harness/01-ue4ss-bridge/implementation-notes/patches-python.md`.

## Setup (from the repo root, with uv)

1. Make the venv `.venv` from the lock file (`pyproject.toml`, `uv.lock`; `mcp==1.30.0` is pinned): `uv sync`
2. Claude Code starts the server from `.mcp.json` over stdio. To start it by hand:
   `$env:PYTHONPATH = "mcp"; uv run python -m ue4ss_bridge`
   Running `python mcp/ue4ss_bridge/__main__.py` directly does not work. The file uses relative imports.

Use stdio only. Do not use `--http`.

## Change a dependency

Use `uv add <name>` or `uv remove <name>` from the repo root. It updates `pyproject.toml` and `uv.lock`; commit both.

## Environment variables

- `UE4SS_BRIDGE_GAME_DIR`: the game `Win64` folder.
  `C:\Program Files (x86)\Steam\steamapps\common\Manor Lords\ManorLords\Binaries\Win64`
- `UE4SS_BRIDGE_DATA_DIR`: leave it unset for manual use. The server and the Lua mod then both use `ue4ss\bridge`. The run launcher sets `HARNESS_RUN_DIR` for the Lua mod, so it must also set this to the absolute path `<HARNESS_RUN_DIR>\bridge`.
- `UE4SS_BRIDGE_GAME_PID`: optional. The process id of the game. With it, the "is the game running" check looks at that one process, not at every process with the game's image name. The run launcher sets it, because parallel games (spec 11) share the image name and `tasklist` can time out under load.
- `UE4SS_BRIDGE_ALLOW_EVAL`: leave it unset. Only `1` registers the `eval_lua` tool and the CLI `eval` verb.
