# Mod docs: Invasion Mod

This folder holds the game design of the Invasion Mod (internal name `InvasionMod`; the player-facing name will change).

| Doc | What it is | Owner |
| --- | --- | --- |
| `M00-invasion-mod/` | Overview design of the whole mod: vision, pillars, feature map, decisions | the user |
| design docs (to come) | Game design docs that the user scaffolds | the user |

Do not write game design content here unless the user asks.

## Where the rest is

- **Built behavior of each feature:** the living spec `openspec/specs/mod/<feature>/spec.md`. Shared parts: `openspec/specs/mod/core/spec.md`.
- **Planned work:** an OpenSpec change in `openspec/changes/<change-name>/`. A new iteration starts as a change (see `CONTRIBUTING.md`).
- **Player feedback:** `openspec/specs/mod/<feature>/feedback.md`.
- **The old feature specs `M01` to `M14` and the batch plan `feature-breakdown.md`:** moved into the OpenSpec archive as `openspec/changes/archive/<date>-legacy-m<NN>-<feature>/` and `<date>-legacy-mod-feature-breakdown/`, unchanged inside (change `archive-legacy-specs`, #288). The path map is in that change's `notes/path-map.md`.
- **Layout and build rules of the mod:** legacy harness spec 22, now `openspec/changes/archive/2026-10-15-legacy-22-mod-pack-layout/`, and the living specs `mod/core` and `harness/pak-mods`.
