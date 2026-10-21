## Why

Issue: #320. The owner asked on PR #317 for proof that the Meshy 3D agent pipeline (`meshy-cli`, skill `harness-meshy-agent`) works end to end: generate a house model and see it placed in the game.

## What Changes

- Generate one house model with `meshy-cli` on the Pro account (private; never published to the Meshy Community page).
- Import it headless in UE 5.5.4 with `import_replace_mesh.py` over the mesh of one vanilla house (the vanilla collision stays), cook it, and ship it in a test pak.
- Add a test scenario that builds that house through HarnessBuild with the test pak and takes screenshots.
- Commit picture evidence.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `harness/mesh-pipeline`: a requirement that the agent CLI pipeline produces a mesh that is placed in the game, with a test scenario.

## Impact

- New test scenario in `harness/scenarios/`, a test pak (not shipped in the Invasion Mod), evidence pictures.
- Needs the owner to install Node.js 22.12+ and `meshy-cli@0.4.3` and to sign in. Costs Meshy credits for one model (capped at 2 generations).
