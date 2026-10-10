"""FakeGameClock: the game clock with pause and speed, as seen in the real game.

Source: docs/specs/02-save-autoload/implementation-notes/pause-and-game-speed.md
"""

# setGameSpeed(0) was measured to leave the clock moving a little (0.8 in 3 s).
RESIDUAL_RATE_AT_SPEED_ZERO = 0.27


class FakeGameClock:
    """The clock stands at 0 for `hold_seconds` after a load. Then the game starts it at 1x.
    That start undoes any pause made too early. If `late_revert_after` is set, the game undoes
    the pause once more, that many seconds after the load (seen 2 to 4 s after our pause).

    starts=False: the game never starts the clock.
    pause_works=False: pauseGame has no effect.
    """

    def __init__(self, hold_seconds=12.0, late_revert_after=17.0, starts=True, pause_works=True):
        self.hold_seconds = hold_seconds
        self.late_revert_after = late_revert_after
        self.starts = starts
        self.pause_works = pause_works
        self.time = 0.0
        self.speed = 1.0
        self.paused = False
        self.held = True
        self.seconds_since_load = None
        self.calls = []
        self._reverted = False
        self._engine = None

    def attach(self, game, engine, player):
        """Add pauseGame, unPauseGame and setGameSpeed to the player, and the clock to the engine."""
        self._engine = engine
        game.method(player, "pauseGame", lambda _self: self.pause_game(player))
        game.method(player, "unPauseGame", lambda _self: self.un_pause_game(player))
        game.method(player, "setGameSpeed", lambda _self, speed: self.set_game_speed(speed))
        game.method(engine, "getGameTimeAdjusted", lambda _self: self.time)
        game.add_ticker(self.tick)

    # -- calls from the mod ---------------------------------------------------------------

    def start_load(self):
        self.seconds_since_load = 0.0

    def pause_game(self, player):
        self.calls.append("pauseGame")
        if self.pause_works:
            self.paused = True
            # This flag is not reliable in the real game. It changes only after these calls.
            player["bIsPlayerPaused"] = True
        self._publish_speed()

    def un_pause_game(self, player):
        self.calls.append("unPauseGame")
        self.paused = False
        player["bIsPlayerPaused"] = False
        self._publish_speed()

    def set_game_speed(self, speed):
        self.calls.append(f"setGameSpeed:{speed}")
        self.speed = float(speed)
        self._publish_speed()

    # -- time -----------------------------------------------------------------------------

    def rate(self):
        if self.seconds_since_load is None or self.held or self.paused:
            return 0.0
        if self.speed == 0:
            return RESIDUAL_RATE_AT_SPEED_ZERO
        return self.speed

    def tick(self, seconds):
        if self.seconds_since_load is None:
            return
        self.seconds_since_load += seconds
        self._apply_game_rules()
        self.time += seconds * self.rate()
        self._publish_speed()

    def _apply_game_rules(self):
        if self.held and self.starts and self.seconds_since_load >= self.hold_seconds:
            self.held = False
            self.paused = False  # the game starts the clock and undoes an earlier pause
        late = self.late_revert_after
        if late is not None and not self._reverted and not self.held and self.seconds_since_load >= late:
            self._reverted = True
            self.paused = False

    def _publish_speed(self):
        if self._engine is not None:
            self._engine["gameSpeed"] = 0 if (self.held or self.paused) else self.speed
