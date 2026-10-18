# Spec 33: Meshy materials

Status: fixed and shown in the game (2026-10-18). Issue: #237. Branch: `feat/33-meshy-materials`.

## Goal
Meshy models must show their texture in the game, not flat grey.

## Non-goals
New Meshy models. A new shader library for mods.

## Result
See `implementation-notes/cause-and-fix.md`. Acceptance: one model (spec 30 Wagenburg) shows its texture in a harness screenshot (`implementation-notes/after-instance.png`); the import scripts make the fix by default; the skill is updated.
