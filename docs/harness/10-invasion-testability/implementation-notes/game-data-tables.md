# Game data tables (names only)

Date: 2026-10-10. Source: `repak list` on the game paks (spec 09 spike, branch feat/22-pak-spike).
This note holds names and paths only. No game asset or extracted file is in git.

## Where the unit data is
There is no `DT_units` file. The unit data tables are:
- `ManorLords/Content/NotStronghold/Data/DT_UnitTemplates` (pak `pakchunk0_s11`). This is the current unit template table.
- `ManorLords/Content/NotStronghold/Data/DT_UnitTemplates_OLD` (same pak). An old copy.
- `ManorLords/Content/NotStronghold/Data/DT_MercenaryCompanies` (same pak). Mercenary companies.
- `ManorLords/Content/NotStronghold/Data/RetinueSet` (same pak). Not a `DT_` table. Related to retinues.
- Text for units: `DT_Translation_UnitTemplates` and `DT_Translation_UnitRoles` (pak `pakchunk0_s16`).
No asset with `Raid`, `Bandit` or `Squad` in a table name was found. `squadStats` is a UI widget (`UI/Tooltips`).

Paths below start at `ManorLords/Content/`. All paks have mount point `../../../`. Asset files have `.uasset` and `.uexp`.

## All DT_ assets under Content
| Asset path | Pak |
|---|---|
| `ManorLords/Content/CPP_BP/dynamicMusic/DT_MusicTracks` | `pakchunk0_s1` |
| `ManorLords/Content/CPP_BP/dynamicMusic/DT_MusicTransitions` | `pakchunk0_s1` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetBird` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetChicken` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetCombat` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetCombined` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetDeer` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetGoat` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetHare` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetHorse` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetHound` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetOx` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetPig` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetSheep` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_AnimsetWork` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_BuildingMeshPathData` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_BuildingSocketMeshData` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_ConstructionBPs` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_GameplayStaticMeshData` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_IndependentBuildingPartAssemblies` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_InputIconConfigTable` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_Items` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_MercenaryCompanies` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_Para` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_PolicyTypes` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_Quests` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_Quirks` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_UnitTemplates` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_UnitTemplates_OLD` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/Data/DT_Upgrades` | `pakchunk0_s11` |
| `ManorLords/Content/NotStronghold/RichText/DT_BigTooltipText` | `pakchunk0_s15` |
| `ManorLords/Content/NotStronghold/RichText/DT_BigTooltipText_LargerFont` | `pakchunk0_s15` |
| `ManorLords/Content/NotStronghold/RichText/DT_FeedbackText` | `pakchunk0_s15` |
| `ManorLords/Content/NotStronghold/RichText/DT_GameplayIcons` | `pakchunk0_s15` |
| `ManorLords/Content/NotStronghold/RichText/DT_Letter` | `pakchunk0_s15` |
| `ManorLords/Content/NotStronghold/RichText/DT_MenuToolTipStyleV2` | `pakchunk0_s15` |
| `ManorLords/Content/NotStronghold/RichText/DT_RichText_Challenge` | `pakchunk0_s15` |
| `ManorLords/Content/NotStronghold/RichText/DT_StoryText` | `pakchunk0_s15` |
| `ManorLords/Content/NotStronghold/RichText/DT_TooltipStyle` | `pakchunk0_s15` |
| `ManorLords/Content/NotStronghold/RichText/DT_TooltipStyle_SmallerText` | `pakchunk0_s15` |
| `ManorLords/Content/NotStronghold/RichText/DT_WhiteTooltipText` | `pakchunk0_s15` |
| `ManorLords/Content/Translation/DT_Translation` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/DT_TranslationMercenaryCompanyNamesold` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Affinities` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Approval` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_BuildingDescriptions` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_BuildingNames` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Collapse` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Crops` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_DevelopmentBranches` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Diplomacy` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Events_Common` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Events_Introduction` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Events_RestoringThePeace` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_GameSetups` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Growth` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Item_Subcategories` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Items` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Jobs` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_LogEntries` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_MainUI` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Maintenance` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Maps` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Menus` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_MercenaryCompanies` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Military` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_PerkCategories` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_PerkEffects` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Perks` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Policies` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Problems` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_QuestRelated` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Quirks` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_ResourceNodes` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Tasks` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Tutorials` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_UnitRoles` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_UnitTemplates` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Upgrades` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Weather_and_Seasons` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_Wiki` | `pakchunk0_s16` |
| `ManorLords/Content/Translation/HoodedHorse/DT_Translation_in_progress` | `pakchunk0_s16` |
| `ManorLords/Content/UI/Development/DT_RegionDevelopmentTech` | `pakchunk0_s16` |
| `ManorLords/Content/UWG/Events/DT_Popups` | `pakchunk0_s18` |
| `ManorLords/Content/ManorLords/Audio/Cues/DT_AudioCues` | `pakchunk0_s2` |
| `ManorLords/Content/ManorLords/Audio/Cues/DT_AudioCues_Combat` | `pakchunk0_s2` |
| `ManorLords/Content/ManorLords/Audio/Voice/Economy/English/Cydney/DT_Voice_Eco_Eng_Cydney` | `pakchunk0_s2` |
| `ManorLords/Content/ManorLords/Audio/Voice/Economy/English/Liam/DT_Voice_Eco_Eng_Liam` | `pakchunk0_s2` |
| `ManorLords/Content/ManorLords/Audio/Voice/Economy/English/LiamsFriend/DT_Voice_Eco_Eng_LiamsFriend` | `pakchunk0_s2` |
| `ManorLords/Content/ManorLords/Database/Approval/DT_Approval` | `pakchunk0_s4` |
| `ManorLords/Content/ManorLords/Database/DT_Alerts` | `pakchunk0_s4` |
| `ManorLords/Content/ManorLords/Database/DT_CoatTextureData` | `pakchunk0_s4` |
| `ManorLords/Content/ManorLords/Database/DT_GameSetupPresets` | `pakchunk0_s4` |
| `ManorLords/Content/ManorLords/Database/DT_HudIcons` | `pakchunk0_s4` |
| `ManorLords/Content/ManorLords/Database/DT_LogEntryTypes` | `pakchunk0_s4` |
| `ManorLords/Content/ManorLords/Database/DT_MapData` | `pakchunk0_s4` |
| `ManorLords/Content/ManorLords/Database/DT_QuestDecoration` | `pakchunk0_s4` |
| `ManorLords/Content/ManorLords/Database/DT_WikiSubjects` | `pakchunk0_s4` |
| `ManorLords/Content/NotStronghold/Audio/Ambience/DT_AmbienceSounds` | `pakchunk0_s9` |
