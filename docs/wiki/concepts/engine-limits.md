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
  - resource: repo://openspec/changes/archive/2026-10-21-spike-playtest-telemetry/notes/recommendation.md
  - resource: repo://openspec/changes/archive/2026-10-21-spike-new-game-difficulty-setting/notes/recommendation.md
  - resource: repo://openspec/changes/archive/2026-10-21-spike-finite-resource-limits/notes/salt-mine-deposit.md
  - resource: repo://openspec/changes/spike-public-order-factor/notes/tick-write.md
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

## Mod menus: bottom bar button and click blocking (#308)
- A mod can add a button to the game's bottom bar from Lua: `WidgetBlueprintLibrary:Create` of `/Game/UI/HUD/mainTabButton.mainTabButton_C`, then `AddChildToHorizontalBox` on `main_tabs_HB` of the HUD widget `MainUICPP_C`. The clone has the game's frame, size and hover glow. Its click and hover are seen with `RegisterHook` on `HandleClicked` and `HandleHovered` of that class (match the widget by name). The default icon is a map, the tooltip shows `mainTab_0`.
- A clone can also go into the viewport (`AddToViewport`, `SetPositionInViewport`): the base menu uses one as its Close button.
- `Button.OnClicked:Add(fn)` on a Button made with `StaticConstructObject` crashes the game (access violation at `0x70` in `XMulticastDelegateProperty::setup_member_functions`). Never bind a delegate on a widget made at run time.
- Click blocking: a full-screen `Button` in the viewport blocks a click to the game, a full-screen `Border` does not. A `Border` of the menu content (Visible) also lets a click through; set it to `SelfHitTestInvisible` (4). `SetInputMode_UIOnlyEx(controller, widget, 0, true)` (4 parameters) also blocks, but changes the input of the whole game.
- Notes: `openspec/changes/add-mod-menu-access-rule/notes/` (open) or its archive.

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
- The class `DepositDecal` (with `bRichDeposit`) still exists, but the game creates no object of it (2026-10-22); an older Nexus Lua mod that wrote it no longer has an effect.
- Owner decision 2026-10-22: the mod does not manage resource state. Notes: `openspec/changes/archive/2026-10-21-spike-finite-resource-limits/notes/`.

## Player logs, files and quit (spike #384)

- A Lua log that writes and flushes each line keeps every line when the game process is killed (63603 of 63603 lines; a log without flush lost 86 lines and ended mid-line). A flush costs about 10 us per line.
- No quit hook fires when the game closes (6 hooks and a `__gc` finalizer tried, after `WM_CLOSE`). A "session running" marker is therefore still there after a normal quit; tell a crash from a quit with a newer folder in `Saved\Crashes`.
- UE4SS Lua `io` reads a 2.6 MB save copy byte for byte and writes files and folders. `io.popen("dir /b /ad /o-d")` finds the newest crash folder; `os.execute` and `io.popen` flash a console window.
- A pure Lua stored zip (no compression) of 4.5 MB takes about 0.2 s; in steps of 256 KB to 1 MB per tick the game does not stall.
- A mod menu can hold a text box, a check box and a button without a pak widget; typing needs `SetKeyboardFocus` first.
- One soak run crashed inside UE4SS Lua (`ltable.c`, `mainpositionTV`, exit code 3); the cause is not known.
- Notes: `openspec/changes/archive/2026-10-21-spike-playtest-telemetry/notes/`.
## Game Setup values: readable, not saved (spike #358)

