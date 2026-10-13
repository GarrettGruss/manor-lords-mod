import math
import unittest

import runlib_path  # noqa: F401
from runlib import plotgeom


class PlotGeometryTests(unittest.TestCase):
    def test_plots_are_side_by_side_with_the_right_size(self):
        plots = plotgeom.make_plots(0, 0, 10, 0, 1, 3)
        self.assertEqual(len(plots), 3)
        c0, c1, c2, c3 = plots[1]["corners"]
        self.assertAlmostEqual(math.dist(c0[:2], c1[:2]), plotgeom.PLOT_WIDTH)
        self.assertAlmostEqual(math.dist(c1[:2], c2[:2]), plotgeom.PLOT_DEPTH)
        self.assertEqual(plots[0]["corners"][1], plots[1]["corners"][0])

    def test_shape_matches_the_command_rules(self):
        plot = plotgeom.make_plots(5, 5, 7, 1, 1, 1)[0]
        self.assertEqual((len(plot["primary"]), len(plot["extension"]), len(plot["facade"])), (7, 7, 2))
        self.assertTrue(all(len(p) == 3 and p[2] == 7 for p in plot["corners"] + plot["border"]))
        self.assertEqual(plot["border"][0], plot["border"][-1])

    def test_house_is_near_the_front_and_the_garden_is_behind_it(self):
        plot = plotgeom.make_plots(0, 0, 0, 0, 1, 1)[0]
        self.assertLess(plot["primary"][1], plotgeom.PLOT_DEPTH * 0.3)
        self.assertGreater(plot["extension"][1], plot["facade"][0][1])

    def test_rotation_is_a_unit_quaternion_about_z(self):
        qx, qy, qz, qw = plotgeom.make_plots(0, 0, 0, 3, -4, 1)[0]["primary"][3:]
        self.assertEqual((qx, qy), (0.0, 0.0))
        self.assertAlmostEqual(qz * qz + qw * qw, 1.0)

    def test_bad_input_fails_loudly(self):
        with self.assertRaises(ValueError):
            plotgeom.make_plots(0, 0, 0, 0, 0, 1)
        with self.assertRaises(ValueError):
            plotgeom.make_plots(0, 0, 0, 0, 1, 0)


if __name__ == "__main__":
    unittest.main()
