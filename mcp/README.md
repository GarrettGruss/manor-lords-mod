# ue4ss-bridge MCP server

Vendored from upstream commit a5eae1c with harness patches. See
`docs/specs/01-ue4ss-bridge/implementation-notes/patches-python.md`.

## Setup (from the repo root)

1. Create the virtual environment: `py -m venv .venv`
2. Install the pinned dependency: `.venv\Scripts\python.exe -m pip install -r mcp\requirements.txt`
3. Start the server (Claude Code does this from `.mcp.json`). Set `PYTHONPATH=mcp` so Python finds the package:
   `$env:PYTHONPATH = "mcp"; .venv\Scripts\python.exe -m ue4ss_bridge`
   Running `python mcp/ue4ss_bridge/__main__.py` directly does not work. The file uses relative imports.

Use stdio only. Do not use `--http`.

## Environment variables

- `UE4SS_BRIDGE_GAME_DIR`: the game `Win64` folder.
  `C:\Program Files (x86)\Steam\steamapps\common\Manor Lords\ManorLords\Binaries\Win64`
- `UE4SS_BRIDGE_DATA_DIR`: leave it unset for manual use. The server and the Lua mod then both use `ue4ss\bridge`. The run launcher sets `HARNESS_RUN_DIR` for the Lua mod, so it must also set this to the absolute path `<HARNESS_RUN_DIR>\bridge`.
- `UE4SS_BRIDGE_ALLOW_EVAL`: leave it unset. Only `1` registers the `eval_lua` tool and the CLI `eval` verb.
