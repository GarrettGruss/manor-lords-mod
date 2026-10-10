# Python patches (harness)

Applies to `mcp/ue4ss_bridge/server.py`, vendored from upstream a5eae1c.
Source: `review-report.md`, section "Required patches" (P2, P7) and finding L6.
Line numbers are for the patched file.

## P2: eval gate (lines 48, 413-432)
- `eval_lua` is registered only when `UE4SS_BRIDGE_ALLOW_EVAL == "1"`.
- The timeout is capped with `min(timeout, MAX_EVAL_TIMEOUT)`. The cap is 60 s (constant at line 48).
- The tool body is re-indented by two spaces, as in the report diff.

## P2b: CLI eval gate and L6 (lines ~723-726)
- The CLI verb `eval` shares `server.py`. It could send eval requests without the gate. It now fails with a clear error unless `UE4SS_BRIDGE_ALLOW_EVAL=1`.
- L6 names only the `eval_lua` timeout as unbounded. Other tools use fixed timeouts (30 s, 60 s for `batch`, 600 s for `dump`). No other change was made.
- `limit` arguments of list tools are not clamped in Python. P5 clamps them in Lua.

## P7: pinning and client config
- `mcp/requirements.txt`: `mcp==1.30.0`. It is the newest 1.x release on PyPI. No hashes and no lock file for sub-dependencies yet.
- `mcp/README.md`: setup steps.
- `.mcp.json`: stdio server `ue4ss-bridge`, `.venv\Scripts\python.exe -m ue4ss_bridge`, `PYTHONPATH=mcp`. `ALLOW_EVAL` is not set.
- `.claude/settings.json`: `deny` for `eval_lua`; `ask` for `set_property`, `call_function`, `console_command`, `hook_function`, `dump`. No `allow` entries.

## Checks done
- `py -I -m py_compile` passed. No `__pycache__` was left.

## Unverified
- The server was not run. `mcp==1.30.0` was not installed or tested with this code (written for `>=1.8,<2`).
- Claude Code behaviour for relative `command` and `PYTHONPATH` in `.mcp.json` is not tested.
- `UE4SS_BRIDGE_DATA_DIR` is `runs\bridge` (relative). It must equal the Lua bridge folder (`HARNESS_RUN_DIR/bridge`, P1). It depends on the server working directory. The run launcher should set an absolute path.
- A `deny` rule hides the tool only if the tool is registered. With eval off, the tool does not exist at all.
