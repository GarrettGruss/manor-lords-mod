# Design: region state and a size limit

## Context

The legacy source is `openspec/changes/archive/2026-10-16-legacy-m01-mod-state/README.md`. The Tags design is in `openspec/changes/archive/2026-10-15-legacy-24-mod-save-state/README.md`. Evidence that region Tags survive a save is in `openspec/changes/archive/2026-10-15-legacy-24-mod-save-state/implementation-notes/persistence-tests.md`.

## Open questions

1. How many entries and how long can the Tags be? Answer: the limit spike (task 1.1). The result sets the limit in ModState.
2. Is a region Tags entry kept for a vassal region that the player settles and then loses? Answer: the region spike (task 1.2).
3. When is option C (side file plus id) needed? Decide only if the spike shows the Tags are too small. Not part of this change.
4. What is the budget for save and load time with the Tags full? Set it from the spike. The spec scenario then states it as a range.