- The new game setup values live in `MLGameInstance.gameSetup.currentGameSetup` (`raidingFrequency`, `yearsUntilFirstRaid`, `maxBanditCamps`, `initialBanditCamps`). Lua can read them (`HarnessGameSetup`). The game does not store them in the save.
- A mod cannot add a working option to the stock Game Setup screen: a cloned option widget shows only "label".
- Opening the Game Setup screen writes the real `menu.sav`, even in a run with a private appdata. Back up first.
- The first `disable_autosave` after a new game started from the menu is undone by the game; send it again after the intro.
- Owner decision 2026-10-21: the mod opens its own scenario settings menu instead (change `add-scenario-settings-menu`, #375). Notes: `openspec/changes/archive/2026-10-21-spike-new-game-difficulty-setting/notes/`.

## Results of the community mod lead spikes (change `spike-community-mod-leads`, #280)

Real game runs on 2026-10-20 and 2026-10-21. Details and run ids are in the notes of the change.

- **A `Squad` struct cannot be read.** `SquadComponent:GetSquad` and `getSquadByID` return the struct by value. Reading it ended the game (exit code 0xC0000409). So `Squad.behaviourStance`, `camp`, `campLocation` and `rallyingStatus` cannot be read from Lua. `HarnessLeads.READ_SQUAD_STRUCT` stays `false`. For lord armies read position, target and alive units from `lords_state`. `steer_state` gives 0 units for an AI lord squad.
- **`SetBehaviourStance` can be called** (`SquadComponent:SetBehaviourStance({ Value = id }, 0 neutral | 1 aggressive | 2 defensive, false)`) without a crash. It returns nothing and cannot be read back. Its effect on a fight was not shown.
- **Equipped ids** (`SMUnit:GetEquippedID(slot)`, slots 0 to 3) are plain numbers on a living unit. A unit that dies leaves the unit list at once, so the gear must be read before the death. The map from id to item was not found.
- **`spawnCompleteUnit` adds a full squad** to an AI lord (3 calls: 1 squad of 32 became 4 squads of 128 units, and `lords_state` lists them). Its return value is a `Squad` struct: do not read it.
- **`SetStaticMesh` swaps the mesh of a finished building** at once (component `StaticMeshComponent0` of an `SMBuilding`). A mesh that is already loaded is found with `StaticFindObject`. The collision shapes come from the new mesh (22 convex shapes became 0 with a sign post, and returned after the restore), while `GetCollisionEnabled` stays the same. Use `GetFullName` for a mesh path, not `GetPathName`.
- **A command field must be in `parseRequest`** of `HarnessActions`. A field that is not listed arrives as `nil` and the command may read only, with no error.

## Corpse pit and loot (spike #360)

- The corpse pit is `DT_Buildings` id 113 (`BM_CorpsePit_C`), job 65, 4 workers. The game does not assign workers to it by itself; a test uses `building_assign_worker type=113`. Without workers, bodies stay on the ground.
- Workers carry bodies (task `collecting_body`). On delivery the pit inventory entry `Type 233` (corpse) `amt` rises by 1. No hook fires, so a mod must poll the pit.
- `pit:addToInventory({Type=<good>, amt=<n>})` counts in the region stock at once. Villagers haul the goods to a store in 3 to 5 game days. No goods pile actor exists and nothing shows on the ground.
- A dead raider keeps `ItemsLooted`, and the same object stays in `Region.corpses` until a worker picks it up.
- Reading `unit.currAnim`, `unit.dropsTo:GetFName()` or `unit.Speed` (one of them) crashed the game (access violation 0x18).
- Owner decision 2026-10-22: the pit replaces the direct store add; loot give-back is for Hussite raids only (change `add-corpse-pit-loot`). Notes: `openspec/changes/archive/*-spike-corpse-pit-loot/notes/`.

## Public order factors (spike #403)

Real game runs on 2026-10-22 and 2026-10-23. Notes: `openspec/changes/spike-public-order-factor/notes/`.

- **Factors are an enum plus config weights, not data rows.** `EApprovalFactorType` has 34 values (0 to 33), for example unemployment 17, patrols 18, administration 19. Public order uses the same enum as approval. A pak cannot add a factor.
- **Weights come only from config.** `ApprovalSettings.ApprovalFactors` is a `float[34]` from `DefaultGame.ini`. Lua (bridge or raw) reaches only element 0. Read the defaults with `GetDefaultApprovalRateForFactor(i)`.
- **A config pak can change a weight** (`ManorLords/Config/DefaultGame.ini` in a `~mods` pak), but index 17 = -50 changed neither `publicOrder` nor approval in 10 game days.
- **`publicOrderMemory` entries have no effect.** An appended entry is safe, but the game rewrites `effectByPopulation` to a small per-person value, never lists it in `summedPublicOrderFactors`, and `publicOrder` stays equal to a control run.
- **A per-tick `Region.publicOrder` write holds.** The top bar shows the written value. The game never restores its own value, so the game value is unreadable after the first write. Families and approval did not change (order 2 against 42, 10 days).
- **Transient values.** `publicOrder` reads 0 or 100 for about 12 percent of samples (about one per game hour, also 100 in a control run). The paused top bar shows the stable value.
- Owner decision 2026-10-23: route A. The mod writes its own order value every tick and applies order effects in mod code.

## Ruins and the rebuild order (change `add-vassal-sack-wipe`, #341)

- `collapseBuilding()` makes a building rubble (`Data.bType` 75) at once and stores the old type in `typeBeforeChange` (0 on a standing building). After a rebuild `typeBeforeChange` reads 75.
- No reflected UFunction rebuilds a ruin. The panel rebuild button runs native code, and hooks on the pawn and panel Blueprint functions caught nothing.
- A rebuild order from Lua works: write `building.Data` back as a whole struct with `bType = typeBeforeChange`, `constructed = false`, `hp = 0`, then call `building:SetupBuilding()`. It rebuilds the parts (2 to 53), restores `maxHp` and storage, and the building is a construction site. Skip a ruin whose `typeBeforeChange` is 0 or 75. No crash in any of these calls.
- Do not call `convertBlueprintsToBuildings` after it: it cuts the parts (42 to 6, 50 to 25) and the finished building has no model. Writing `Data` without `SetupBuilding` gives a "finished" building with the rubble parts only (a pile of ash).
- `addToInventory({Type, amt})` is accepted on a ruin, so goods can be given when no building stands.
- AI lord with ruins: one collapsed building was a site again within about 1 game day. After the order on 35 ruins the AI built 13 in about 2 game days (against 1 or 2 at a time without it), and the owner saw full models. Removing logs and planks only delays an AI rebuild briefly (villagers make planks at once).
- A wiped region has no AI lord on the map although `region.ownerPawn` still points to the old pawn, and nobody builds. `ResetAIBuildingOptions` changed nothing, and `IsActive` of a planner is false in healthy villages too, so it means nothing. The mod gives the region to a lord again (`lord_receive_region`).
- Not tested: whether a rebuild order survives a save and a load (needs the guarded `save_game`).
- Source: `openspec/changes/add-vassal-sack-wipe/notes/rebuild-order.md` (runs 20261022-231049-8008 and 20261022-231824-d19d).

## Bandit camps, AI lords and raids with the game settings at zero (spike #430)

Fixture `playtest-noai` (AI opponents 0, Off map adversary Absent, Raider frequency None, Initial bandit camps 0, spawn limit 0). Notes: `openspec/changes/spike-playtest-world-ai/notes/` (until archived: `openspec/changes/archive/*-spike-playtest-world-ai/notes/`).

- **No bandit pawn without a camp.** The world has one `PawnCPP` (the player). `bandit_state` is refused and `HarnessBattle.spawn_at("bandit")` returns "no pawn for side bandit".
- **`RTSMultiEngineCPP:spawnBanditCamp()` makes the bandit pawn** ("Outlaws", trait `bandit`) with a camp (type 100, 17 parts) and 18 Brigands, also with camps 0 and limit 0. Each call makes another camp. The pawn has no relation row with the player: call `addPawnRelations` (`lord_relations`). The pawn stays when its units are killed with `just_die`. The camp squads walk on their own (one went to the player village and left).
- **AI lords with AI opponents 0.** `spawnNewAILord` works. The lord builds only after a full claim: `lord_found_village` (free region) or `lord_receive_region` (settled region), plus `lord_relations` and `lord_start_ai(build)`. Writing `Region.ownerPawn` alone gives no buildings (0 in 55 game days); a founded village went from 4 to 21 buildings in about 85 game days (13 in the first 9 days).
- **The Hussite raid needs no setting.** It is the army of a mod-made lord (`lord_raid.lua`). It spawns and passes the raid test scenarios with Off map adversary Absent, AI opponents 0 and Raider frequency None.
- **The raid goes to the camera region.** `battlefield_anchor({ lord })` uses the current region of the player pawn (the camera). A raid that starts with the camera over a free region is anchored there, although the mod log names the player's village as target.
- **Plunder needs goods in tier 1 stores.** `world.plunder` takes only from them. With 21 goods in the stores, the baron steal rule took all on day 1 and the plunder took 0 afterwards.
- A fixture run that ends with `--keep-open` frees its slot lock: another agent's run can take the slot and kill the game. Hold the slot with a long scratch test scenario.
- One game crash (`EXCEPTION_ACCESS_VIOLATION reading 0x328`) 30 s after the first unpause with 3 camps, a second lord and killed camp squads. Two repeats with one camp did not crash. Cause not isolated.
