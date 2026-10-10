"""FakeGame: a Lua state with a fake UE4SS API, for testing mods without the game."""

import json
import os
import shutil
import tempfile
from pathlib import Path

from lupa import LuaRuntime

REPO_ROOT = Path(__file__).resolve().parents[3]
PRELUDE = Path(__file__).with_name("prelude.lua")

DEFAULT_STEP_SECONDS = 0.5  # the polling time most mods use (LoopAsync 500)


class FakeGame:
    """Use as a context manager. It sets the test environment and restores it on exit.

    env: extra environment variables for the mod (a value of None removes the variable).
    strict_threads: fail when a game object is touched outside the game thread.
    array_wrap: TArray elements come as wrappers that need :get().
    fstring_mode: text properties come as FString-like values that need :ToString().
    separate_states: every `load_mod` runs the mod in its own Lua state, as UE4SS does. A shared module (HarnessCommands)
        is then loaded again for each mod, and the registries are separate. Loading the same mod again makes a fresh state.
    """

    def __init__(self, env=None, strict_threads=False, array_wrap=False, fstring_mode=True,
                 repo_root=REPO_ROOT, separate_states=False):
        self.repo_root = Path(repo_root)
        self._env = dict(env or {})
        self._options = (strict_threads, array_wrap, fstring_mode)
        self.separate_states = separate_states
        self._states = {}
        self._saved_env = {}
        self._tickers = []
        self.run_dir = None
        self.lua = None
        self.fg = None

    # -- life cycle -----------------------------------------------------------------------

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.close()

    def start(self):
        self.run_dir = Path(tempfile.mkdtemp(prefix="fakegame-"))
        self._set_environment({"HARNESS_RUN_DIR": str(self.run_dir), **self._env})
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        shared = (self.repo_root / "mod" / "shared").as_posix()
        self.lua.globals().package.path = f"{shared}/?/?.lua;{shared}/?.lua;" + self.lua.globals().package.path
        self.fg = self.lua.execute(PRELUDE.read_text(encoding="utf-8"))
        self.fg.strict_threads, self.fg.array_wrap, self.fg.fstring_mode = self._options

    def close(self):
        if self.lua is not None:
            # Lua closes its open files when it collects them. Windows cannot delete open files.
            self.lua.execute("collectgarbage()")
            self.lua = self.fg = None
        self._restore_environment()
        if self.run_dir is not None:
            shutil.rmtree(self.run_dir, ignore_errors=True)
            self.run_dir = None

    def _set_environment(self, values):
        for name, value in values.items():
            self._saved_env.setdefault(name, os.environ.get(name))
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = str(value)

    def _restore_environment(self):
        for name, old in self._saved_env.items():
            if old is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = old
        self._saved_env = {}

    # -- building the world ---------------------------------------------------------------

    def obj(self, class_name, _path=None, **props):
        """A fake UObject. It is found by FindFirstOf(class_name) while it is valid."""
        return self.fg.object(class_name, self.lua.table_from(props), _path)

    def array(self, items=(), wrap=None, visible=None):
        """A fake TArray. visible() returns how many items the mod may see now."""
        return self.fg.array(self.lua.table_from(list(items)), self.lua.table_from(
            {k: v for k, v in (("wrap", wrap), ("visible", visible)) if v is not None}))

    def struct(self, **fields):
        """A struct is a plain Lua table."""
        return self.lua.table_from(fields)

    def text(self, value):
        """Text in the current mode: an FString-like value or a plain string."""
        return self.fg.text(value)

    def method(self, obj, name, fn):
        """Register obj:name(...). fn is called as fn(obj, ...)."""
        self.fg.set_method(obj, name, fn)

    def finder(self, class_name, fn):
        """Replace the lookup of FindFirstOf(class_name). fn() returns an object or None."""
        self.fg.finders[class_name] = fn

    def static(self, path, obj):
        """Make StaticFindObject(path) return obj."""
        self.fg.statics[path] = obj

    def invalidate(self, obj):
        self.fg.invalidate(obj)

    def spawn(self, obj):
        """Tell the callbacks of NotifyOnNewObject that obj was created."""
        self.fg.spawn(obj)

    # -- time -----------------------------------------------------------------------------

    def now(self):
        return self.fg.now

    def add_ticker(self, fn):
        """fn(seconds) runs on every step, before the loops. The game clock uses this."""
        self._tickers.append(fn)

    def tick(self, seconds=DEFAULT_STEP_SECONDS):
        for ticker in self._tickers:
            ticker(seconds)
        self.fg.step(seconds)

    def advance(self, seconds, step=DEFAULT_STEP_SECONDS):
        for _ in range(round(seconds / step)):
            self.tick(step)

    def run_until_idle(self, limit_seconds=400, step=DEFAULT_STEP_SECONDS):
        """Step until no LoopAsync loop is alive. Returns the seconds used. Fails at the limit."""
        used = 0.0
        while self.fg.live_loops() > 0:
            if used >= limit_seconds:
                raise TimeoutError(f"loops still alive after {limit_seconds} fake seconds")
            self.tick(step)
            used += step
        return used

    # -- events from the player -----------------------------------------------------------

    def press(self, key_name, *modifier_names):
        """Press a key, for example press("F8") or press("R", "CONTROL"). Returns the bind count."""
        key = self.lua.eval(f"Key.{key_name}")
        modifiers = self.lua.table_from([self.lua.eval(f"ModifierKey.{m}") for m in modifier_names])
        return self.fg.press(key, modifiers)

    def fire_hook(self, path, *args):
        """Call the pre and post callbacks that the mod registered with RegisterHook(path)."""
        self.fg.fire_hook(path, *args)

    # -- running a mod and reading its output ---------------------------------------------

    def state(self, name, fresh=False):
        """The Lua state of a mod (a name), or None when the game runs all mods in one state. `fresh` makes a new state."""
        if not self.separate_states:
            return None
        if fresh or name not in self._states:
            self._states[name] = self.fg.new_state()
        return self._states[name]

    def exec(self, code, state=None):
        """Run Lua code in the game state, or in the state of the mod `state`. Returns what the chunk returns."""
        env = self.state(state) if state else None
        if env is None:
            return self.lua.execute(code)
        return self.fg.run_in_state(env, code, "=exec")

    def load_mod(self, name):
        return self.load_script(self.repo_root / "mod" / name / "Scripts" / "main.lua", state=name, fresh=True)

    def load_script(self, path, state=None, fresh=False):
        source = Path(path).read_text(encoding="utf-8")
        env = self.state(state, fresh) if state else None
        if env is not None:
            return self.fg.run_in_state(env, source, "@" + Path(path).as_posix())
        run = self.lua.eval("function(src, name) local f, e = load(src, name); if not f then error(e, 0) end; return f() end")
        return run(source, "@" + Path(path).as_posix())

    def printed(self):
        return [line for line in self.fg.printed.values()]

    def files(self):
        return sorted(p.name for p in self.run_dir.iterdir())

    def read_text(self, name):
        return (self.run_dir / name).read_text(encoding="utf-8")

    def read_json(self, name):
        return json.loads(self.read_text(name))

    def read_jsonl(self, name):
        return [json.loads(line) for line in self.read_text(name).splitlines() if line.strip()]

    def log_lines(self):
        if "mod.log" not in self.files():
            return []
        return self.read_text("mod.log").splitlines()
