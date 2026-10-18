# Real runs

| Run id | Test scenario | Verdict | Result |
|---|---|---|---|
| 20261018-230211-b6d4 | smoke | pass | `mod.log` has 23 `[UEBridge] request` lines, all `ok`, with id, verb, target and ms. No property value or Lua source is in the lines. |

Example line: `INFO [UEBridge] request id=a6029688de47 verb=objects target=- ms=16 ok`.

Save fixtures are git-ignored. A new worktree must copy `harness/fixtures/saves/` from the main checkout before a real run. Otherwise preflight fails with "the files of fixture 'base' differ from the manifest".
