# Mod docs: Invasion Mod

This folder holds the design and the legacy feature specs of the Invasion Mod (internal name `InvasionMod`; the player-facing name will change).
The legacy harness specs are in `docs/harness/`. The layout and build rules of the mod are in harness spec 22 (`docs/harness/22-mod-pack-layout/`).

> **Since 2026-10-18, new mod work is planned in OpenSpec (`openspec/`).** See the archived change `openspec/changes/archive/2026-10-18-adopt-openspec/` (issue #251) and `openspec/specs/process/spec-workflow/spec.md`.
> - `M00-invasion-mod/` stays here. It is the design. The user owns it.
> - The `M<NN>-<feature>/` folders are read-only legacy. Do not add iterations or notes. An iteration that had an open issue on 2026-10-18 may finish here.
> - The built behavior of each feature is in its living spec `openspec/specs/mod/<feature>/spec.md` (change `backfill-living-specs`, issue #253). Shared parts: `mod/core`. Standalone player mods: `openspec/specs/mods/<name>/`.
> - A new iteration is an OpenSpec change (`openspec/changes/<change-name>/`). A planned iteration file here is rewritten into a change when its work starts.
> - Feedback goes to `openspec/specs/mod/<feature>/feedback.md`. The first change for a feature moves the open items from the legacy `feedback.md`.
>
> The sections "How a feature spec is written" and "How a feature grows" below describe the legacy process.

## Documents
| Doc | What it is | Owner |
| --- | --- | --- |
| `M00-invasion-mod/` | Overview design of the whole mod: vision, pillars, feature map | the user |
| design docs (to come) | Game design docs that the user scaffolds | the user |
| `M<NN>-<feature>/` | One spec per core feature, broken out of the design docs | agent, reviewed by the user |

The batch plan that breaks M00 into feature specs is in [`feature-breakdown.md`](feature-breakdown.md).

A feature spec is made only when the user breaks a part of the design out into a core feature.

## How a feature spec is written (legacy)
Path: `docs/mod/M<NN>-<feature>/`. `<feature>` is the same name as in `mod/InvasionMod/Scripts/features/<feature>/`, `data/<feature>/` and `scenarios/<feature>/`.
```
M01-<feature>/
  README.md                 the living spec: goal, player rules, current state, tunables, iteration list
  iterations/
    01-<name>.md            one iteration: goal, changes, acceptance criteria, scenarios, result
  feedback.md               player feedback, dated, with the iteration that answers it
  implementation-notes/     findings, one file per topic
```
- `README.md` always describes the feature as it is now. When an iteration is done, update the README in the same branch.
- Each iteration has acceptance criteria as measurable game state (ranges). At least one scenario checks each criterion.
- Branch per iteration: `feat/M<NN>-<feature>-<iteration>`, for example `feat/M02-refugees-01-first-wave`.
- One GitHub issue per iteration: `Mod M<NN>.<iteration>: <name>`.
- Tuning-only changes (values in `config.lua`) need no iteration file. Log them in `feedback.md` and in the mod changelog.

## How a feature grows (legacy)
1. Feedback comes in. Write it in `feedback.md`.
2. If it is a number, change the tunable and run the feature's scenarios.
3. If it changes the rules, write a new iteration file first, then the code.
4. If a feature grows too large, split it into a new feature with its own `M<NN>` spec. `requires` in `mod.json` keeps the load order.

## References
- `mod/RefugeeWaves` (spec 15, #51): an example of a small feature with tunables, a configure command and no hidden save state. The `refugees` feature is built new; RefugeeWaves is only a reference.
- Test criteria from the first brief: `docs/harness/10-invasion-testability/criteria.json`.
