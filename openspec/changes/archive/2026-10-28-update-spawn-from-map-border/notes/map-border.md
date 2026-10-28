# Spike B: map bounds, walkable land and border points

Question: where is the border of the playable area, and how does the mod find a border point on walkable land?

## Map bounds

- The level has one edge actor, class `Medium_Map_Bounds_C` (object `revised_scaled_edge_Blueprint_C_0`, map Jagged_Cliffs). It has six `SplineComponent`s, `Spline1` to `Spline6`, with two points each. Together they are the four sides of the playable square.
- `SplineComponent:GetLocationAtSplinePoint(index, 1)` (1 = world space) returns the world point. Space 0 returns local points (0 and 173632.8), which is wrong.
- Jagged_Cliffs: x from -89459 to 84174, y from -89040 to 84593 (a square of about 173600 units).
- The landscape is much larger than the play area: origin (-223526, -223358), 18 x 18 components of 24805 units each (about 446000 units). So an army 3000 units outside the square still stands on landscape.
- The player manor of the test save (region Nusslohe) is at about (-43956, -63097). The south edge is 28943 units from it, the west edge 48503.
- The class name says "Medium". Other map sizes probably have other class names. `border.lua` tries `Medium_`, `Small_` and `Large_Map_Bounds_C`. When none is found, the log says so and the army starts near the manor as before.

## Walkable land

- The level has no navmesh (`AbstractNavData` only, no `RecastNavMesh`, no `NavMeshBoundsVolume`). `ProjectPointToNavigation` has nothing to project on. No other query for "walkable" or "water" was found in the time box.
- Water: three `BP_Stream_C` actors and no ocean `WaterBody` on this map.
- So the validity of a border point is shown by a test, not computed: `probe-border-points` (`probe_border_points.py`).

Run `20261028-020728-5a13`: 8 squads at 8 points, 3000 units outside the square (N, S, E, W, NE, NW, SE, SW), and a challenge at the manor for the lord. Every squad had 32 living units after the spawn, walked in, and stood at 190 to 15000 units from the manor after 200 game seconds (5 game days). The farthest point (NE corner, 177000 units) arrived last, in about 6 game days. One squad (W) lost 12 units on the way (a fight on the road). No crash.

Verdict: a point 3000 units outside the edge works on this map for all 8 compass points. The mod keeps 5000 units away from the corners (`inset`). It uses the point of the side that is nearest to the target and at least `min_spawn_distance` (30000) away.

## March time

At game speed 3 (a game day is 40 game seconds), from 3000 units outside the edge to the manor: 3 to 8 game days. Run `20261028-025114-297a`: 3 days from the west edge (48500 units). Run `20261028-023857-c6eb`: 5 days. The raid tracker detects arrival (a fifth of the living raiders within 12000 units of the manor), so the mod does not depend on a fixed time. `march_lead_days` (5) only moves the spawn before the planned raid day.

Not verified: other maps, and border points with a cliff or a forest right outside the square.
