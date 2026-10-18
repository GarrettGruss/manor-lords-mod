# Design

This folder holds the game design of the Invasion Mod (internal name `InvasionMod`; the player-facing name will change). It is part of `design/` (see [`../README.md`](../README.md)). The user owns it. Agents read it and cite it; they change it only when the user asks.

| File | What it is |
| --- | --- |
| [`invasion-mod.md`](invasion-mod.md) | The guiding philosophy: vision, pillars, core loop, factions, systems, pacing, out of scope. Every mod spec and change serves it. |
| [`decisions.md`](decisions.md) | The decision log of the user. Numbers stay stable, because specs, changes and code comments cite them ("decision 28"). New decisions go at the end. |
| [`trailer.md`](trailer.md) | The trailer brief. The change `add-trailer-pipeline` builds from it. |

## How the design reaches the specs

- `openspec/config.yaml` holds a short summary of the pillars. OpenSpec adds it to every planning request.
- A mod proposal names the design section it serves and must not contradict the pillars.
- Built behavior is in the living specs (`openspec/specs/mod/<feature>/spec.md`). Planned work is in the changes (`openspec/changes/<change-name>/`).

## History

- The original M00 overview design, with the old feature map, build plan, balance targets and open questions, and the feasibility reviews of 2026-10-15: `openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/`.
- The old feature specs M01 to M14 and the batch plan: `openspec/changes/archive/<date>-legacy-m<NN>-<feature>/` and `<date>-legacy-mod-feature-breakdown/`.
- The open questions that are not answered: the change `decide-open-mod-rules`.
