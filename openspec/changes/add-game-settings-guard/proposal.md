## Why

Issue: #438. The Invasion Mod needs three game parts: bandit camps, the off-map AI (Off Map Adversary) and AI lords (AI Opponents). The player can switch each one off in the New Game settings of the game. The mod then offers raid settings that cannot work, and the player does not know why.

## What Changes

- At new game start, the mod reads the game setup and stores a guard result in ModState: which of the three parts are off.
- In the scenario settings menu, each mod setting that depends on an off part is set to 0 (off) and locked. The player cannot raise it.
- Next to a locked value, the menu shows a warning, for example "Locked: this game was started with bandit camps off".
- After a load, the mod uses the stored result. A save without a stored result uses a live check.

### Dependency map (owner requirement 2026-10-23)

| Game setting off | Mod part that breaks | Proposed default | Status |
|---|---|---|---|
| Bandit camps: initial 0 and limit 0 | Banditry bands (feature `bandits`) cannot spawn | The menu has no banditry setting: show the warning only. Lock one if a setting exists later | To confirm by spike #430 / #416 |
| AI opponents 0 (`numGenericAILords`) | Vassals and vassal raids have no lords; sack rebuild needs AI lords | Lock "Vassal raids" to 0 and warn | To confirm by spike #430 / #416 |
| Off map adversary absent (field `adversary_baron` or other, see spike) | Unknown whether Hussite raids still spawn | Warn only. Lock Yearly player raid and Great raid only if the spike shows them broken | To confirm by spike #430 / #416 |

The menu rows come from change `update-raid-difficulty-levels` (#404, PR #435): Yearly player raid, Great raid, Vassal raids, First Hussite raid and Raid size.

## Open questions (with defaults)

- Show a banner at game start that lists the switched-off parts? Default: yes.
- Can a locked row be unlocked later in the same game? Default: no, never.
- Which game field means "Off Map Adversary"? Default: the spike finds it (`adversary_baron` is the candidate).

## Impact

- Specs: `mod/scenario_settings` (ADDED requirements).
- Code: `mod/shared/HarnessGameSetup`, the scenario_settings feature (menu, ModState); the bandits and vassals features read the guard.
- No change to the game files.
