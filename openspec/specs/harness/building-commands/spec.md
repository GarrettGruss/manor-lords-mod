# harness/building-commands Specification

## Purpose
Named harness commands that build, read, change and remove buildings, walls and building parts in the player village without the mouse. Tests and spikes use them to set up walls, ruins, construction sites, composite buildings, burgage plots and squad orders.

## Requirements

### Requirement: Free walls are read from the road list
The harness SHALL answer `wall_state` with every wall road of the world and no other road. A wall road has road type 3 or a wall type, and a spline length above 0. Each row SHALL give the road id, wall name, blueprint flag, mesh count, length and middle point. The reply SHALL also give the total, the count by wall name and the number of all roads. `wall_state` SHALL NOT change the game.

#### Scenario: A planner wall and a plain road
- **WHEN** a planner wall and a plain road exist and a client sends `wall_state`
- **THEN** the planner wall is listed with its wall name and mesh count
- **AND** the plain road is not listed
- Checked by `harness/tests/test_fakegame_harnesswalls.py`.

### Requirement: A committed road can become a wall and be removed
The harness SHALL switch the road tool on `road_mode`, commit the drawn road on `road_commit`, turn a road into a wall on `wall_make` with `wall_type` 2, 3 or 4, and remove a wall road on `wall_remove`. A refused command SHALL change nothing.

#### Scenario: Build and remove a wooden wall
- **WHEN** a client sends `road_mode`, `road_commit`, `wall_make` with `wall_type` 2 and then `wall_remove`
- **THEN** the road is listed by `wall_state` as a wooden wall with meshes after `wall_make`
- **AND** it is not listed after `wall_remove`
- Checked by `harness/tests/test_fakegame_harnesswalls.py`.

#### Scenario: Stone walls
- **WHEN** a client sends `wall_make` with `wall_type` 3 or 4
- **THEN** the road has more meshes than a wooden wall of the same length
- Checked by `harness/tests/test_fakegame_harnesswalls.py`.

#### Scenario: Bad wall input
- **WHEN** a client sends `road_mode` with a value that is not a boolean, `road_commit` with no points, or `wall_make` with `wall_type` 1
- **THEN** the reply is not ok and the error names the problem
- **AND** `wall_remove` of a plain road is refused
- Checked by `harness/tests/test_fakegame_harnesswalls.py`.

### Requirement: Blocking wall pieces can be spawned along a road
The harness SHALL spawn blocking palisade pieces along a road on `wall_pieces` with `road` and `step` (at least 50 cm, default 200). It SHALL destroy only the pieces it made for a road on `wall_pieces_clear`. It SHALL refuse a request that needs more than 400 pieces. `path_state` SHALL read the size of the global obstacle list and SHALL NOT change it.

#### Scenario: Pieces along a road
- **WHEN** a client sends `wall_pieces` for a wall road and then `wall_pieces_clear` for the same road
- **THEN** the first reply gives the number of pieces spawned and the obstacle count before and after
- **AND** the second reply destroys those pieces only
- Not checked yet.

#### Scenario: Too many pieces
- **WHEN** a client sends `wall_pieces` with a `step` that needs more than 400 pieces, or a `step` below 50
- **THEN** the reply is not ok and nothing is spawned
- Not checked yet.

### Requirement: Building and mesh facts can be read
The harness SHALL read, without changing the game: `building_health` of one building id, `mesh_users` and `mesh_actors` by mesh name, `master_site` for a building master built or not, and `building_sites` for the buildings of the village. `building_sites` SHALL list at most 40 rows.

#### Scenario: Health of one building
- **WHEN** a client sends `building_health` for a building id that exists
- **THEN** the reply gives its type, hp, max hp, on-fire flag, rubble flag and built flag
- Checked by `harness/tests/test_fakegame_harnesswalls.py`.

#### Scenario: A site lists the goods it needs
- **WHEN** a client sends `building_sites` with the type of a construction site
- **THEN** the site lists the goods it still needs
- **AND** a built building of that type lists none
- Checked by `harness/tests/test_fakegame_harnessbuild.py`.

