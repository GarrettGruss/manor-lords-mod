# Inventory: Invasion Mod legacy work (group LM)

Date: 2026-10-18. Scope: `docs/mod/M01-*` to `M14-*`. M00 was read only.
Verdicts: CONVERT (a change folder), DONE (built on main), DROP (obsolete), NOTED (a loose open item with no legacy iteration; no change, listed so it is not lost).
Issue column: an existing GitHub issue, if any.

## Planned or open work

| Legacy file | Verdict | Change name or reason | Issue | Spec gap |
|---|---|---|---|---|
| `M01-mod_state/README.md` row 02 region-state-and-limits (no iteration file) | CONVERT | `add-mod-state-region-tags` | none | no |
| `M03-raid_behavior/README.md` row 02b loot-back-to-store | DONE | Built in M03.01 (`openspec/specs/mod/raid_behavior` requirement "The loot of a dead raider goes to the nearest store"; scenario `raid_behavior/loot_return.py`). The README row is out of date. | none | no |
| `M03-raid_behavior/README.md` row 03 carry-caps | CONVERT | `add-raid-carry-caps` (modifies "Loot is capped per raider") | none | no |
| `M03-raid_behavior/README.md` row 04 storage-tiers (with ruin rebuild discount) | CONVERT | `add-raid-storage-tiers` | none | no |
| `M05-unit_balance/iterations/04-counters-veterancy.md` (shield and pavise counter against crossbows) | DROP | The file Result says there is no stat lever. The pike bonus and veterancy are built. Archers are native. | none | no |
| `M11-liege_influence/README.md` row 01 influence-balance | CONVERT | `add-liege-influence` (backlog, M00 decision 9) | none | no |
| `M11-liege_influence/README.md` rows 02 spend-influence, 03 military-aid | NOTED | Later steps. Listed as non-goals of `add-liege-influence`. | none | no |
| `M12-tech_tree/iterations/02-pak-ui.md` (U5, U6 real mouse clicks) | DONE | Spec 34 (`docs/harness/34-widget-click-hooks/README.md`, Evidence) made clicks hook events. Scenario `tech_tree/widget_clicks.py` (10 of 10 clicks, runs `20261018-180342-674d`, `20261018-180458-603f`) and `tech_tree/widget.py` (`20261018-180609-de2e`) pass. Nothing is open. Issue #203 can close. `05-laws-menu.md` line "Real clicks: open (#203)" is covered by the same runs. | #203 (in progress) | yes: `openspec/specs/mod/tech_tree_widget/spec.md` requirement "Mouse clicks on the buttons" describes the old poll and `click_cooldown_s`, and its scenario says "Not checked yet". It should name the click hook and `widget_clicks.py`. |
| `M14-plundered_start/README.md` row 01 start-sack | CONVERT | `add-plundered-start` (backlog, M00 decision 25) | none | no |

## Iterations that are built (no work left)

| Legacy file | Verdict | Reason | Issue | Spec gap |
|---|---|---|---|---|
| `M01-mod_state/iterations/01-tags-module.md`, `feedback.md` | DONE | Living spec `mod/mod_state`. Feedback: none yet. | #142 | no |
| `M02-invasion/iterations/01` to `07` (first raid, great raid clock, subjugation raid, difficulty, raid widget, great raid waves, vassal targets), `feedback.md` | DONE | Living specs `mod/invasion`, `mod/raid_widget`. Feedback: none yet. | #143, #171, #177, #175, #189, #186, #220 | no |
| `M03-raid_behavior/iterations/01`, `02`, `feedback.md` | DONE | Living spec `mod/raid_behavior`. Feedback: none yet. | #144, #168 | no |
| `M04-bandits/iterations/01`, `02`, `03` | DONE | Living spec `mod/bandits`. | #155, #161, #167 | no |
| `M05-unit_balance/iterations/01`, `02`, `03` | DONE | Living specs `mod/unit_balance`, `mod/invasion` (roles). | #156, #162, none | no |
| `M05-unit_balance/iterations/04-counters-veterancy.md` (veterancy, pike bonus) | DONE | Built and passed. The open part is the DROP row above. | none | no |
| `M06-sack_and_terms/iterations/01` to `04` | DONE | Living spec `mod/sack_and_terms`. | #173, #181, #205, #224 | no |
| `M07-vassals/iterations/01` to `04` | DONE | Living spec `mod/vassals`. | #187, #191, #209, #212 | no |
| `M08-tribute/iterations/01`, `02` | DONE | Living spec `mod/tribute`. | #197, #214 | no |
| `M09-refugees/iterations/01`, `02` | DONE | Living spec `mod/refugees`. | #200, #202 | no |
| `M10-finite_resources/iterations/01`, `02` | DONE | Living spec `mod/finite_resources`. | #222, #226 | no |
| `M12-tech_tree/iterations/01`, `04`, `05` (README row 03 first-nodes is part of 01) | DONE | Living specs `mod/tech_tree`, `mod/tech_tree_widget`. | #195, #217, #236 | no |
| `M13-manor_stronghold/iterations/01`, `02`, `03` | DONE | Living spec `mod/manor_stronghold`. The mod-owned hire path that `02` leaves open is built in `03` (extra retinue squads). | #207, none, #215 | no |

## Loose open items (no legacy iteration, no change)

| Source | Item | Verdict | Reason |
|---|---|---|---|
| `M02-invasion/README.md`, `iterations/02` | Season weights; winter raid rule | NOTED | Marked TBD. Not built. Needs a user decision on the weights (M00 balance). |
| `M02-invasion/iterations/05-raid-widget.md` | Terms buttons and a start screen in the widget | NOTED | Terms stay named commands. The user has not asked for the UI. |
| `M02-invasion/README.md`, `M06-sack_and_terms/README.md` | Loss of the great raid's final battle | NOTED | M00 decision 27: TBD, no rule. |
| `M06-sack_and_terms/README.md` | Terms after a sack; effect of vassalage on later raids; move best units and remove home families on a capital move | NOTED | Listed as "not here" in the iteration files. Some are blocked by engine facts (spike S8, S11). |
| `M07-vassals/iterations/04-loss-and-submission.md` | Vassal pays tribute to the invader; `take_by_lord` loss (crashes) | NOTED | Only a flag exists. The crash blocks the second. |
| `M08-tribute/README.md` | Tribute for influence | NOTED | Follows `add-liege-influence` (needs a user decision). |
| `M10-finite_resources/iterations/01`, `02` | Real iron mine test; measured use rate for the 2 to 4 year target; player-visible stock; clay supply by vassals; AI lords | NOTED | Measurement and tuning items. A tuning-only change needs no change folder (process spec). The UI item needs the user. |
| `M04-bandits/iterations/03-coin-buy-back.md` | A UI for the buy-back (diplomacy entry or button) | NOTED | The command is built. The UI needs a user decision (README open question 6). |
| `M13-manor_stronghold/README.md` | Raiders treat the manor store differently | NOTED | Covered by `add-raid-storage-tiers`. |

## Counts

- CONVERT: 5 (`add-mod-state-region-tags`, `add-raid-carry-caps`, `add-raid-storage-tiers`, `add-liege-influence`, `add-plundered-start`).
- DONE: 13 groups of built iterations, plus M03 row 02b and M12.02. DROP: 1 (M05.04 shield counter). NOTED: 9 loose items.
- Spec gaps: 1 (`mod/tech_tree_widget`, mouse clicks).
