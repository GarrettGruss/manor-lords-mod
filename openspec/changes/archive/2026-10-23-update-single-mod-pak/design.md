## Decisions

- Reuse `copy_assets` of `modpak.py`. No new build step: a cooked widget is a file under `data/<feature>/assets/ManorLords/Content/HarnessMod/`.
- Owner of each asset: `raid_widget` (WBP_RaidMenu), `scenario_settings` (WBP_ScenarioSettings), `liege_influence` (WBP_LiegeTribute), `tech_tree_widget` (WBP_TechTreeMenu), `invasion` (WBP_ClickButton, shared by all menus). Two features may not own one file.
- The assets come from unpacking the committed old paks (the cook of the UE project gives the same files). The `ue/make_*.py` scripts stay the source: a rebuilt widget is cooked and copied to the same asset path.
- A feature with `"pak": false` is not built. All widget features are built, so the pak always holds every menu.