#### Scenario: A type above the limit
- **WHEN** a client sends `building_sites` with a type above 600
- **THEN** the reply is not ok
- Checked by `harness/tests/test_fakegame_harnessbuild.py`.

#### Scenario: A missing building
- **WHEN** a client sends `building_health` with an id that no building has, or with no id
- **THEN** the reply is not ok and the error names the problem
- Checked by `harness/tests/test_fakegame_harnesswalls.py`.

### Requirement: Ruins, demolition and rebuild cost can be driven
The harness SHALL burn (`fire`) or collapse (`collapse`, the default) the first built building of a type on `ruin_building`, demolish every ruin on `demolish_ruins`, and lower the amount of a good that a construction site needs on `set_site_cost`. It SHALL NOT raise a cost.

#### Scenario: A building is ruined and the ruin is removed
- **WHEN** a client sends `ruin_building` with `method` fire for a built type and then `demolish_ruins`
- **THEN** the building count of that type falls and the rubble count rises by 1
- **AND** after `demolish_ruins` the rubble count is 0
- Checked by `harness/tests/test_fakegame_harnessbuild.py`.

#### Scenario: A cost can only be lowered
- **WHEN** a client sends `set_site_cost` with an amount below the current need, and then with an amount above it
- **THEN** the first reply is ok and `building_sites` reads the new amount
- **AND** the second reply is not ok
- Checked by `harness/tests/test_fakegame_harnessbuild.py`.

#### Scenario: A rebuild in the game uses the lower cost
- **WHEN** a ruined building is demolished, a new site is placed and its cost is lowered
- **THEN** the builders use no more goods than the lowered cost
- Checked by `harness/scenarios/rebuild_cost.py`.

#### Scenario: Bad ruin or cost input
- **WHEN** a client sends `ruin_building` with no type, a method other than `fire` or `collapse`, or a type that has only a site, or `set_site_cost` for a site or good that does not exist
- **THEN** the reply is not ok and nothing is changed
- **AND** `demolish_ruins` removes ruins only
- Checked by `harness/tests/test_fakegame_harnessbuild.py`.

### Requirement: Unsafe spike commands need an explicit game setting
The harness SHALL refuse the unsafe commands `construction_complete`, `path_obstacles_clear`, `building_stat_write`, `master_part_remove`, `master_part_add` and `master_artisan_set` unless the game runs with `HARNESS_ALLOW_UNSAFE=1`. The refusal SHALL name the variable. With the variable set, each command SHALL still check its own input first.

#### Scenario: The variable is not set
- **WHEN** a client sends any unsafe command and the game has no `HARNESS_ALLOW_UNSAFE=1`
- **THEN** the reply is not ok and the error contains `HARNESS_ALLOW_UNSAFE=1`
- Checked by `harness/tests/test_fakegame_harnesswalls.py`.

#### Scenario: Part commands are refused
- **WHEN** a client sends `master_part_remove`, `master_part_add` or `master_artisan_set` without the variable
- **THEN** the reply is not ok and no part or job is changed
- Checked by `harness/tests/test_fakegame_harnessparts.py`.

#### Scenario: The variable is set
- **WHEN** the game runs with `HARNESS_ALLOW_UNSAFE=1` and a client sends `construction_complete` without a building id
- **THEN** the reply is not ok with an input error, not a refusal for the variable
- Checked by `harness/tests/test_fakegame_harnesswalls.py`.

### Requirement: Parts of a composite building can be read and changed
The harness SHALL list the parts and the extension parts of one building master on `master_parts`, write the region of a site on `master_set_region` and `constructed` on `master_finish`, and read each write back. A request SHALL name the master with `building` or `type`. `master_part_remove` and `master_part_add` SHALL work only in an unsafe game.

#### Scenario: Read parts by type
- **WHEN** a client sends `master_parts` with a `type` that has a built master
- **THEN** the reply gives the part count, the valid part count and up to `limit` part rows
- Checked by `harness/tests/test_fakegame_harnessparts.py`.

