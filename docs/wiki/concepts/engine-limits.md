---
type: Concept
title: Engine limits found by spikes
description: Things the game does not allow from Lua or data, found by spikes, with the evidence and the reason. Holds buildings inside the manor bailey, resource deposits, and the results of the community mod lead spikes (Squad struct reads, dead units, unit growth, stances, mesh swap).
tags: [engine, limits, bailey, manor, spike]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-19T00:00:00Z }
sources:
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-17-bailey-buildings/README.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-17-bailey-buildings/implementation-notes/bailey-buildings.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-12-manor-exploration/
  - resource: repo://openspec/changes/archive/2026-10-20-spike-community-mod-leads/notes/lead-1-2-stances.md
  - resource: repo://openspec/changes/archive/2026-10-20-spike-community-mod-leads/notes/lead-1-5-building-mesh-swap.md
---
# Engine limits found by spikes

## Buildings inside the manor bailey: not possible

Closed as not possible by owner decision, 2026-10-19 (issue #68, change `spike-bailey-buildings`). No more tests, no fixture and no pak route will be tried. Criterion M2 (wall in a whole town) stays not verified.

Facts that stay true:

- The mouse path refuses a normal building inside the bailey. The ghost is orange with the text "Road Access obstructed". The same building outside the ring is white and is placed (checked on the fixtures `manor-bailey` and `manor-closed`, a valid Large castle).
- The refusing check is native C++. Nine candidate functions were hooked and gave zero events. No data table holds the rule, and no reflected flag that it reads was found.
- A burgage plot committed without the mouse (`plot_field_place`, `addCommitFieldRequest`) skips the check and makes sites inside the ring. Builders never build them (0 of 4 after 30 game days, while 4 of 4 outside plots were built).
- Not separated: a bailey rule, or no reachable road path because the palisade blocks roads (ring with one gate). A gate-free ring test was never run.

Do not plan a feature that needs buildings inside the bailey.

## Bandit letter banner: hide it, do not stop it (spike #343)
- The reply letter and its banner come from native code. No hook sees them (`addToInbox`, `playEventMessage`, `playMessage` and others stay silent). A UE4SS pre-hook cannot cancel a UFunction.
- The banner is the widget class `questMessageElaborate_C`. It appears about 6 game seconds after `PawnCPP:sendLetter`.
- Setting `read` or `wasOpened`, or emptying `InBox`, does not stop the banner.
- What works: `RemoveFromParent` on live `questMessageElaborate_C` widgets that were not in the list taken before the send (run `s343-b1`). The letter stays in InBox, unopened. The game does not crash. The mod must hide the banner for each letter.
- Owner decision 2026-10-21: hiding the banner is enough; the letter may stay in the inbox. Notes: `openspec/changes/archive/2026-10-21-spike-bandit-message-toggle/notes/`.

## Menu pictures: PNG at run time (spike #333)
- A mod menu can show a picture the game does not have, without a pak. `KismetRenderingLibrary:ImportFileAsTexture2D(world, path)` loads a PNG from an absolute path with forward slashes. The texture is not compressed.
- Build the widget in Lua: `WidgetBlueprintLibrary:Create`, then `StaticConstructObject` of `WidgetTree` and `Image`. Use `Image:SetBrushFromTexture(texture, false)`, `AddToViewport` and `SetPositionInViewport`.
- 9-slice: write `image.Brush.DrawAs = 1` (Box) and `image.Brush.Margin = {Left, Top, Right, Bottom}`. Margin is a fraction of the texture (16 px of 256 px is 0.0625). Corners stay sharp at any size when the corner art is inside the margin.
- `SetDesiredSizeOverride` alone did not size a new full screen image (it drew about 24 px). Put the image in a canvas panel with full-screen anchors, or set the override after the brush change.
- Not known: a cooked pak texture and a custom (blackletter) font. Both need an editor cook and were not tried. A shipped mod must deploy its PNG next to its Lua (not tested).
- Owner decision 2026-10-21: menus may use PNG images loaded at run time. Notes: `openspec/changes/archive/2026-10-21-spike-menu-custom-textures/notes/`.

## Resource deposits: not reachable from Lua (spike #342)

- A deposit's surface amount, its "Rich" flag and "Endless Underground Reserves" live in native code. No reflected field holds them (checked on a salt mine, run 20261022-013541-4c3a). The amount shows only in the tooltip text (`MainUICPP_C.WidgetTree.WhiteTooltipRT`) while the mouse is over the deposit.
- The surface amount falls as the mine works: 1 per game day with 3 families on a salt mine.
- `ResourceNode` actors hold only map decals. `RTSGameManager.deposits` is empty. `getNearestResource(good, pos)` finds only construction piles, not salt.
- The only lever is the region production limit: `setProductionLimit(good, n)` holds a high value, and `setProductionUnlimited(good)` resets it. It caps output; it does not change a deposit. No region "unlimited" flag exists.
- The Nexus mod "Rich Deposit" (mod 357) changes deposits with a native DLL patch, not through reflection.
- Owner decision 2026-10-22: the mod does not manage resource state. Notes: `openspec/changes/archive/2026-10-22-spike-finite-resource-limits/notes/`.

## Results of the community mod lead spikes (change `spike-community-mod-leads`, #280)

Real game runs on 2026-10-20 and 2026-10-21. Details and run ids are in the notes of the change.

- **A `Squad` struct cannot be read.** `SquadComponent:GetSquad` and `getSquadByID` return the struct by value. Reading it ended the game (exit code 0xC0000409). So `Squad.behaviourStance`, `camp`, `campLocation` and `rallyingStatus` cannot be read from Lua. `HarnessLeads.READ_SQUAD_STRUCT` stays `false`. For lord armies read position, target and alive units from `lords_state`. `steer_state` gives 0 units for an AI lord squad.
- **`SetBehaviourStance` can be called** (`SquadComponent:SetBehaviourStance({ Value = id }, 0 neutral | 1 aggressive | 2 defensive, false)`) without a crash. It returns nothing and cannot be read back. Its effect on a fight was not shown.
- **Equipped ids** (`SMUnit:GetEquippedID(slot)`, slots 0 to 3) are plain numbers on a living unit. A unit that dies leaves the unit list at once, so the gear must be read before the death. The map from id to item was not found.
- **`spawnCompleteUnit` adds a full squad** to an AI lord (3 calls: 1 squad of 32 became 4 squads of 128 units, and `lords_state` lists them). Its return value is a `Squad` struct: do not read it.
- **`SetStaticMesh` swaps the mesh of a finished building** at once (component `StaticMeshComponent0` of an `SMBuilding`). A mesh that is already loaded is found with `StaticFindObject`. The collision shapes come from the new mesh (22 convex shapes became 0 with a sign post, and returned after the restore), while `GetCollisionEnabled` stays the same. Use `GetFullName` for a mesh path, not `GetPathName`.
- **A command field must be in `parseRequest`** of `HarnessActions`. A field that is not listed arrives as `nil` and the command may read only, with no error.
