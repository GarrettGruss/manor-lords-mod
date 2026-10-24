## Why

Issue: #438. The Invasion Mod needs three game parts: bandit camps, the off-map AI (Off Map Adversary) and AI lords (AI Opponents). The player can switch each one off in the New Game settings of the game. The mod then offers raid settings that cannot work, and the player does not know why.

## What Changes

- At new game start, the mod reads the game setup once and saves three mod settings in ModState: `vassals` (true/false), `villager_banditry` (true/false) and `hussites_enabled` (true/false).
- In the scenario settings menu, each mod setting that depends on an off part is set to 0 (off) and locked. The player cannot raise it.
- Next to a locked value, the menu shows a warning, for example "Locked: this game was started with bandit camps off".
- After a load, the mod uses the stored result. A save without a stored result uses a live check.
- No banner at game start. The warnings show only in the existing mod start menu.

### Dependency map (owner requirement 2026-10-23)

| Game setting off | Mod part that breaks | Proposed default | Status |
|---|---|---|---|
| Bandit camps: initial 0 and limit 0 | Villager banditry (no bandit pawn, confirmed in playtest-noai) | Disable the banditry timer and leave. The menu shows a warning line. No menu row to lock | Confirmed in playtest-noai; spike#430 / #416 may add detail |
| AI opponents 0 (`numGenericAILords`) | Vassals are not enabled | Warn only in the menu: "vassals are not enabled". No lock | Owner decision 2026-10-23 |
| Off map adversary absent (field `adversary_baron` or other, see spike) | Hussite raids do not work | Set Yearly player raid, Great raid and Vassal raids to 0, lock them and warn. Vassal raids are Hussite raids in the code (the subjugation raid is a lord raid of the mod, `invasion/init.lua`) | Lock rule decided. A task confirms in playtest-noai (spike #430 Q3) |

The menu rows come from change `update-raid-difficulty-levels` (#404, PR #435): Yearly player raid, Great raid, Vassal raids, First Hussite raid and Raid size.

## Open questions (with defaults)

- Start banner: none (owner decision 2026-10-23). Warnings show only in the mod start menu.
- Can a locked row be unlocked later in the same game? Default: no, never.
- Which game field means "Off Map Adversary"? Default: the spike finds it (`adversary_baron` is the candidate).

## Impact

- Specs: `mod/scenario_settings` (ADDED requirements).
- Code: `mod/shared/HarnessGameSetup`, the scenario_settings feature (menu, ModState); the bandits and vassals features read the guard.
- No change to the game files.
