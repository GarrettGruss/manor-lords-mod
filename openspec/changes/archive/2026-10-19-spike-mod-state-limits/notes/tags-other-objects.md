# Tags of an AI lord and a building (task 1.2)

Same runs as `tags-limits.md`: write `spike-tags-w2`, `spike-tags-w3`; load `spike-tags-r1`, `spike-tags-r2`.

- Marker `spike:mrk00001=xxxx...` (43 chars) was appended with `FName` to the first `PawnCPP_AI` (a lord, 4 lords on the map) and to the first `SMBuildingMaster` (a building).
- After save and load (r1 and r2 scan the lords and buildings): exactly one lord holds the marker and exactly one building holds the marker. Both checks passed in both load runs. **Tags on AI lord pawns and on buildings survive a save and a load.**
- Caution: the index in `FindAllOf` order is not a stable id. The scan found the marker at index 1 in the first load run (r1); do not rely on the index in a feature. Find the object by its own data or by the marker itself.
- No crash.
