"""Import this first in a harness_tools test. It makes runlib and harness_tools importable."""

import sys
from pathlib import Path

import runlib_path  # noqa: F401

MCP_DIR = Path(__file__).resolve().parent.parent.parent / "mcp"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))
