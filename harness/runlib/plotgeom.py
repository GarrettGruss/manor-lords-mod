"""Geometry of burgage plots for the command `plot_field_place` (spec 15, part 8).

Units are game units (100 = 1 m). A row of plots is side by side. Each plot has a front edge and a back edge.
Shape taken from a field the game made: 7.5 m wide, 30 m deep, the house stands at about 0.22 of the depth,
the facade (line between house half and garden half) at 0.5 and the garden centre at 0.78.
The corner order is front start, front end, back end, back start. The depth direction is the width direction turned by -90 degrees.
"""

from __future__ import annotations

import math

PLOT_WIDTH = 750.0
PLOT_DEPTH = 3000.0
HOUSE_AT = 0.22
FACADE_AT = 0.5
GARDEN_AT = 0.78
MAX_PLOTS = 12


def _yaw_quaternion(yaw: float) -> tuple[float, float, float, float]:
    return (0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2))


def _point(origin, width_dir, depth_dir, across: float, down: float, z: float) -> list[float]:
    return [origin[0] + width_dir[0] * across + depth_dir[0] * down, origin[1] + width_dir[1] * across + depth_dir[1] * down, z]


def one_plot(origin, width_dir, depth_dir, index: int, width: float, depth: float, z: float) -> dict:
    start = index * width
    corner = lambda across, down: _point(origin, width_dir, depth_dir, start + across, down, z)  # noqa: E731
    c0, c1, c2, c3 = corner(0, 0), corner(width, 0), corner(width, depth), corner(0, depth)
    e0, e1 = corner(width, depth * FACADE_AT), corner(0, depth * FACADE_AT)
    facade_a, facade_b = e1, e0
    yaw = math.atan2(depth_dir[1], depth_dir[0]) - math.pi / 2
    qx, qy, qz, qw = _yaw_quaternion(yaw)
    house = corner(width / 2, depth * HOUSE_AT)
    garden = corner(width / 2, depth * GARDEN_AT)
    return {
        "corners": [c0, c1, c2, c3],
        "border": [c0, c1, c2, c3, c0],
        "ext_corners": [e1, e0, c2, c3],
        "ext_border": [e1, e0, c2, c3, e1],
        "primary": house + [qx, qy, qz, qw],
        "extension": garden + [qx, qy, qz, qw],
        "facade": [facade_a, facade_b],
    }


def make_plots(start_x: float, start_y: float, z: float, away_x: float, away_y: float, count: int,
               width: float = PLOT_WIDTH, depth: float = PLOT_DEPTH) -> list[dict]:
    """`count` plots side by side. The front edge starts at (start_x, start_y). The back of the plots lies in the direction (away_x, away_y)."""
    if not 1 <= count <= MAX_PLOTS:
        raise ValueError(f"make_plots: count must be from 1 to {MAX_PLOTS}")
    length = math.hypot(away_x, away_y)
    if length == 0:
        raise ValueError("make_plots: the away direction must not be zero")
    depth_dir = (away_x / length, away_y / length)
    width_dir = (-depth_dir[1], depth_dir[0])
    return [one_plot((start_x, start_y), width_dir, depth_dir, index, width, depth, z) for index in range(count)]
