---
type: Concept
title: Engine limits found by spikes
description: Things the game does not allow from Lua or data, found by spikes, with the evidence and the reason. Holds buildings inside the manor bailey, resource deposits, and the results of the community mod lead spikes (Squad struct reads, dead units, unit growth, stances, mesh swap).
tags: [engine, limits, bailey, manor, spike]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-19T00:00:00Z }
sources:
  - resource: repo://openspec/changes/archive/2026-10-24-spike-militia-weapon-rebellion/notes/q3-homes-stock-weapons.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-17-bailey-buildings/README.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-17-bailey-buildings/implementation-notes/bailey-buildings.md
  - resource: repo://openspec/changes/archive/2026-10-15-legacy-12-manor-exploration/
  - resource: repo://openspec/changes/archive/2026-10-20-spike-community-mod-leads/notes/lead-1-2-stances.md
  - resource: repo://openspec/changes/archive/2026-10-20-spike-community-mod-leads/notes/lead-1-5-building-mesh-swap.md
  - resource: repo://openspec/changes/archive/2026-10-21-spike-playtest-telemetry/notes/recommendation.md
  - resource: repo://openspec/changes/archive/2026-10-21-spike-new-game-difficulty-setting/notes/recommendation.md
  - resource: repo://openspec/changes/archive/2026-10-21-spike-finite-resource-limits/notes/salt-mine-deposit.md
  - resource: repo://openspec/changes/archive/2026-10-23-spike-public-order-factor/notes/tick-write.md
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
- The catalog of game widgets is [Native UI elements of the game](native-ui-elements.md). The guide for a new menu is [Building mod UI](../workflows/building-mod-ui.md).
- A mod can add a button to the game's bottom bar from Lua: `WidgetBlueprintLibrary:Create` of `/Game/UI/HUD/mainTabButton.mainTabButton_C`, then `AddChildToHorizontalBox` on `main_tabs_HB` of the HUD widget `MainUICPP_C`. The clone has the game's frame, size and hover glow. Its click and hover are seen with `RegisterHook` on `HandleClicked` and `HandleHovered` of that class (match the widget by name). The default icon is a map, the tooltip shows `mainTab_0`.
- A game widget class can go into the viewport (`AddToViewport`, `SetAnchorsInViewport` and `SetAlignmentInViewport` for a place without the viewport size): the base menu uses the game's `menuButton_C` as its Close button, bottom middle. Do not call `SetPositionInViewport` after the anchor: the widget then went to the top left (run 20261024-000819-9d15). Set the text with the property `TextKey` and `updateText`, and the `TextBlock` child.
- Esc: `RegisterKeyBind(Key.ESCAPE)` fires but does not swallow the key. The game opens its Esc menu (`mainMenu_widget_C`, made on the first Esc, collapsed when closed) and hides the HUD. `widget:continue()` closes it and gives the HUD back; `DoCloseAndHideSelf` leaves the HUD hidden. A hook cannot cancel the open. Notes: `openspec/changes/archive/2026-10-24-update-mod-menu-close-and-pause/notes/esc-key.md`.
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
- A cloned option widget shows only "label" until the mod sets it up. Spike #416 (`openspec/changes/spike-scenario-template-menu/notes/`, until archived: `openspec/changes/archive/*-spike-scenario-template-menu/notes/`) showed that it works from Lua: `AddChildToGrid` (the rows are in a `GridPanel`), `Text:SetText`, `Spinner:UpdateOptions` with `SettingOption {Label, Value}`, and `Spinner:GetCurrentIndex` for the value. Rows are hidden with `SetVisibility(1)`.
- The template bar `ModePresets` is made from the rows of the data table `DT_GameSetupPresets` (5 rows). A pak with a 6th row gives a 6th button, and a real click writes that row into `MLGameInstance.gameSetup` at once (AI lords, baron, difficulty, ...). A button made by Lua cannot select a preset (`HandlePressed` and `gamePresetSelected:Broadcast` do nothing).
- A click button of our pak (HarnessClickHooks) gets a disabled look with `handle.widget:SetColorAndOpacity({R=0.4,G=0.4,B=0.4,A=1})` (white to restore); the mod ignores the click itself. Used by the liege screen arms button (change `fix-arms-button-manor`, #455; `notes/disabled-look.md`). Do not read the building list (`HarnessManor.manor_state`) at each menu refresh or poll: two real runs crashed after such reads, so the menu caches the answer.
- The mod reads none of the raid, camp, aggressiveness, baron and AI count settings. Writing `raidingFrequency` or `daysUntilNextRaid` in a running game does not start or stop a native raid within 15 game days (the game recomputes the counter).
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

Real game runs on 2026-10-22 and 2026-10-23. Notes: `openspec/changes/archive/2026-10-23-spike-public-order-factor/notes/`.

- **Factors are an enum plus config weights, not data rows.** `EApprovalFactorType` has 34 values (0 to 33), for example unemployment 17, patrols 18, administration 19. Public order uses the same enum as approval. A pak cannot add a factor.
- **Weights come only from config.** `ApprovalSettings.ApprovalFactors` is a `float[34]` from `DefaultGame.ini`. Lua (bridge or raw) reaches only element 0. Read the defaults with `GetDefaultApprovalRateForFactor(i)`.
- **A config pak can change a weight** (`ManorLords/Config/DefaultGame.ini` in a `~mods` pak), but index 17 = -50 changed neither `publicOrder` nor approval in 10 game days.
- **`publicOrderMemory` entries have no effect.** An appended entry is safe, but the game rewrites `effectByPopulation` to a small per-person value, never lists it in `summedPublicOrderFactors`, and `publicOrder` stays equal to a control run.
- **A per-tick `Region.publicOrder` write holds.** The top bar shows the written value. The game never restores its own value, so the game value is unreadable after the first write. Families and approval did not change (order 2 against 42, 10 days).
- **Transient values.** `publicOrder` reads 0 or 100 for about 12 percent of samples (about one per game hour, also 100 in a control run). The paused top bar shows the stable value.
- Owner decision 2026-10-23: route A. The mod writes its own order value every tick and applies order effects in mod code.
- **The tooltip rows (spike #422).** The Public Order tooltip is the widget `BigTooltip_ApprovalAndPublicOrder_C` (one instance kept by the game instance). Its rows are `approvalFactorWidget_C` (`DescriptionText`, `ValueText`) in `recentFactors_VB`; `updateContents` clears and rebuilds them each time the tooltip opens, from `Region:getSummedFactorsRecentPast` over `summedPublicOrderFactors`. An entry appended to that list shows at once with the native label of its enum value, but the game rebuilds the list each game day, so it must be appended again; `past = true` entries give "Lingering Memories"; `publicOrderMemory` is not read. A custom row (own text, colour, sum) works from Lua: `Create` the row class, `AddChildToVerticalBox`, then `SetText` (a `SetText` before the add is overwritten by the row's default "Hunger +0%"; run 20261024-024516-b286). The row has an arrow `Image` (`Image_45` in `HorizontalBox_24`) with the up-arrow texture `tiny_arrow_triangle_up`; the game turns it with `RenderTransform.Angle` (0 for a positive value, 180 for a negative value). A new row has angle 180, so a custom row shows a down arrow until `Image:SetRenderTransformAngle(0.0)` is called after the add (change `fix-order-tooltip-arrows`, run uparrow-rows). Hook `updateContents` with a pre callback and add the row with `ExecuteWithDelay(60, ...)` (post callbacks of Blueprint hooks never fired). A real mouse hover over the scale icon opens the tooltip in a harness run (`osinput.hover_at`). The top bar percentage shows the written `publicOrder` of the region under the camera while the game runs. Notes: `openspec/changes/spike-public-order-indicators/notes/` (until archived: `openspec/changes/archive/*-spike-public-order-indicators/notes/`).

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
- **`battlefield_anchor({ lord })` without `home` uses the camera region (fixed for the raid in change `fix-raid-anchor-manor`).** The lord raid now calls it with `home = true`: the anchor is the player manor, else the average of the home-region buildings, never the camera. Before the fix, the call used the current region of the player pawn (the camera). A raid that starts with the camera over a free region puts the army and the battle marker there, although the mod log names the player's village as target. The mod plunder tick does not depend on the army position (a control run plundered 68 goods a day with the army 60 000 units from the village). The camera drifts in a long run when the cursor sits near the screen edge.
- **Plunder needs goods in tier 1 stores.** `world.plunder` takes only from them. With 21 goods in the stores, the baron steal rule took all on day 1 and the plunder took 0 afterwards.
- A fixture run that ends with `--keep-open` frees its slot lock: another agent's run can take the slot and kill the game. Hold the slot with a long scratch test scenario.
- One game crash (`EXCEPTION_ACCESS_VIOLATION reading 0x328`) 30 s after the first unpause with 3 camps, a second lord and killed camp squads. Two repeats with one camp did not crash. Cause not isolated.

## Crashes after spawns: threads and Lua state (spike #465)

- Crash reports (143 unique, 2026-09-27 to 2026-10-23): 53 are access violations inside the Lua core with garbage pointers, 40 in the UE4SS UObject wrapper (small addresses such as `0x10`, `0x18`, `0x70`), 38 in game code or a rethrow site, 8 engine fatal errors, 3 aborts from a Lua error in a `LoopAsync` callback. 96 of 143 fault on the game thread (`engine_tick_hook`, `process_simple_actions`).
- `LoopAsync`, `ExecuteAsync` and `ExecuteWithDelay` run the Lua callback on a separate thread. A Lua state is not thread safe, so this can damage the Lua heap of the mod. These functions are deprecated in the installed UE4SS. Use `LoopInGameThreadWithDelay(ms, fn)` and `ExecuteInGameThreadWithDelay`. Cancel with `CancelDelayedAction(handle)`. The shared module `HarnessLoop` wraps this.
- `RegisterKeyBind` callbacks run on the input thread. Do not touch shared Lua tables there. Queue the work with `ExecuteInGameThread` and change the tables in the queued function (`menu.request_toggle`, the Esc bind). No `LoopAsync` is left in the mods that ship (change `fix-lua-thread-safety`; `UEBridge` has the local patch P10).
- A scan of all units (`FindAllOf("SMUnit")`) does not run in the tick of a spawn. `raid_behavior` scans the new raid units about 0.25 s after the spawn.
- `pcall` does not catch a native access violation. Check `IsValid` before a method call on a widget from `GetChildAt` or on an object from `FindAllOf`.
- Not proven: that the timer change removes the crashes. After all timers moved (change `fix-lua-thread-safety`), `invasion-first-raid` had 0 crashes in 10 runs (3 of 11 before). The speed failure `TimeControlError` of `invasion-great-raid-waves` stayed (5 of 10); it is not caused by the timers. Details: `openspec/changes/archive/*-spike-lua-crash-after-spawn/notes/`.
- Each run folder has `hostmem.jsonl` (free and total PC memory and game resident memory every 2 s). Free memory fell to about 1 GB in runs without a crash.

## Militia squads, weapons in homes and turning villagers into bandits (spike #482)
- `PawnCPP:addMilitiaSquad(region, FName("spearMilitia"))` registers a militia squad from villagers without the mouse. It moves existing men (roles Husband and Son) from squad 0 into a new squad. The total unit count does not change. The squad size depends on the free men (10, 6, 4 in a village of 15 to 24 residents). The squads count in `pawn.commandedSquads` and the units count as side `player`. `canAddNewMilitiaSquad()` was true for 3 squads.
- Item 133 is the spear and item 271 is the large shield (the gear of `spearMilitia` is `163/133/271/273`). `building:addToInventory({Type=<id>, amt=<n>})` on the storehouse (`Data.bType` 72) raises `region:getStockOfGood` by exactly `n`.
- Registered, not rallied militia men stock one spear and one shield each in their burgage plots (`bType` 3) from the storehouse. It took about 6 game days for 10 men. The goods stay in the home `Inventory` and still count in the region stock. `region:getNumAssignedMilitaryStockOfType(id)` reports the number reserved for the militia.
- `building:consumeGoodNoCheck(id)` on a home removes one item from the home.
- `SMUnit:turnToBandit` on villagers (family members) does not make bandit units: the unit leaves its family and gets role 5 (Soldier), the side counts stay the same. A bandit squad at the homes (`homeless_rebel mode home`) is made of new units, and 3 families were killed. With no AI lords and no raids, that squad left the map (AI log "enough looted. Leaving map") and burned nothing in 1180 game seconds.

## Removing villagers: bodies and destroy (spike-rebel-without-corpses, 2026-10-24)

- `SMUnit:just_die` on a family member makes a body (`VAMP_DefaultUnit_C`, `dead`) where the person stands. It stays in `Region.corpses` about 1 230 game s (30 game days) without a corpse pit, and its actor vanishes about 400 game s later.
- `K2_DestroyActor` on any `SMUnit` crashes the game: a dead body (also after the list was emptied) within seconds (reading 0xe60), a living villager within seconds to 2 game days (reading 0x938).
- `Region:removeWorkerFamilyAt(familyID)` deletes only the family record. The people stay alive. Its argument is a family id, not an index.
- Safe on bodies: `SetActorHiddenInGame(true)` (`bHidden` true) and `Region.corpses:Empty()`. No visual effect was shown in a picture.
- `SMUnit:turnToSoldierJoinSquad` needs a Squad struct (unsafe to read). No reflected setter for the side of a unit was found.
- No native emigrate or evict function exists on Region, SMUnit or the pawn. Immigration refills the village about every 3 game days.

## Militia gear, rally and removing a bandit camp (spike-militia-corpses-and-camp-removal, #489)

- **Rally has no reflected call.** The Rally button (`Skill_Rally`, `W_HUD_ArmySkillButtonV2_C`, `SkillType` 11) only calls `PawnCPP:setPlaceRallyingPoint()`. The rally point is set by a real mouse click: `LMB_BP_pressed` and `LMB_BP_released` called from Lua do nothing. `SquadComponent:SetSkillActive(handle, 11, ...)` returns false (it works for sprint, skill 9). A squad handle is a struct `{Value = id}`, and `SMUnit.assignedSquadID.Value` is readable. `PawnCPP:selectSquad({Value=id}, false, false)` selects a squad.
- **Equip and unequip work on a living unit.** `SMUnit:equip(itemId, true, false)` fills a slot (spear 133 slot 1, large shield 271 slot 2; read with `GetEquippedID(slot)`). `SMUnit:unequip(slot)` clears it. This is cosmetic for a villager: it changes no stock and reverts in about 1 game day.
- **Dead militia:** each body is in `Region.corpses`, the squad shrinks, residents drop, the family record stays. The weapons in the home of a dead man go back to the storehouse in about 1 game day. Region stock stays the same. Hiding the bodies and `Region.corpses:Empty()` ran without a crash for about 30 game days.
- **Disband from Lua does not work.** `SquadComponent:RequestDisbandSquad` and `PawnCPP:disbandSquad` return without error and change nothing. Clicking `Skill_Disband` did not remove the squad.
- **A bandit camp can be removed.** After `just_die` on its 18 Brigands, `SMBuildingMaster:demolish(true)` on the camp master (`bType` 100; `canBeDemolished()` says false, `demolish()` needs its 1 argument) removes the 17 parts and the master in about 10 game s. The Outlaws pawn survives. The game did not respawn the camp or brigands in 28 game days. No crash.

- **Squad skill 19 (raid) can be toggled from Lua.** `SquadComponent:SetSkillActive(handle, 19, true, false)` returns true and `IsSkillActiveForSquad(handle, 19)` becomes true (spike `spike-squad-raid-skill`, run `spike-squad-raid-1`). `isSkillAvailableForSquad(handle, skill, {})` takes an Out table as third argument. In peacetime, in the own region, `PawnCPP:isAnySquadRaiding({})` stayed false and no raid was seen. Next to a built building of an enemy village (a new AI lord at war, region of the village), skill 19 makes the squad walk by itself to the village and stop (flame on its banner), with flag false and with flag true, but no raid starts: `isAnySquadRaiding` stays false and no loot or fire shows in 240 to 400 game seconds, also 55 units from a built building (spike `spike-raid-skill-near-enemy`, probe `probe-raid-near`). Without the skill the squad stays still. A bandit camp is no target: its building has no region and the squad does not move. Why no raid starts is open (rally by mouse, unit type and goods not tested). A player squad can be put next to a target without a move order: centre the camera (`centre_camera_on`), then `spawn_units("player", ...)`. A real right click through `steer_cursor` did not move the squad this time. The village of a lord lies around world (0, 0), not at the region actor point. `GetSquadUnitCount` returned 0 for a 20-man squad.
