## Why

Issue: #453. Owner decision 2026-10-23. Villager banditry spawns Brigands squads inside the village at the homes of the families that left. The owner wants the families to go to a bandit camp. Spike #430 proved that `RTSMultiEngineCPP:spawnBanditCamp()` makes the bandit pawn "Outlaws" (when missing) and a camp with 18 Brigands, also with the game camp settings at 0 (`openspec/changes/archive/2026-10-23-spike-playtest-world-ai/notes/bandit-camps.md`).

## What Changes

- When families leave for banditry, the mod spawns one bandit camp (`spawnBanditCamp`) instead of squads at the homes. The leave count stays (default 18 families) and the families still leave.
- The mod makes the bandit pawn itself when none exists (one `spawnBanditCamp` call), then calls `addPawnRelations` for it. Villager banditry then works with the game setting bandit camps 0. This replaces the "no bandit pawn: no bandits spawn" rule.
- The rule "one squad per 5 families" is removed. Default: one camp per leave event, and the camp has its own 18 Brigands (owner question 1).
- The game picks the camp place. `spawnBanditCamp` has no position argument. The change records where the camp appears and its distance from the village (task 1.2). The mod does not move the camp (owner question 2).
- Change `add-game-settings-guard` (edited in this pull request): `villager_banditry` no longer becomes false from camps 0. The lock, the warning line and the disabled banditry timer are removed from that change.

## Open questions (with defaults)

1. The squads-per-5-families rule. Default: removed. One camp per leave event, 18 Brigands from the camp, whatever the number of families.
2. Camp position. Default: the game picks it. If the camp appears near the village, a follow-up change can try to place it at a border point.
3. Leave events at short intervals make many camps. Default: no cap now. The spike saw a crash with 3 camps at once and killed squads; it is unproven-safe.

## Impact

- Specs: `mod/bandits` (MODIFIED). `mod/scenario_settings` through the unmerged change `add-game-settings-guard` (edited here).
- Code: `mod/InvasionMod/Scripts/features/bandits/world.lua` (`M.leave`), `config.lua` (`families_per_squad` removed from bandits; refugees keep their own), tests and a test scenario.
- Overlap: the open change `update-spawn-from-map-border` modifies the same requirement for the border arrival of conversion squads. Its banditry part no longer applies once camps replace squads. Its owner must rebase it onto this change (its banditry requirement and scenarios are dropped).
- Game risk: many camps may crash the game (spike #430 note). No save function is used.
