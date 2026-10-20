## 1. Setup (owner)

- [x] 1.1 The owner installs Node.js 22.12+ and `meshy-cli@0.4.3` and signs in with `meshy auth login --device` on the Pro account. Verified by `meshy --version` and a balance check. (Done 2026-10-19: `meshy` 0.4.3 installed, MESHY_API_KEY set, balance 1010.)

## 2. Model

- [x] 2.1 Generate one house with `meshy-cli` (private, at most 2 generations), download FBX or GLB to `runs/genmesh/meshy-agent-house/`. Verified by the files and `notes/generation.md` (task id, credits, prompt or images).
- [x] 2.2 Import over one vanilla house mesh with `import_replace_mesh.py`, cook, and build the test pak with `pakmod.py`. Verified by the pak listing and a key grep (0 matches).

## 3. Test scenario

- [x] 3.1 Add the test scenario that builds the house and takes screenshots. Verified by a real run with the pak and one without.
- [x] 3.2 Commit compressed screenshots to `evidence/` with `evidence/README.md`. Verified by review of the pictures.

## 4. Close

- [ ] 4.1 Update the skills `harness-meshy-agent` and `harness-meshy`, the wiki and `CHANGELOG.md`. Verified by `wiki.py check`.
- [ ] 4.2 Fill the test results table and evidence links of the implementation pull request.
