# harness/mesh-pipeline Specification

## Purpose
The mesh pipeline makes a 3D model for the game: reference images from Gemini, a textured mesh from Meshy, a headless Unreal Editor import with a game material, a cook, and a mod pak. Cost caps and logs keep the paid API calls under control.

## Requirements

### Requirement: Reference images from Gemini
The tool `harness/tools/genimage.py` SHALL generate 1 to 4 images for each call. It SHALL read the key from `GEMINI_API_KEY` (environment, else Windows user scope), SHALL fail with a clear message when the key is missing, and SHALL NOT print the key. It SHALL take 0 to 3 reference images with `--ref` and send them with the prompt in the same request. It SHALL append each call to `runs/genimage/log.jsonl`. With `--list-models` it SHALL list the image models the key can use.

#### Scenario: Count out of range
- **WHEN** `--count` is 0 or above 4
- **THEN** the tool stops with a message that gives the range
- Checked by `harness/tests/test_genimage.py`.

#### Scenario: A call is logged
- **WHEN** images are generated
- **THEN** one line is added to `runs/genimage/log.jsonl` with the model, the prompt, the output files and their sizes, and the reference files with their SHA-256 hashes
- Checked by `harness/tests/test_genimage.py`.

#### Scenario: References are sent with the prompt
- **WHEN** `--ref` is given one to three times with a Gemini model
- **THEN** the request holds one image part for each reference, in the given order, followed by the text prompt
- Checked by `harness/tests/test_genimage.py`.

#### Scenario: Too many references
- **WHEN** `--ref` is given four or more times
- **THEN** the tool stops with a message that gives the range, and makes no API call
- Checked by `harness/tests/test_genimage.py`.

#### Scenario: A bad reference file
- **WHEN** a reference file is missing, is not PNG, JPEG or WebP, or is larger than 7 MB
- **THEN** the tool stops with a message that names the file and the reason, and makes no API call
- Checked by `harness/tests/test_genimage.py`.

#### Scenario: References with an Imagen model
- **WHEN** `--ref` is given with a model whose name starts with `imagen`
- **THEN** the tool stops with a message that only Gemini models take references, and makes no API call
- Checked by `harness/tests/test_genimage.py`.

### Requirement: Mesh generation with cost caps
The tool `harness/tools/genmesh.py multi` SHALL send 1 to 4 images to a Meshy multi-image-to-3D task and download `model.fbx`, `model.glb` and the texture maps to the output folder. It SHALL refuse a call whose estimated cost is above 60 credits, or when the credits logged today plus the estimate are above 200. A refused call SHALL make no API call. It SHALL read the key from `MESHY_API_KEY` and SHALL NOT print or log it.

#### Scenario: A successful task
- **WHEN** a task succeeds
- **THEN** the credits of the task are logged and the model and texture files are downloaded
- Checked by `harness/tests/test_genmesh.py`.

#### Scenario: The day cap
- **WHEN** 190 credits are already logged today
- **THEN** the call is refused and no API call is made
- Checked by `harness/tests/test_genmesh.py`.

#### Scenario: A failed task
- **WHEN** the task ends FAILED
- **THEN** the tool stops with the task error and logs the status
- Checked by `harness/tests/test_genmesh.py`.

#### Scenario: Image count
- **WHEN** no image or more than four images are given
- **THEN** the tool stops with a message
- Checked by `harness/tests/test_genmesh.py`.

### Requirement: The task id is never lost
The tool SHALL log the Meshy task id to `runs/genmesh/log.jsonl` as soon as the task is created, before it polls. The command `resume --task <id> --out <dir>` SHALL download an existing task, create no new task and log 0 credits.

#### Scenario: Timeout while polling
- **WHEN** polling fails after the task was created
- **THEN** the log already holds the task id with the kind `task-created`
- Checked by `harness/tests/test_genmesh.py`.

#### Scenario: Resume
- **WHEN** `resume` runs for a finished task
- **THEN** no POST is sent, the files are downloaded, and the log entry has kind `resume` and 0 credits
- Checked by `harness/tests/test_genmesh.py`.

### Requirement: Headless import in the Unreal Editor
The scripts in `mod/HarnessActions/ue/` SHALL import an FBX as a static mesh in a separate UE 5.5 project, driven by environment variables. `import_mesh.py` SHALL set the real size and cap textures (1024 for colour and normal, 512 for the others). `import_replace_mesh.py` SHALL scale the mesh so the longest floor side equals `TARGET_CM` and copy it to the path of a vanilla mesh. `make_bm.py` SHALL make a `BM_` building Blueprint class from named parts.

#### Scenario: Import
- **WHEN** `import_mesh.py` runs with `MESH_FBX`, `MESH_NAME` and `MESH_DEST`
- **THEN** a static mesh exists at the destination and the log gives its size, vertices and material
- Not checked yet.

### Requirement: Game-based material instance
Every imported Meshy mesh SHALL use a material instance (`MI_Meshy`) of the game master material `/Game/NotStronghold/Buildings/TudorWall/tudorWall01`, with the texture parameters `d`, `n`, `spec` and `AO`. The pak SHALL NOT contain the stub master material. A mesh with its own imported material would show grey in the game.

#### Scenario: Material instance
- **WHEN** `meshy_material.py` runs during an import
- **THEN** `MI_Meshy` is an instance of the game master material with the Meshy textures set
- Not checked yet.

### Requirement: Re-cook an old pak
The tool `harness/tools/recook_meshy_pak.py <old pak> <new name> <mesh folder>` SHALL unpack an old pak, remove the files of the old material and the emission and metallic maps, copy the cooked `MI_Meshy` and textures from the UE workspace, and build a new pak. It SHALL NOT change the old pak and SHALL keep the data files.

#### Scenario: Re-cook
- **WHEN** the tool runs for an old pak
- **THEN** a new pak with the cooked material exists and the old pak is unchanged
- Not checked yet.

### Requirement: The Meshy agent CLI makes a house that is placed in the game
The harness SHALL have a test scenario that builds one vanilla house whose mesh was replaced by a model generated with `meshy-cli` and imported with the mesh pipeline. The model SHALL be generated privately on the Pro account and SHALL NOT be published to the Meshy Community page.

#### Scenario: The generated house stands in the world
- **WHEN** the test scenario runs with the test pak and builds the house
- **THEN** the building exists, uses the replaced mesh, and the screenshots show the generated house
- Checked by `harness/scenarios/meshy_house.py` (test scenario `meshy-agent-house`), runs 20261020-041549-7439 (pak) and 20261020-041739-4836 (vanilla). Pictures: `evidence/`. The mesh path stays the vanilla path, so the pictures tell the two runs apart.

#### Scenario: The run without the pak shows the vanilla house
- **WHEN** the same test scenario runs without the test pak
- **THEN** the building exists and uses the vanilla mesh
- Checked by `harness/scenarios/meshy_house.py` (test scenario `meshy-agent-house`), runs 20261020-041549-7439 (pak) and 20261020-041739-4836 (vanilla). Pictures: `evidence/`. The mesh path stays the vanilla path, so the pictures tell the two runs apart.
