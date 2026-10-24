# Question 2: AI lord and construction with AI opponents 0

Run `noai-h-175358` (hold run, slot 1, speed 3). Fixture `playtest-noai`. Evidence: `evidence/q2-ai-village-goldhof.jpg`.

## Verdict

**Yes.** The mod can make an AI lord, give it a region, and the lord then builds the village by itself, also with AI opponents 0. Only the full claim path makes the lord build. Writing `region.ownerPawn` alone does not.

## Numbers

| Step | Result |
|---|---|
| `lords_state` in the fixture | 0 lords. `settings`: `spawn_ai_players=false`, `ai_can_build=true`. No baron (`adversary_baron=false`). |
| `spawn_ai_lord name="Probe Baron" build=1` | `RTSMultiEngineCPP:spawnNewAILord`: lord 1, `lords_before 0`, `lords_after 1`. |
| `lord_relations 1`, `lord_start_ai 1 speed=1 build=1` | relation row made (`relations_before 0 after 1`); `startAI` accepted. |
| `lord_take_region 1 hofstetten` (write `ownerPawn`) | owner changed. Buildings 0, families 0 for the whole watch (about 55 game days). No `AI_build` line for this region. |
| `lord_found_village 1 Goldhof type=1 supply=2` (claim, then `settleRegion`) | steps `claim`, `settle`: 4 buildings, 5 families at once. |
| watch at speed 3, polled every 15 s | Goldhof buildings: 4 (day 180), 7 (183), 10 (186), 13 (189), 14 (211), 16 (215), 19 (247), 21 (266). Families 5 to 8. The construction log has `AI_build: LoggingCamp, HitchingPost, Marketplace, BurgagePlotTool, Well_Lv1, Storehouse_Lv1, TradingPost, Sawpit` and `AI_upgrade: BurgageExpansion, OrderHorse`. |
| construction log | 25 `debugLog_AI_construction` lines in about 85 game days; 12 lines in the first 20 game days (inside the 10 to 15 range of spike S13). |

(`day` in the poll log is the day of the year; the calendar shows Jun 26 at the start and Sep 22 at the end, so about 85 game days.)

## Details

- The first 9 game days were the fastest build (4 to 13 buildings). Later growth is slow (settlement runs out of silver: the lord has `silver 0`). It built with silver 0 from the start supply (`supply=2`).
- `lord_receive_region` (clear owner, then claim) was not repeated here. It is the route for a region that already has buildings (`add-vassal-sack-wipe`).
- Spawning a lord needs no setting. "AI opponents 0" only means that the game does not create lords at the start; `spawnNewAILord` still works.
- The lord's `influence` rose to 100 by itself during the watch ("claimRegions: not enough influence" lines).
- Picture: the AI village Hochweg (region Goldhof) at the end, with houses, a workshop and a market stall area.

## Recommendation

The mod can use its own AI lords in a world with AI opponents 0. For a vassal that must build, use `spawn_ai_lord` + `lord_relations` + `lord_start_ai(build)` + a full claim (`lord_found_village` for a free region, `lord_receive_region` for a ruined or settled one). Do not rely on `ownerPawn` writes. No game setting is needed.

## Not verified

- Whether the lord and village survive a save and a load.
- Behaviour over a game year, or with several lords at once.
- The wiped-region case in this world (`add-vassal-sack-wipe` tested it in the base fixture).
