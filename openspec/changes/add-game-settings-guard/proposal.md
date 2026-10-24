## Why

Issue: #438. The Invasion Mod needs AI lords (AI Opponents) for vassals. The player can set AI opponents to 0 in the New Game settings of the game. The mod then offers vassals that cannot work, and the player does not know why.

Owner decision 2026-10-24: the Hussite lock is removed. Spike #430 proved that the Hussite raids of the mod (mod-made AI lord armies) work with Off Map Adversary absent. The 6th template of the owner (change `add-hussite-scenario-template`) sets it absent. So the off-map adversary needs no guard.

## What Changes

- At new game start, the mod reads the game setup once and saves one mod setting in ModState: `vassals` (true/false).
- When `vassals` is false, the mod start menu shows the warning "vassals are not enabled". No row is locked.
- After a load, the mod uses the stored result. A save without a stored result uses a live check.
- No banner at game start. The warning shows only in the existing mod start menu.
- Removed from the first plan: the `hussites_enabled` setting, the lock of the Yearly player raid, Great raid and Vassal raids levels, and the mapping of the off-map adversary field. `hussites_enabled` is not kept, not even as information: no requirement uses it.

### Dependency map (owner requirement 2026-10-23, updated 2026-10-24)

| Game setting off | Mod part that breaks | Result | Status |
|---|---|---|---|
| Bandit camps: initial 0 and limit 0 | None. The mod makes the bandit pawn itself (change `update-banditry-bandit-camp`) | No lock, no warning | Decided 2026-10-23 |
| AI opponents 0 (`numGenericAILords`) | Vassals are not enabled | Warn only in the menu: "vassals are not enabled". No lock | Decided 2026-10-23 |
| Off map adversary absent | None. Hussite raids are mod-made AI lord armies (spike #430) | No lock, no warning | Decided 2026-10-24 |

### Size of the guard

The guard is now very small: one setting (`vassals`), one warning and one live check for old saves. Nothing is locked. The owner may want to fold it into the vassals feature instead of keeping it as a separate guard. This change keeps it separate until the owner decides.

## Open questions (with defaults)

- Start banner: none (owner decision 2026-10-23). The warning shows only in the mod start menu.

## Impact

- Specs: `mod/scenario_settings` (ADDED requirements). Edited by change `update-banditry-bandit-camp`: no banditry lock.
- Code: `mod/shared/HarnessGameSetup`, the scenario_settings feature (menu warning, ModState); the vassals feature reads the guard.
- No change to the game files.
