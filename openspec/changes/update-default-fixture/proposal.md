## Why

Issue #379. Owner decision (2026-10-22): the default fixture becomes `base-corpse-pit`. It is the `base` village with a built corpse pit (#360, fixture added in #371). The corpse pit carries raider loot back to the village, so most raid tests need it.

## What Changes

- `DEFAULT_FIXTURE` becomes `base-corpse-pit`. The `default` tag in `harness/fixtures/fixtures.json` moves to it.
- `base` stays in the manifest unchanged. A test scenario that needs the village without the pit names `base` with `--fixture base`.
- Test scenarios whose docstring says they run on `base` and that rely on its exact state (family count, approval, free homes) are checked; each either still works on the new default or names `base`.
- Docs that name the default (`docs/wiki/workflows/dev-loop-and-fixtures.md`) are updated.

## Capabilities

### Modified Capabilities

- `harness/save-fixtures`: "Fixtures are listed in a manifest" (the default fixture).

## Impact

- `harness/runlib/fixtures.py`, `harness/fixtures/fixtures.json`, test scenario docstrings, the wiki page above.
- The fixture files are local (git ignores the store). A machine without `base-corpse-pit` must import it (`harness/tools/fixtures.py import`).
