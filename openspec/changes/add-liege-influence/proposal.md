# Proposal: add the influence balance of the liege

Issue: #271. Legacy source: `docs/mod/M11-liege_influence/README.md` (iteration table row "01 influence-balance", no iteration file).

## Why

The design (M00) says the player is sworn to a liege. Tribute to the liege gives influence, and influence buys aid, villagers, weapons or tools. M11 is not started. It is a backlog feature (M00 decision 9, 2026-10-16): the liege is off-screen and only a custom menu represents it. The user decided on 2026-10-18 that all open legacy work moves into changes, so the first step gets a change. This change stays in the backlog until the user starts it.

## What Changes

- The mod keeps an influence value (mod-owned, in ModState).
- A tribute sent to the liege raises the influence.
- The influence is shown by a named command.

## Non-goals

- Spending influence on villagers, weapons or tools (legacy iteration 02).
- A liege aid call and a military aid army (legacy iteration 03).
- Path effects of M12 on influence (oppression: military success, prosperity: tribute and wealth).
- The relief army of the great raid. M02 owns it until M11 starts.
- A menu. The first step uses a named command (see open question 2 in `design.md`).

## Legacy folders

`docs/mod/M11-liege_influence/` (read-only). Related: `docs/mod/M00-invasion-mod/` (design, owned by the user).

## Capabilities

### New Capabilities
- `mod/liege_influence`: the influence value and how tribute raises it.

### Modified Capabilities
- None.

## Impact

- New feature folder `mod/InvasionMod/Scripts/features/liege_influence/`, `data/liege_influence/` if it needs data, and `scenarios/liege_influence/`.
- It requires `mod_state` and `tribute`.
- Wiki, the mod feature list and CHANGELOG.
