"""A ready-made Manor Lords state: main menu, load screen, and the in-game engine.

Field names come from docs/specs/02-save-autoload/implementation-notes/jmap-findings.md and
in-game-messages-and-hud.md. Values match the real save `saveGame_0`.
"""

from types import SimpleNamespace

from .clock import FakeGameClock

IO_HANDLER_PATH = "/Script/ManorLords.Default__IoHandler"


def _slot_entry(game, slot_index, save_slot, level_name):
    descriptor = game.obj("MLSaveGameDescr", saveSlot=game.text(save_slot), LevelName=game.text(level_name))
    return game.struct(SlotIndex=slot_index, Descriptor=descriptor)


def _build_in_game(game, clock):
    region = game.obj("Region", isSettled=True, Approval=50, publicOrder=90, regionalWealth=50,
                      supplies_food=2, settlementLevel=0)
    game.method(region, "getNumHomelessFamilies", lambda _self: 5)
    game.method(region, "getNumTotalPopulation", lambda _self: 10)
    letter = game.struct(daySent=6, paras=game.array([game.text("welcome_from_hildebolt")]))
    player = game.obj("PawnCPP", bIsPlayerPaused=True, silver=0, influence=0, kingsFavour=0,
                      InBox=game.array([letter]), isMainPlayer=True)
    calendar = game.obj("TemporalComponent", day=61, month=3, Year=1, Season=1)
    engine = game.obj("RTSMultiEngineCPP", playerRef=player, regions=game.array([region]),
                      TemporalComponent=calendar, gameSpeed=0)
    clock.attach(game, engine, player)
    return SimpleNamespace(region=region, player=player, calendar=calendar, engine=engine)


def build_manor_lords_state(game, *, save_slot="saveGame_0", wanted_slot_listed=True,
                            save_exists=True, menu_delay=2.0, slot_list_delay=0.0,
                            engine_delay=2.0, clock=None):
    """Create the menu and the game and wire them like the real game.

    save_slot: the slot name that the load screen lists.
    wanted_slot_listed: False lists another name instead (the wanted slot never shows up).
    save_exists: the answer of IoHandler:DoesSaveGameExist.
    menu_delay: seconds until the main menu widget exists.
    slot_list_delay: seconds after SwitchToLoadScreen until the wanted slot is in the list.
    engine_delay: seconds after LoadGame until the engine actor exists.
    clock: a FakeGameClock (default: the real-game behavior).
    Returns a namespace: clock, calls (names of the menu calls), widget, screen, engine, player, ...
    """
    clock = clock or FakeGameClock()
    state = SimpleNamespace(clock=clock, calls=[], switched_at=None, loaded_at=None)
    state.game_objects = _build_in_game(game, clock)
    state.engine = state.game_objects.engine
    state.player = state.game_objects.player
    started_at = game.now()

    def list_is_complete():
        if slot_list_delay <= 0:
            return True
        return state.switched_at is not None and game.now() - state.switched_at >= slot_list_delay

    other = _slot_entry(game, 5, "saveGame_5", "Divided")
    wanted = _slot_entry(game, 2, save_slot if wanted_slot_listed else "other_slot", "Jagged_Cliffs")
    # The game fills the list while it scans the save folder, so the wanted slot can come late.
    slots = game.array([other, wanted], visible=lambda: 2 if list_is_complete() else 1)
    state.screen = game.obj("W_MainMenu_SaveLoadScreenV2_C", SortedSlotsByDate=slots)

    def switch_to_load_screen(_self, _save_mode):
        state.switched_at = game.now()
        state.calls.append("SwitchToLoadScreen")

    def load_game(_self, entry):
        state.loaded_at = game.now()
        state.calls.append(f"LoadGame:{entry['SlotIndex']}")
        clock.start_load()

    state.widget = game.obj("mainMenu_widget_C")
    game.method(state.widget, "SwitchToLoadScreen", switch_to_load_screen)
    game.method(state.widget, "LoadGame", load_game)

    state.io_handler = game.obj("IoHandler", _path=IO_HANDLER_PATH)
    game.method(state.io_handler, "DoesSaveGameExist", lambda _self, _slot: save_exists)

    in_menu = lambda: state.loaded_at is None
    game.finder("mainMenu_widget_C", lambda: state.widget if in_menu() and game.now() - started_at >= menu_delay else None)
    game.finder("W_MainMenu_SaveLoadScreenV2_C",
                lambda: state.screen if state.switched_at is not None and in_menu() else None)
    game.finder("RTSMultiEngineCPP",
                lambda: state.engine if not in_menu() and game.now() - state.loaded_at >= engine_delay else None)
    game.finder("PawnCPP", lambda: state.player if not in_menu() else None)
    return state
