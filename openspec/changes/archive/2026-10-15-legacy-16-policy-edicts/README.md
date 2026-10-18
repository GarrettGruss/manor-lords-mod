# Spec 16: Policy edicts

Status: spike done for Q1 to Q5 (2026-10-12). Policies exist (19 rows, 6 available); enactPolicy returned false; setPolicySigned works but showed no effect; a Lua screen with a game policy card works. Notes: `implementation-notes/policies.md` and `implementation-notes/policy-menu.md`.

Decision (user, 2026-10-13): menu option c, a pak widget. Acceptance criteria: the custom menu is created in the game, and a screenshot captures it.
Plan: `implementation-notes/pak-widget-plan.md`. The UE 5.5 editor is required and is not installed. Status: blocked until the user installs UE 5.5.4.

Earlier decision (user, 2026-10-12): menu option b (Lua screen with game policy cards) or c (pak widget) were both acceptable. The spike branch is
finished; open follow-ups: the effect of Strict fasting (12) during a food shortage, a real click on a Lua-placed card, why `enactPolicy` returns false.

Follow-ups (issue #60, 2026-10-12, notes in `implementation-notes/policy-followups.md`):
- Strict fasting: no measurable effect on food use or approval in the base village (food use is about 0 there, so the test has no power). Open.
- A real click on a Lua-placed game policy card works. It calls `Region:setPolicySigned(id, true)`, not `enactPolicy`.
- `enactPolicy` still returns false for 95 slot and id combinations, with silver, influence, level and `availablePolicies` changed. The condition is not found.
- Menu choice (b or c): still the user's decision. Evidence favors b as the first step (see the note).

Tracking issues: #55, #60

## Goal
Find out if the base game has a policy system, so that the player (or the mod) can enact a temporary edict such as rationing at a cost
in approval, and if the mod can show its own menu for policies.

## Why
- The user asked: does the game have policies? Can the player enact a temporary edict like rationing, at a cost in approval? Can the mod show a
  custom policy menu?
- Offline lead from the jmap: `PawnCPP:enactPolicy(Region, slotNo, policyID)`, `Region.policies`, `Region.policiesSigned`,
  `Region:getMaxPolicies`, the DataTable `DT_PolicyTypes` (19 rows), and the widgets `policyWidget_C` and `developmentPanelTree_C`.
- The row "Strict fasting" (id 12) says: "Citizens skip every 5th meal. Reduces food consumption, decreases approval." This is rationing.

## Non-goals
- New game assets in git. Pak builds or installs in this spike.
- A permanent balance change of the base game.
- Calling any save function. Changing the user's saves.
- Writing game memory, or DataTable writes in the live game (this spike).

## Questions
- Q1: Which policies exist, and where are they defined (DataTable or code)? What do they cost, and what do they do?
- Q2: What can the mod read live: available policies, active policies, signed state, slots, approval and its factors, development points?
- Q3: Does `enactPolicy` work from a named command? What changes (policies, approval, silver, development points)? Can a policy be removed again by a game call?
- Q4: Is there a policy close to rationing? Can food use per family be changed? Can a temporary approval effect be added? What would need a pak mod?
- Q5: How can a mod show a policy menu: (a) the game's own panel, (b) a widget made from Lua with buttons, (c) a pak widget?

## Plan
1. Offline: list the classes, structs, enums and functions about policies, approval and food use (jmap). Read `DT_PolicyTypes` and its
   translation table from the pak (JSON under `runs/`, never in git).
2. Read-only live command `policy_state` in the new module `HarnessPolicies`, with a Python action and fake game tests.
3. Enact test on fixture `base`: one `enactPolicy` call, read the change over a few game days, then try to remove it by a game call.
   If a game call can do it, add `policy_enact` (game calls only).
4. Rationing: check what the mod can do today, and what needs a pak row.
5. Menu: study the three options. Test only (b) in the live game, if cheap.

## Open questions
- Does `enactPolicy` charge anything (silver, development points, influence)? The cost is not in the table row.
- Is the policy effect timed? The row has a `timeLeft` field, but the table shows 0 for every row.
- Does a mod-made widget receive clicks without a real mouse?

## Acceptance criteria
- [x] `policies.md` lists the policies, where they are defined, the live values and the enact result with evidence.
- [x] `policy-menu.md` describes the options a, b and c with a recommendation.
- [x] A read command `policy_state` exists, with a Python action and fake game tests.
- [x] `policy_enact` and `policy_sign` exist with tests (enact returned false in the real game; sign works).
- [x] No game asset, key or save data is in git. No save function was called.

## Update 2026-10-14: policy menu follow-ups (issue #60)
Click wiring (Lua poll, `Region:setPolicySigned`), the real policy list with game names, an F7 toggle, a clean widget and a releasable mod PolicyMenu 0.1.0 work in the real game. Gate scenario `policy-menu`. Notes: `implementation-notes/policy-menu-followups.md`. Open: publish the release (user decision).

## Update 2026-10-13: pak widget spike (option c)
A cooked Widget Blueprint in a mod pak was shown in the real game and a screenshot captured it. Findings and steps: `implementation-notes/pak-widget-spike.md`. Key facts: the widget tree is made headless from Python by copying a stock engine widget (the root widget is protected); `LoadAsset` does not load mod-pak assets but `AssetRegistryHelpers:GetAsset(FAssetData)` does. Open: click wiring, full policy list, clean source widget.
