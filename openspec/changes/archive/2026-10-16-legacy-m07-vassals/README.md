# M07: vassals

Feature folder: `vassals`. Batch 4.

## Goal
The player vassalizes a nearby neighbor or founds a vassal region with settlers. The player rules a vassal only through policies and orders.

## Player rules (from M00)
- Two ways to gain a vassal: vassalize a nearby neighbor, or send settlers to found a region. A settled region starts under the player's full control.
- Indirect control: policies and orders only. No direct building in a vassal region.
- Policies and orders are mod-owned settings. Lua applies their effects.
- Loyalty is a mod-owned value.
- Vassals send supplies (tribute: M08). They expect protection from the empire and from bandits.
- The empire raids vassals first. A lost vassal cuts tribute and sends refugees (M09).
- An unprotected vassal may submit and pay tribute to the invader.
- A fortified vassal can become the fallback capital (M06).
- No scouting and no intel in version 1.

## Current state
Iterations 01 and 02 are done. The mod holds goals = Endless, keeps a 3 slot registry with loyalty in the pawn Tags, and hands a player-settled region to a new friendly AI lord. Finding: the lord declares war by itself (the mod declares peace), and it builds only when the region has 4 buildings after the settle call (flagged `stalled` otherwise). Iteration 03 is next.

## Proven building blocks
- Claim, settle and hand over a region as an AI-lord region: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/dynamic-lords.md`, `baron-model.md`. A rerun on 2026-10-13 saw no lord build on the base fixture.
- Goals = Endless (2) on `MLGameInstance` stops the victory cinematic on a claim, 3 of 3: `openspec/changes/archive/2026-10-15-legacy-26-game-start-settings/implementation-notes/claim-victory-test.md`, `start-settings.md`.
- The victory problem before the fix: `openspec/changes/archive/2026-10-15-legacy-15-bandit-settlement/implementation-notes/settler-camp.md`.
- Policy effects are native and `enactPolicy` returned false in 95 tries, so vassal policies are mod-owned: `openspec/changes/archive/2026-10-15-legacy-16-policy-edicts/implementation-notes/policy-followups.md`.
- Review: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-vassals.md`.
- Mod state with region Tags: M01.

## Tunables (M00)
- Loyalty start value, loss and gain rates (M00 gives no numbers).
- Number of vassals (2 or 3 in the middle game).

## Dependencies
- M01 mod-state. Spec 26 (goals = Endless; set before the first claim, in every game).
- Feeds M08, M09, M10, M11, M12.

## Open questions
1. How are vassal regions shown: AI lord regions, player regions with locked building, or an abstract layer in Lua only? (M00 open question 3.)
2. Which effects can Lua apply to a region the player does not control? (M00 open question 4.)
3. What does a lost vassal's land become: enemy region, bandit camp, or free land? (M00 open question 8.)
4. How does the player vassalize a neighbor: by claim, or by an order and a payment? M00 does not say.
5. Does Lua set goals = Endless on every start and every load, or only at the first claim?
6. Can the AI lord of a vassal region grow without a build? (Open from the 2026-10-13 rerun.)
7. Answered (decision 1): survive the great raid waves until the relief army arrives, then the very large battle. Endless stops the claim victory; the win is this mod rule (M02, M06).
8. Vassal model (decision 5): still open. It is being explained to the user.

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | claim-without-victory | Set goals = Endless and claim one region as a vassal, with loyalty in region Tags. | done, PASS (#187) |
| 02 | settled-vassal | Found a vassal with settlers. | done, PASS with findings (#191) |
| 03 | policies-and-orders | Mod-owned policies applied to a vassal. | done, PASS (#209) |
| 04 | loss-and-submission | Lose or submit a vassal. | done, PASS (#212) |

## Decisions (2026-10-16, M00 items 20 and 21)
- Model A. No vassals at the start. The player settles a region; the game hands it to a friendly AI lord who rules in the player name.
- Watch in playtests whether the AI lord declares war.
- First spike: does a handed-over AI lord grow reliably?
