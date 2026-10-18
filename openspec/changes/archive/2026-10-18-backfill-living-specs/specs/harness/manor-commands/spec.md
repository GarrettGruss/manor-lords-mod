# Spec Delta

## Purpose

Named harness commands that read and change the manor of the player village: its modules, its stored goods, its worker slots, its planner blueprints, its wall and keep meshes and its garrison limit. Tests and spikes use them without the mouse.

## ADDED Requirements

### Requirement: Manor state is read only
The harness SHALL answer `manor_state` and `manor_worker_state` without changing the game. `manor_state` SHALL list each manor module of the player village with its type, built flag, goods, capacity and a flag for the region manor. `manor_worker_state` SHALL add slots, job, assigned families and the number of unassigned families.

#### Scenario: A village without a manor
- **WHEN** a client sends `manor_state` and the village has no manor module
- **THEN** the reply is ok with `count` 0 and `region_has_manor` false
- Checked by `harness/tests/test_fakegame_harnessmanor.py`.

#### Scenario: A Keep site that is not built
- **WHEN** a Keep site exists and a client sends `manor_state`
- **THEN** the site is listed with `built` false
- **AND** other building types are not listed as manor modules
- Checked by `harness/tests/test_fakegame_harnessmanor.py`.

### Requirement: A Keep site can be finished by a shortcut
The harness SHALL finish a manor site at once on `finish_manor_site` and register it as the region manor. The command SHALL refuse a type that is not a manor type, a village with no unfinished site of that type, and a site that is already built.

#### Scenario: Finish a Keep site
- **WHEN** a client sends `finish_manor_site` with `type` 57 and an unfinished Keep exists
- **THEN** the reply is ok and the module is built and is the region manor
- Checked by `harness/tests/test_fakegame_harnessmanor.py`.

#### Scenario: Finish with no site or a wrong type
- **WHEN** a client sends `finish_manor_site` for a type with no unfinished site, or for a type that is not a manor type
- **THEN** the reply is not ok and the error names the problem
- **AND** a built Keep is not finished a second time
- Checked by `harness/tests/test_fakegame_harnessmanor.py`.

### Requirement: Manor goods are stored by put and take
The harness SHALL add goods to a built manor module on `manor_put` and remove goods on `manor_take`. Each reply SHALL give the amount of the good in the module and in the region stock before and after. The harness SHALL refuse a put that would pass the module capacity (200 units by default), a take of more than the module holds, a put into a site that is not built, and a good or amount outside the allowed range. A refused command SHALL change nothing.

#### Scenario: Put and take
- **WHEN** a client sends `manor_put` for 20 units of a good and then `manor_take` for 5 units
- **THEN** the module holds 20 and then 15 units
- **AND** the region stock changes by the same amounts
- Checked by `harness/tests/test_fakegame_harnessmanor.py`.

#### Scenario: A put above the capacity
- **WHEN** a client sends `manor_put` and the module total would pass its capacity
- **THEN** the reply is not ok and the module is unchanged
- Checked by `harness/tests/test_fakegame_harnessmanor.py`.

#### Scenario: A take of more than the module holds
- **WHEN** a client sends `manor_take` for more units than the module holds
- **THEN** the reply is not ok and the module is unchanged
- Checked by `harness/tests/test_fakegame_harnessmanor.py`.

#### Scenario: Goods stay after game time
- **WHEN** goods were put into the manor and game days pass
- **THEN** the goods stay in the manor
- Checked by `harness/scenarios/manor_storage.py`.

### Requirement: The manor module can get worker slots and workers
The harness SHALL give a built manor module the worker slots and role of a Storehouse (`job` 45) or a Granary (`job` 44) on `manor_worker_slot`, with `slots` from 1 to 6. It SHALL assign a family on `manor_assign_worker` and take every family off on `manor_unassign_workers`. Each change SHALL be read back and fail loudly if the building does not report it. A change lasts until the game ends.

#### Scenario: Slots and a worker
- **WHEN** a client sends `manor_worker_slot` with `job` 45 and `slots` 3, and then `manor_assign_worker`
- **THEN** `manor_worker_state` shows 3 slots, the storehouse role and one assigned family
- Checked by `harness/tests/test_fakegame_harnessmanor.py`.

