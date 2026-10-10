# ue4ss-bridge MCP server

Vendored from upstream commit a5eae1c with harness patches. See
`docs/specs/01-ue4ss-bridge/implementation-notes/patches-python.md`.

## Setup (from the repo root, with uv)

1. Create the virtual environment: `uv venv --python 3.12 .venv`
2. Install the locked dependencies (hashes are checked):
   `uv pip install --python .venv\Scripts\python.exe --require-hashes -r mcp\requirements.txt`
3. Claude Code starts the server from `.mcp.json` over stdio. To start it by hand:
   `$env:PYTHONPATH = "mcp"; .venv\Scripts\python.exe -m ue4ss_bridge`
   Running `python mcp/ue4ss_bridge/__main__.py` directly does not work. The file uses relative imports.

Use stdio only. Do not use `--http`.

## Change a dependency

Edit `mcp/requirements.in`, then rebuild the lock file:
`uv pip compile mcp\requirements.in --generate-hashes --python-version 3.12 -o mcp\requirements.txt`

## Environment variables

- `UE4SS_BRIDGE_GAME_DIR`: the game `Win64` folder.
  `C:\Program Files (x86)\Steam\steamapps\common\Manor Lords\ManorLords\Binaries\Win64`
- `UE4SS_BRIDGE_DATA_DIR`: leave it unset for manual use. The server and the Lua mod then both use `ue4ss\bridge`. The run launcher sets `HARNESS_RUN_DIR` for the Lua mod, so it must also set this to the absolute path `<HARNESS_RUN_DIR>\bridge`.
- `UE4SS_BRIDGE_ALLOW_EVAL`: leave it unset. Only `1` registers the `eval_lua` tool and the CLI `eval` verb.
