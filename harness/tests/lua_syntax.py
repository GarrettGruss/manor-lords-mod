# Syntax check for every Lua file in mod/. Run from the repo root:
#   uv run --no-project --python 3.12 --with lupa python harness/tests/lua_syntax.py
﻿import sys, pathlib
from lupa import LuaRuntime
lua = LuaRuntime()
bad = 0
for p in sorted(pathlib.Path("mod").rglob("*.lua")):
    try:
        lua.compile(p.read_text(encoding="utf-8"))
        print("ok  ", p)
    except Exception as e:
        bad += 1
        print("FAIL", p, str(e)[:200])
sys.exit(1 if bad else 0)