#### Scenario: Bad worker input
- **WHEN** a client sends `manor_worker_slot` with a job other than 44 or 45, or `slots` outside 1 to 6, or on a site that is not built
- **THEN** the reply is not ok
- **AND** `manor_assign_worker` is refused without a slot, with all slots taken, with no free family, and for a family index that does not exist or already has a workplace
- Checked by `harness/tests/test_fakegame_harnessmanor.py`.

#### Scenario: Workers carry goods into the manor
- **WHEN** a worker is assigned to the manor module and game days pass
- **THEN** the manor receives goods only when a worker is assigned
- Checked by `harness/scenarios/manor_storage_workers.py`.

### Requirement: Planner blueprints can be added without the mouse
The harness SHALL add a manor planner blueprint on `manor_blueprint_add` and open or close the planner on `manor_planner`. A blueprint request SHALL give `type`, `x`, `y` and `z`, and MAY give `yaw`, `mesh`, `commit` and a commit `order`. A refused request SHALL spawn nothing.

#### Scenario: Missing fields
- **WHEN** a client sends `manor_blueprint_add` without `x`, `y` and `z`, or without `type`
- **THEN** the reply is not ok and the error says that type, x, y and z are required
- Checked by `harness/tests/test_fakegame_harnesswalls.py`.

#### Scenario: No manor or no matching blueprint
- **WHEN** a client sends `manor_blueprint_add` or `manor_planner` and the player has no manor, or no blueprint of that type exists
- **THEN** the reply is not ok and nothing is spawned
- **AND** a `mesh` path does not skip the manor check
- Checked by `harness/tests/test_fakegame_harnesswalls.py`.

#### Scenario: A module is added and committed in the game
- **WHEN** a client sends `manor_blueprint_add` with `commit` true on a village with a manor
- **THEN** the blueprint count rises by 1 and the module is converted to a building
- Not checked yet.

#### Scenario: An unknown commit order
- **WHEN** a client sends `manor_blueprint_add` or `manor_planner` with an `order` other than `hand`, `convert_first` or `convert_only`
- **THEN** the reply is not ok and nothing is spawned
- Not checked yet.

### Requirement: Wall and keep meshes of one manor can be changed
The harness SHALL set the wall mesh and the keep mesh of one manor on `wagen_apply` with `manor`, `wall_mesh` and `keep_mesh`. One of the two meshes MAY be left out. `wagen_state` SHALL count the wall parts by mesh for each manor. `wagen_revert` SHALL restore every mesh that `wagen_apply` changed. The harness SHALL refuse a request without a manor id and a mesh path that cannot be loaded. It SHALL change only the mesh of building actors of the chosen manor.

#### Scenario: Apply and revert
- **WHEN** a client sends `wagen_apply` for a manor with a mesh path and then `wagen_revert`
- **THEN** the apply reply gives the number of wall and keep parts changed
- **AND** the revert reply gives the number of parts restored
- Not checked yet.

#### Scenario: A mesh that cannot be found
- **WHEN** a client sends `wagen_apply` with a mesh path that does not load
- **THEN** the reply is not ok and no mesh is changed
- Not checked yet.

### Requirement: The garrison limit bonus is opt in
The harness SHALL change the garrison limit only when the game starts with `HARNESS_GARRISON_BONUS` set to a number other than 0. The bonus SHALL apply while a built manor module of type `HARNESS_GARRISON_MODULE_TYPE` (default 83) exists. With the variable unset or 0, the harness SHALL NOT install the hook.

#### Scenario: The variable is not set
- **WHEN** the game starts without `HARNESS_GARRISON_BONUS`
- **THEN** no hook is installed and the garrison limit is unchanged
- Not checked yet.

#### Scenario: The variable is set
- **WHEN** the game starts with `HARNESS_GARRISON_BONUS` 24 and a built module of the chosen type exists
- **THEN** the limit that script callers read is higher by 24
- Not checked yet.
