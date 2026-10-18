# Proposal: test that a mod menu stays open for five minutes

Issue: #272. Legacy source: `openspec/changes/archive/2026-10-18-legacy-34-widget-click-hooks/README.md`. Legacy issue: #254 (closed).

## Why

Spec 34 replaced the polling of menu buttons with click hooks. A 50 ms scheduler tick broke the Lua state after about 3 minutes with a menu open. The tick is now 100 ms. The proof is a one-time run (`20261018-173614-d910`, 300 s). It is not a committed test scenario. The pull request that syncs the living specs (#267) marks the scenario "A menu stays open" as "Not checked yet".

Two small items are open in the spec 34 README:
- The click button source widget has a leftover graph with compile errors ("Can't connect pins"). The event works, but a cleaner source is better.
- The shared module `HarnessClickHooks` is in no living spec. See the Capabilities note below.

## What Changes

- A test scenario that opens a menu, waits 300 s with the state read twice a second, and asserts that the Lua state is alive and the clicks still count.
- A cleaner source for the click button widget.

## Non-goals

- A new menu layout, hover, tooltips, keyboard focus.
- A faster scheduler tick.

## Legacy folders

- `openspec/changes/archive/2026-10-18-legacy-34-widget-click-hooks/` (note: `implementation-notes/click-hook-method.md`).

## Capabilities

### New Capabilities
- None here. The lead should decide where the built module `HarnessClickHooks` (`attach`, `bind_texts`, `set_text`, `set_visible`, `drain`, `release`) is specified. It fits no existing capability. It could be a requirement of `harness/game-actions`, or a new capability `harness/click-hooks`.

### Modified Capabilities
- `mod/core`: the scenario "A menu stays open" gets a check. This is a text edit of the line "Not checked yet" after #267 is merged. This change is a `skip_specs` task list until then.

## Impact

- New test scenario under `mod/InvasionMod/scenarios/tech_tree/` (the menu with the click button).
- `mod/shared/HarnessClickHooks/ue/make_click_button.py` and the pak `techmenu_P.pak`, `raidmenu_P.pak` if the source changes.
