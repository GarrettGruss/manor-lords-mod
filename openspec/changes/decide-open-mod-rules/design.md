# Design: Decide the open mod rules

## Open decisions (the owner decides)

| # | Item | Legacy source | Question | Note |
|---|---|---|---|---|
| 1 | Season weights for raids; the winter raid rule | `M02-invasion/README.md`, `iterations/02-great-raid-clock.md` | Which weights per season, and are winter raids allowed? | Marked TBD. M00 balance. |
| 2 | Terms buttons and a start screen in the raid widget | `M02-invasion/iterations/05-raid-widget.md` | Do players need UI for the terms and the start? | Terms are named commands today. |
| 3 | Loss of the final battle of the great raid | `M02-invasion/README.md`, `M06-sack_and_terms/README.md` | What happens when the player loses it? | M00 decision 27 is TBD. |
| 4 | Terms after a sack; effect of vassalage on later raids; moving the best units and removing home families on a capital move | `M06-sack_and_terms/README.md` | Which of these are wanted? | Some depend on engine facts (legacy spikes S8, S11). |
| 5 | A vassal pays tribute to the invader; loss by `take_by_lord` | `M07-vassals/iterations/04-loss-and-submission.md` | Keep the first as a rule? The second crashes the game today. | Only a flag exists. |
| 6 | Tribute for influence | `M08-tribute/README.md` | Wanted? | Follows `add-liege-influence`. |
| 7 | Iron mine test; measured use rate for the 2 to 4 year target; a stock the player sees; clay from vassals; AI lords | `M10-finite_resources/iterations/01`, `02` | Which to measure or build? | Tuning-only items need no change folder. |
| 8 | A UI for the bandit buy-back | `M04-bandits/iterations/03-coin-buy-back.md` (README open question 6) | Diplomacy entry, a button, or none? | The command is built. |
| 9 | Raiders treat the manor store differently | `M13-manor_stronghold/README.md` | None. | Covered by `add-raid-storage-tiers`. |

## Open questions of the archived M00 design (added 2026-10-18)

The change `split-design-brief` moved the M00 open questions to the archive (`openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/README.md`, "Open questions"). These are not answered yet:

| # | Item | M00 question | Question |
|---|---|---|---|
| 10 | Effects on a region the player does not control | 4 (open part) | Which effects may Lua apply to an AI lord's region? |
| 11 | The land of a lost vassal | 8 | Does it become an enemy region, a bandit camp, or empty land that can be retaken? |
| 12 | A second invader faction | 12 | Is a mercenary free company (linked to the bandits) needed for the first release? |

The other M00 questions are answered by decisions (`design/decisions.md`), built (living specs), or are open changes (`add-plundered-start`, `add-liege-influence`).
