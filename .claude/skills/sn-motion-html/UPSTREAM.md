# Upstream

Copied from https://github.com/OpenSenseNova/SenseNova-Skills at commit 7838651, folder `skills/sn-motion-html`, MIT License (see `LICENSE`). `references/upstream-overview.md` is the upstream `docs/sn-motion-html.md`.

## Changes in this repo

- `scripts/seedance_pipeline.py`: key lookup, `--max-clips`, spend log, no retry on account errors.
- `scripts/export_video.py`: new. Video export of the story page.
- `assets/template/src/motion-runtime.js`: export mode (`?export=1`).
- `assets/template/styles.css`: export mode rules at the end.
- `assets/template/content/timing.json`: new. Video timing.
- `assets/template/.gitignore`, `assets/template/.env.example`.
- `SKILL.md`: `uv run python`, and the section "Changes in this repo".
- `spec/`, `tests/`: new.
