"""Mock tests for HarnessUnits and HarnessRaids (spec 10): the census, the kill and the loot commands, on fake units."""

import json
import unittest

import fakegame_path  # noqa: F401
from fakegame import FakeGame


def build_units(game):
    """One player pawn, one bandit pawn with squad 5 (3 units, one carries loot) and 2 villagers without a squad."""
    game.exec("FName = function(text) return { fname = text } end")
    player = game.obj("PawnCPP", isMainPlayer=True, isBandit=False, isAI=False, commandedSquads=game.array([]))
    bandit = game.obj("PawnCPP", isMainPlayer=False, isBandit=True, isAI=True,
                      commandedSquads=game.array([game.struct(Value=5)]))
    units = []
    for index in range(5):
        squad = 5 if index < 3 else 0
        units.append(game.obj("SMUnit", dead=False, assignedSquadID=game.struct(Value=squad), currentUnitRole=5 if squad else 0,
                              ItemsLooted=4 if index == 0 else 0, morale=1.0, combatExperience=0.0,
                              realPos=game.struct(X=10.0 * index, Y=2.0, Z=3.0)))
    return player, bandit, units


class CensusTests(unittest.TestCase):
    def test_counts_by_side_and_loot(self):
        with FakeGame() as game:
            build_units(game)
            lua = game.lua
            census = lua.eval('(function() return require("HarnessUnits").census({sample = 2}) end)()')
            self.assertEqual(census["units"], 5)
            self.assertEqual(census["by_side"]["bandit"], 3)
            self.assertEqual(census["by_side"]["civil"], 2)
            self.assertEqual(census["loot"]["total"], 4)
            self.assertEqual(census["loot"]["carriers"], 1)
            self.assertEqual(len(census["sample"]), 2)  # sample rows are not civil
            self.assertEqual(census["squads"][1]["size"], 3)

    def test_the_sample_is_bounded(self):
        with FakeGame() as game:
            build_units(game)
            census = game.lua.eval('(function() return require("HarnessUnits").census({sample = 9999}) end)()')
            self.assertLessEqual(len(census["sample"]), 30)


class CommandTests(unittest.TestCase):
    def run_command(self, game, command, **fields):
        folder = game.run_dir / "commands"
        folder.mkdir(exist_ok=True)
        number = len(list(folder.glob("*.json"))) // 2 + 1
        body = {"id": f"{number:04d}", "command": command, **fields}
        (folder / f"{number:04d}.json").write_text(json.dumps(body), encoding="utf-8")
        game.advance(1)
        return json.loads((folder / f"{number:04d}.result.json").read_text(encoding="utf-8"))

    def test_set_loot_then_census_reads_it(self):
        with FakeGame() as game:
            build_units(game)
            game.load_mod("HarnessActions")
            game.advance(1)
            answer = self.run_command(game, "set_unit_loot", side="bandit", count=2, amount=7)
            self.assertEqual((answer["ok"], answer["changed"]), (True, 2))
            census = self.run_command(game, "units_census")["census"]
            self.assertEqual(census["loot"]["total"], 14 + 0)  # 7 + 7: the old value 4 was replaced

    def test_bad_input_is_refused(self):
        with FakeGame() as game:
            build_units(game)
            game.load_mod("HarnessActions")
            game.advance(1)
            self.assertIn("side must be", self.run_command(game, "kill_units", side="king")["error"])
            self.assertIn("count must be", self.run_command(game, "kill_units", side="bandit", count=9999)["error"])

    def test_kill_marks_units_dead(self):
        with FakeGame() as game:
            _, _, units = build_units(game)
            for unit in units:
                game.method(unit, "just_die", game.lua.eval("function(self) self.dead = true end"))
            game.load_mod("HarnessActions")
            game.advance(1)
            answer = self.run_command(game, "kill_units", side="bandit", count=2)
            self.assertEqual(answer["killed"], 2)
            self.assertEqual(answer["after"]["dead"], 2)

    def test_spawn_raiders_passes_a_vector(self):
        with FakeGame() as game:
            build_units(game)
            seen = []
            engine = game.obj("RTSMultiEngineCPP", playerRef=None)
            game.method(engine, "spawnRaiders", lambda this, squads, center: seen.append((squads, center["X"], center["Y"])))
            game.load_mod("HarnessActions")
            game.advance(1)
            answer = self.run_command(game, "spawn_raiders", squads=2, x=5, y=6)
            self.assertTrue(answer["ok"], answer)
            self.assertEqual(seen, [(2, 5, 6)])
            self.assertIn("squads must be", self.run_command(game, "spawn_raiders", squads=99)["error"])


if __name__ == "__main__":
    unittest.main()