#### Scenario: Missing id and type
- **WHEN** a client sends `master_parts` or `master_site` with neither `building` nor `type`
- **THEN** the reply is not ok
- Checked by `harness/tests/test_fakegame_harnessparts.py`.

#### Scenario: A site is changed and read back
- **WHEN** a client sends `master_set_region` and `master_finish` for a site that is not built
- **THEN** the replies show the new region and `constructed` true
- Checked by `harness/tests/test_fakegame_harnessparts.py`.

#### Scenario: A part is hidden
- **WHEN** the unsafe variable is set and a client sends `master_part_remove` with `mode` hide
- **THEN** the part stays in the list and is hidden
- **AND** an index outside the list or an unknown mode is refused
- Checked by `harness/tests/test_fakegame_harnessparts.py`.

#### Scenario: A pak Blueprint is loaded
- **WHEN** a client sends `load_pak_blueprint` with a `name` of letters, digits and underscores
- **THEN** the class `/Game/HarnessMod/<name>` is loaded and kept, or the reply says that the class was not found
- **AND** a `name` with other characters is refused
- Not checked yet.

### Requirement: Artisan and burgage plot commands work without the mouse
The harness SHALL read the artisan state of a master on `master_artisan`, request upgrades on `plot_upgrade`, assign a family to a building on `building_assign_worker`, and shift or place burgage plot fields on `plot_field_shift` and `plot_field_place`, all without the mouse. A refused request SHALL change nothing.

#### Scenario: Artisan state is read without the unsafe variable
- **WHEN** a client sends `master_artisan` and the game has no `HARNESS_ALLOW_UNSAFE=1`
- **THEN** the reply is ok and gives the artisan state
- Checked by `harness/tests/test_fakegame_harnessparts.py`.

#### Scenario: Upgrade and worker requests fail loudly
- **WHEN** a client sends `plot_upgrade` with an id above 1000 or with no building, or `building_assign_worker` without a type or without an own building of that type
- **THEN** the reply is not ok and the error names the problem
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

#### Scenario: Plot field shift and place
- **WHEN** a client sends `plot_field_shift` with `dx` and `dy`, or `plot_field_place` with plot data
- **THEN** the outline and centre move by `dx` and `dy`, or the pawn field holds the plots and is closed
- **AND** bad numbers, bad plot data and an open field are refused
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

#### Scenario: Limits of the plot commands
- **WHEN** a client sends `plot_upgrade` with an `upgrade` above 1000, `plot_field_shift` beyond 10000 or on an open field, or `plot_field_place` with fewer than 1 or more than 12 plots
- **THEN** the reply is not ok
- **AND** `building_assign_worker` is refused when the building has no free worker slot
- Checked by `harness/tests/test_fakegame_harnesshousing.py`.

### Requirement: Squads can be ordered and the order calls recorded
The harness SHALL order one squad to a line across the way to a point on `steer_move`, read a squad on `steer_state`, and drive the select, cursor and right-click steps on `steer_select`, `steer_cursor`, `steer_mouse3d` and `steer_rmb`. It SHALL record the calls of 1 to 60 function paths on `steer_hook` and return them on `steer_hook_log`.

#### Scenario: Bad squad or point
- **WHEN** a client sends `steer_state` or `steer_move` with a squad id below 1, or `steer_move` with an `x` beyond 500000
- **THEN** the reply is not ok and no order is given
- Not checked yet.

#### Scenario: A squad is ordered in the game
- **WHEN** a client sends `steer_move` for a living player squad
- **THEN** the reply gives the side and the squad centre before and after
- Not checked yet.

#### Scenario: A squad that cannot be ordered
- **WHEN** a client sends `steer_move` for a squad that no pawn commands, a squad with no living unit, a `half_width` above 2000 or a coordinate beyond 500000
- **THEN** the reply is not ok and no order is given
- Not checked yet.
