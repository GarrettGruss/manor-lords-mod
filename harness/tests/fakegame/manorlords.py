"""A ready-made Manor Lords state: main menu, load screen, and the in-game engine.

Field names come from docs/specs/02-save-autoload/implementation-notes/jmap-findings.md and
in-game-messages-and-hud.md. Values match the real save `saveGame_0`.
"""

from types import SimpleNamespace

from .clock import FakeGameClock

IO_HANDLER_PATH = "/Script/ManorLords.Default__IoHandler"
TIMER_LIBRARY_PATH = "/Script/Engine.Default__KismetSystemLibrary"
# Values read from the real game (docs/specs/06-dev-loop-and-fixtures/implementation-notes/autosave.md).
AUTOSAVE_PERIOD_S = 600
FIRST_TIMER_HANDLE = 503316508


class FakeAutosaveTimer:
    """The autosave timer of the player pawn. It counts real time, also while the game is paused (as the real one did)."""

    def __init__(self, game, *, works=True):
        self.game = game
        self.works = works
        self.calls = []
        self.handle = game.struct(Handle=FIRST_TIMER_HANDLE)
        self.ends_at = game.now() + AUTOSAVE_PERIOD_S

    def remaining(self):
        return self.ends_at - self.game.now()

    def restart(self, seconds):
        """SetAutosavePeriodOnPawn. A broken timer (works=False) answers true but changes nothing."""
        self.calls.append(f"SetAutosavePeriodOnPawn:{seconds:g}")
        if self.works:
            self.handle["Handle"] += 5000000000
            self.ends_at = self.game.now() + seconds
        return True


def _build_autosave(game, player, works):
    timer = FakeAutosaveTimer(game, works=works)
    player["autosaveHandle"] = timer.handle
    instance = game.obj("MLGameInstance", Settings=game.struct(autosavePeriod=AUTOSAVE_PERIOD_S), savefileToLoad=game.text(""))
    timer.instance = instance
    game.method(instance, "SetAutosavePeriodOnPawn", lambda _self, seconds: timer.restart(seconds))
    library = game.obj("KismetSystemLibrary", _path=TIMER_LIBRARY_PATH)
    game.method(library, "K2_TimerExistsHandle", lambda _self, _world, _handle: True)
    game.method(library, "K2_GetTimerRemainingTimeHandle", lambda _self, _world, _handle: timer.remaining())
    game.static(TIMER_LIBRARY_PATH, library)
    timer.library = library
    return timer


def _slot_entry(game, slot_index, save_slot, level_name):
    descriptor = game.obj("MLSaveGameDescr", saveSlot=game.text(save_slot), LevelName=game.text(level_name))
    return game.struct(SlotIndex=slot_index, Descriptor=descriptor)


def _build_in_game(game, clock, autosave_works):
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
    autosave = _build_autosave(game, player, autosave_works)
    return SimpleNamespace(region=region, player=player, calendar=calendar, engine=engine, autosave=autosave)


def build_manor_lords_state(game, *, save_slot="saveGame_0", wanted_slot_listed=True,
                            save_exists=True, menu_delay=2.0, slot_list_delay=0.0,
                            engine_delay=2.0, clock=None, autosave_works=True, load_starts_new_game=False,
                            open_map_works=True, open_map_loads_slot=None):
    """Create the menu and the game and wire them like the real game.

    save_slot: the slot name that the load screen lists.
    wanted_slot_listed: False lists another name instead (the wanted slot never shows up).
    save_exists: the answer of IoHandler:DoesSaveGameExist.
    menu_delay: seconds until the main menu widget exists.
    slot_list_delay: seconds after SwitchToLoadScreen until the wanted slot is in the list.
    engine_delay: seconds after LoadGame until the engine actor exists.
    clock: a FakeGameClock (default: the real-game behavior).
    autosave_works: False makes SetAutosavePeriodOnPawn answer true but leave the timer as it was.
    load_starts_new_game: True copies the real bug seen before 2026-10-11: LoadGame clears savefileToLoad and a new game starts.
    open_map_works: False makes the console command `open` do nothing (the map never opens).
    open_map_loads_slot: a slot name that `open` wrongly leaves in savefileToLoad (a save would load).
    Returns a namespace: clock, calls (names of the menu calls), widget, screen, engine, player, ...
    """
    clock = clock or FakeGameClock()
    state = SimpleNamespace(clock=clock, calls=[], switched_at=None, loaded_at=None)
    state.game_objects = _build_in_game(game, clock, autosave_works)
    state.autosave = state.game_objects.autosave
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
        if load_starts_new_game:
            state.autosave.instance["savefileToLoad"] = game.text("")
        clock.start_load()

    state.widget = game.obj("mainMenu_widget_C")
    game.method(state.widget, "SwitchToLoadScreen", switch_to_load_screen)
    game.method(state.widget, "LoadGame", load_game)

    def console_command(_self, command, _write_to_log=False):
        state.calls.append(f"ConsoleCommand:{command}")
        if command.startswith("open ") and open_map_works and state.loaded_at is None:
            state.loaded_at = game.now()
            if open_map_loads_slot:
                state.autosave.instance["savefileToLoad"] = game.text(open_map_loads_slot)
            clock.start_load()

    # The real PlayerController:ConsoleCommand is not callable from Lua (run fresh-start-1). The game uses the library call.
    state.controller = game.obj("PlayerController")
    state.world = game.obj("World")
    game.method(state.autosave.library, "ExecuteConsoleCommand",
                lambda _self, _world, command, _controller=None: console_command(_self, command))
    game.finder("World", lambda: state.world)

    state.io_handler = game.obj("IoHandler", _path=IO_HANDLER_PATH)
    game.method(state.io_handler, "DoesSaveGameExist", lambda _self, _slot: save_exists)

    in_menu = lambda: state.loaded_at is None
    game.finder("mainMenu_widget_C", lambda: state.widget if in_menu() and game.now() - started_at >= menu_delay else None)
    game.finder("W_MainMenu_SaveLoadScreenV2_C",
                lambda: state.screen if state.switched_at is not None and in_menu() else None)
    game.finder("RTSMultiEngineCPP",
                lambda: state.engine if not in_menu() and game.now() - state.loaded_at >= engine_delay else None)
    game.finder("PlayerController", lambda: state.controller)
    game.finder("PawnCPP", lambda: state.player if not in_menu() else None)
    return state
