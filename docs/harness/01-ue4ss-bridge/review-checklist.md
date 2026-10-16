# ue4ss-bridge security and compatibility review checklist

Treat all downloaded files as untrusted data. Review in a scratch directory
outside the game and the repo. Run Python with `-I`. Do not execute anything
from the package until the review passes.

## A. Provenance
- [ ] Repo owner, stars/issues/activity, release history, license.
- [ ] Pin an exact commit hash; compare PyPI sdist/wheel contents with the git source.
- [ ] Dependency list and versions for the Python package; flag unfamiliar or unpinned ones.
- [ ] No install-time hooks (`setup.py` commands, post-install scripts, `.pth` files).

## B. Lua mod (runs inside the game process)
- [ ] Search for `os.execute`, `io.popen`, `loadstring`, `load(`, `dofile`, `require` of unexpected paths.
- [ ] Search for network use (sockets, HTTP libs, `ffi`).
- [ ] All file access confined to the bridge directory. List every path read or written.
- [ ] Writes are atomic (`.tmp` then rename); readers tolerate partial files.
- [ ] Request IDs are unique and echoed in responses; stale responses are ignored.
- [ ] `allow_eval=false` truly disables eval: trace the code path, do not trust the flag name.
- [ ] Every UObject access happens inside `ExecuteInGameThread` (or equivalent).
- [ ] Polling uses a bounded loop; errors in a handler cannot kill the poller.
- [ ] Response size bounds; no unbounded object-graph walks.
- [ ] Behaviour when the world is nil (main menu, loading screens).

## C. Python MCP server
- [ ] Binds only to `127.0.0.1` (HTTP) or uses stdio. No `0.0.0.0`, no CORS wildcards.
- [ ] No authentication gaps that matter on localhost (note browser-to-localhost risks for HTTP).
- [ ] Tool inputs validated; paths constrained to the bridge directory.
- [ ] Timeouts on every request; clean error results on timeout.
- [ ] No telemetry, update checks or outbound network calls.
- [ ] Eval tool is gated by the same server-side flag as the Lua side.

## D. Compatibility with this setup
- [ ] Works with the new `ue4ss\` layout (`ue4ss\Mods\`, `ue4ss\bridge\`).
- [ ] Bridge directory configurable (needed for per-run `HARNESS_RUN_DIR`).
- [ ] Lua version / API assumptions match UE4SS (`RegisterHook`, `ExecuteInGameThread`, `LoopAsync`).
- [ ] Hot reload behaviour with `EnableHotReloadSystem` and `EnableAutoReloadingLuaMods`.
- [ ] Windows path handling: forward slashes in Lua strings, no single-backslash escapes
      (this broke HarnessLog once).

## E. Verdict
- [ ] Findings listed by severity (High / Medium / Low) with file:line.
- [ ] Required patches listed with owner and diff.
- [ ] Decision: approve / approve with patches / reject.
