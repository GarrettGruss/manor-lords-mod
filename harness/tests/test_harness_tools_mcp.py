import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import harness_tools_path  # noqa: F401
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXPECTED_TOOLS = {
    "list_scenarios", "run_scenario", "wait_for_run", "read_summary", "list_runs",
    "read_log", "read_telemetry", "list_screenshots", "game_status", "stop_game",
}
READ_ONLY_TOOLS = EXPECTED_TOOLS - {"run_scenario", "stop_game"}


def payload(result) -> dict:
    return result.structuredContent or json.loads(result.content[0].text)


class McpServerTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.runs = Path(temp.name) / "runs"
        (self.runs / "r1").mkdir(parents=True)
        (self.runs / "r1" / "summary.json").write_text(json.dumps({"run_id": "r1", "verdict": "pass"}))

    def with_session(self, work):
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "harness_tools"],
            env={**os.environ,
                 "PYTHONPATH": os.pathsep.join([str(REPO_ROOT / "mcp"), str(REPO_ROOT / "harness")]),
                 "HARNESS_RUNS_ROOT": str(self.runs)},
        )

        async def go():
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await work(session)

        return asyncio.run(asyncio.wait_for(go(), timeout=60))

    def test_lists_tools_and_calls_two(self):
        async def work(session):
            listed = (await session.list_tools()).tools
            scenarios = await session.call_tool("list_scenarios", {})
            summary = await session.call_tool("read_summary", {})
            rejected = await session.call_tool("read_summary", {"run_id": "../x"})
            return listed, scenarios, summary, rejected

        listed, scenarios, summary, rejected = self.with_session(work)
        self.assertEqual({t.name for t in listed}, EXPECTED_TOOLS)
        for tool in listed:
            self.assertTrue(tool.description, tool.name)
            is_read_only = bool(tool.annotations and tool.annotations.readOnlyHint)
            self.assertEqual(is_read_only, tool.name in READ_ONLY_TOOLS, tool.name)
        self.assertIn("noop", json.dumps(payload(scenarios)))
        self.assertEqual(payload(summary)["summary"]["verdict"], "pass")
        self.assertFalse(payload(rejected)["ok"])


if __name__ == "__main__":
    unittest.main()
