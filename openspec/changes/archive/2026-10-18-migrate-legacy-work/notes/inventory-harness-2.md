# Inventory: harness specs 14 to 18, 25 to 26, 28 to 32, 34 (group LH2)

Date: 2026-10-18. Legacy files are not changed. Issue state read with `gh api` (the `gh issue view` call fails on the classic projects notice).
Change names: all `x-issue: TBD`, all `skip_specs: true` (no delta spec yet), all pass `openspec validate <name> --strict`.

| Legacy item | Verdict | Change name or reason | Open issue | Spec gap |
|---|---|---|---|---|
| 14 README, acceptance 3 (builders finish a free wall, units blocked) | CONVERT | `spike-blocking-wall-route` | #52 | no |
| 14 `free-walls.md` "Where this leaves free walls": leads not tried (planner functions, path grid, slow-at-wall rule) | CONVERT | `spike-blocking-wall-route` | #52 | no |
| 14 Q5 (offer the wall tool to the player) and Q6 (save and load) | CONVERT | `spike-blocking-wall-route` (tasks 3.x, 4.1) | #52 | no |
| 14 partial breach (no call removes one piece) | CONVERT | `spike-blocking-wall-route` task 2.4 | #52 | no |
| 14 issue #52 "decide which commands and memory tools stay in git" | DONE | Unsafe commands are behind a setting in `harness/building-commands` ("Unsafe spike commands need an explicit game setting") | #52 | no |
| 14 issue #52 "place a tax office through the planner" | DONE | Done live 2026-10-12 (`free-walls.md` "Tax office through the manor planner", issue #63 closed); `manor_blueprint_add` is in `harness/manor-commands` | #63 closed | no |
| 14 wall commands, fake tests, CHANGELOG | DONE | `harness/building-commands` (wall_state, wall_make, wall_pieces, path_state, building_health) | #52 | no |
| 14 `os-mouse-regression.md` (issue #115) | DONE | Fixed (`check_mouse_present`); issue #115 closed | #115 closed | no |
| 15 README "Feature: refugee waves", feature plan, feature criteria | DONE | Built in the Invasion Mod as `mod/refugees` (living spec). The standalone mod `RefugeeWaves` was removed (README line 80 to 100 plan is obsolete) | #51, #61 closed | no |
| 15 reverse direction (`homeless_rebel`, rally in the woods, `rebel_raid_rally`) | DONE | `harness/settlement-commands` and `mod/bandits` ("Unhoused refugees turn into bandits" in `mod/refugees`) | #51 closed | no |
| 15 open: choose the rally point, why `spawnArmy` squads give no family | DROP | Raiders cannot be steered: feasibility decision 1 (`openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/implementation-notes/feasibility-summary.md`, "Design changes needed" row 1) | none | no |
| 15 open: `family_add` crash (0x3c1), `turnToBandit` crash cause | DROP | Do not use; `settle_region` and `homeless_rebel` replace them (README "Not usable" table row; `settlement-commands` spec says families can be added) | none | no |
| 15 open: tent placement without the mouse, tent slot writes | DROP | Done as "not possible" (`tent-slot-limit.md`, `tent-placement.md`); the mod uses `settleRegion` for tents | none | no |
| 15 open: whole-family add, third `settle_region`, bad plot ground | DROP | Not needed by `mod/refugees` (waves in steps of 5 with `settleRegion`) | none | no |
| 15 acceptance 2 (settle letter: no scenario yet) | DONE | `mod/InvasionMod/scenarios/bandits/buy_back.py` and `convert_families.py` cover the letter and the conversion | #51 closed | no |
| 16 README, `policies.md`, `policy_state`, `policy_enact`, `policy_sign` | DONE | `harness/policy-commands` | #55, #60 closed | no |
| 16 pak widget plan, PolicyMenu 0.1.0 release, menu follow-ups, click wiring | DROP | Mod `PolicyMenu` was removed (change `remove-standalone-test-mods`); laws and vassal policies are mod-owned (M00 README line 144) | #60 closed | no |
| 16 open: Strict fasting effect, why `enactPolicy` returns false | DROP | M00 decision 2: the game policy system is not used (`enactPolicy` false in 95 tries). No Invasion Mod feature needs it | #60 closed | no |
| 17 README Q1 to Q4, gate-free ring test, flag toggles, fold-or-continue decision | CONVERT | `spike-bailey-buildings` | #68 | no |
| 18 build menu card for a new id (acceptance, last box) | CONVERT | `spike-composite-building-gaps` | #69 closed | no |
| 18 Siege Camp (483) has no build path; leads not tried (`siege-camp-build.md`, `hidden-buildings.md` "How to test") | CONVERT | `spike-composite-building-gaps` task 3.1 (only if the owner wants it) | #94 closed | no |
| 18 #104 goals 1 and 2 (inspect hitching post and small stable, find what sets capacity) | DONE | `access-points.md`: capacity is the row field `stableSpace`; entry and delivery points are `gathering`, `workpos`, `res_<good>_<n>`. Hitch spots are native | #104 | no |
| 18 #104 goal 3 (large stable with 4 oxen, pak, placed by click) | DONE | Row 125 and pak `stable4_P.pak` (in git): placed with a real click, built, `stableMax` 4, 4 oxen housed (`real-mouse-placement-proof.md`). The 4 oxen are not seen at rest spots: the owner stopped the hitch tests on 2026-10-15 | #104 | no |
| 18 #104 leftovers: scenario for row 125 without `--keep-open`, `order_oxen` adds one ox, where idle oxen stand | CONVERT | `spike-composite-building-gaps` tasks 4.x | #104 | no |
| 18 hitch spots per ox (native) | DROP | Owner decision 2026-10-15 in the spec 18 README ("Decision: ox hitch spots") | #104 | no |
| 18 pak, part edit, mouse-free placement, blueprint route notes | DONE | `harness/building-commands` (`master_parts`, `load_pak_blueprint`), `harness/pak-mods`. Mouse-free placement was not achieved (`mousefree-placement.md`) and is not planned | #69 closed | no |
| 25 A1 to A3 (levers, A/B, recommendation) | DONE | `ab-results.md`; lever used in `mod/unit_balance` (unarmored lethality, armored att and armorPierce factors) | #129 closed | no |
| 25 open: live write of att and armorPierce on militia, pak equipment route | DONE | `mod/unit_balance` writes att and armorPierce for armored units. The pak equipment route is not needed | #129 closed | no |
| 26 A1 to A3 | DONE | `claim-victory-test.md`; `harness/game-setup` and the scenario `mod/InvasionMod/scenarios/vassals/claim_without_victory.py` | #130 closed | no |
| 26 plundered start (A3: Lua after the start) | DONE | Moved to the mod design M14 and the change `add-plundered-start` (other group) | #130 closed | no |
| 26 `start-settings.md` section 8 open questions (which code reads `goals`, preset rows, ruins fields) | DROP | The claim test answered the use case; the rest is research with no user (`start-settings.md` section 5 says no start setting gives ruins) | none | no |
| 28 README (unit tuning, A1 to A6, restart a session) | DONE | `harness/unit-tuning` (all seven requirements). The session runbook belongs in the wiki | #138 closed | no |
| 29 Part A hand cannon (recruit card, gun look, speed and range split) | DROP | M00 decision 7: no handgunners (`design/invasion-mod.md` line 284). `recommendation-for-m00.md` "Next steps" are conditional on the design | #178 closed | no |
| 29 Part B war wagon | DROP | Same file: war wagons stay out of version 1; stand-in squad only | #178 closed | no |
| 29 notes and A/B results | DONE | `harness/combat-commands` carries the commands; results stay in legacy notes | #178 closed | no |
| 30 README (host a, b, c; open: host b mouse run, bandits stuck in ring, mixed camps, grey look, respawn on load, license) | CONVERT | `spike-wagenburg-bandit-camp` (decision by the owner first) | #229 | no |
| 30 `encampment_*` commands | DONE | `harness/encampment-commands` | #229 | no |
| 31 README (open: plot panel text and icon, save and load, several plots, texture, owner check) | CONVERT | `spike-weaver-extension-shipping` (decision by the owner first) | #230 | no |
| 31 new extension number | DROP | Not possible with data (`new-extension-number.md`); the README says do not plan for it | #230 | no |
| 31 spike commands (`master_artisan`, `plot_upgrade`) | DONE | `harness/building-commands` | #230 | no |
| 32 README (open: AI manor study, rebuild and load, closed gate and damage, models, license) | CONVERT | `spike-wagenburg-manor-reskin` (decision by the owner first) | #233 | no |
| 32 `mesh_actors`, `wagen_*` | DONE | `harness/building-commands`, `harness/manor-commands` (the `wagen_*` scenarios are "Not checked yet") | #233 | no |
| 34 README results and acceptance criteria | DONE | Code: `mod/shared/HarnessClickHooks`; scenarios `tech_tree/widget_clicks.py`, `widget.py`, `invasion/raid_widget.py`. PR #267 fixes `mod/core`, `mod/tech_tree_widget`, `mod/raid_widget` | #254 closed | yes: `HarnessClickHooks` (attach, bind_texts, set_text, set_visible, drain, release) is in no living spec and not in the wiki (only in the skill `harness-pak-mod`) |
| 34 acceptance 3 (menu open 5 minutes, run `20261018-173614-d910`) | CONVERT | `add-menu-stay-open-scenario` | #254 closed | yes: "A menu stays open" is "Not checked yet" in #267 |
| 34 open: click button source has compile errors in its graph | CONVERT | `add-menu-stay-open-scenario` task 2.1 | #254 closed | no |
| 34 PolicyMenu port, `policy-menu-clicks` runs | DROP | PolicyMenu was removed | #254 closed | no |
| Folders above 33 | none | `ls docs/harness` shows 00 to 34 only; 33 (Meshy materials) is outside this scope | | |

## Counts

- Rows: 46 (plus one note row). CONVERT 13 (7 change folders). DONE 21. DROP 12.
- Change folders: `spike-blocking-wall-route`, `spike-bailey-buildings`, `spike-composite-building-gaps`, `spike-wagenburg-bandit-camp`, `spike-weaver-extension-shipping`, `spike-wagenburg-manor-reskin`, `add-menu-stay-open-scenario`.

## Doubts

- Changes 30, 31 and 32 wait for an owner decision. They have no delta spec yet, because the shipped behavior would be game design for the Invasion Mod. A delta spec is a task after the decision.
- #104 stays open on GitHub, but the owner stopped the hitch tests on 2026-10-15. The goal "screenshot 4 oxen in it" was not met. The leftovers are in `spike-composite-building-gaps`. The lead may close #104 instead.
- The spec 15 README is large. I did not read all of `homeless-rebellion.md` (33 KB). I relied on the README and the living spec `harness/settlement-commands`.
- The grey Meshy look is said to be fixed by spec 33. The three Wagenburg changes include a picture check.
- Capability for `HarnessClickHooks` is the lead's choice (see `add-menu-stay-open-scenario/proposal.md`).
