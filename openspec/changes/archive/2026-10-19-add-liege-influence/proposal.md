# Proposal: add the influence balance of the liege

Issue: #271. Legacy source: `openspec/changes/archive/2026-10-16-legacy-m11-liege-influence/README.md` (iteration table row "01 influence-balance", no iteration file).

## Why

The design (M00) says the player is sworn to a liege. Tribute to the liege gives influence, and influence buys aid, villagers, weapons or tools. M11 is a backlog feature (M00 decision 9, 2026-10-16): the liege is off-screen and only a custom menu represents it. The owner answered the open questions on 2026-10-19 and approved the start (see `design.md`).

## What Changes

- The mod keeps an influence value (mod-owned, in ModState). It does not decay and has no cap.
- The player sends silver from the lord's treasury to the liege through a pak widget menu.
- 10 silver of tribute gives 1 influence (`influence_per_unit` is 0.1, set in the feature config).
- The command `InvasionMod.liege_send_tribute` is the action behind the menu and is used by tests. The command `InvasionMod.liege_state` shows the influence.

## Non-goals

- Spending influence on villagers, weapons or tools (legacy iteration 02).
- A liege aid call and a military aid army (legacy iteration 03).
- Path effects of M12 on influence (oppression: military success, prosperity: tribute and wealth).
- The relief army of the great raid. M02 owns it until M11 starts.
- Sending goods or silver from the regional treasury.

## Legacy folders

`openspec/changes/archive/2026-10-16-legacy-m11-liege-influence/` (read-only). Related: `design/` (design, owned by the user).

## Capabilities

### New Capabilities
- `mod/liege_influence`: the influence value, the tribute menu and how tribute raises influence.

### Modified Capabilities
- None.

## Impact

- New feature folder `mod/InvasionMod/Scripts/features/liege_influence/`, `data/liege_influence/` for the widget asset, and `scenarios/liege_influence/`.
- A new widget in the Invasion Mod pak (`ue/` sources, cooked asset).
- It requires `mod_state` and `tribute`, and the shared module `HarnessClickHooks`.
- Wiki, the mod feature list and CHANGELOG.
