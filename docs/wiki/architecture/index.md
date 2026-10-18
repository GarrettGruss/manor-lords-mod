# Pages

* [Invasion Mod features](invasion-features.md) - The features of mod/InvasionMod - what each one implements now, its named commands, its dependencies on other features, and its mod spec.
* [Invasion Mod structure](invasion-mod.md) - How mod/InvasionMod is built - one Lua mod and one pak made of features, with main.lua, feature_loader, feature_list, scheduler, config, mod.json, data patches and scenarios.
* [Harness and player mods](other-mods.md) - The Lua mods in mod/ besides the Invasion Mod - harness mods (HarnessBoot, HarnessTelemetry, HarnessReload, HarnessPlace, HarnessActions, UEBridge), stand-in fixtures and probes. The standalone player mods were removed.
* [System overview](overview.md) - The layers of the harness (game mods, live control bridge, outer harness, MCP tools) and how one edit, deploy, run and read loop flows through them.
* [Shared Lua modules](shared-lua-modules.md) - What the modules in mod/shared are, how mods load them, the rules they all follow, and which of them have fake-game tests.
* [Source map](source-map.md) - What each top folder and main subfolder of the repo owns, the entry files, and which paths are git-ignored.
