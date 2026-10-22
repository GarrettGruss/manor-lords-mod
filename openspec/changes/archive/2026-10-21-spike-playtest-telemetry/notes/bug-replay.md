# 1.7 Bug replay

## Question

Would a bug bundle (log with decision lines, low-rate state samples, crash folder, save) have let us find the cause of the bugs #337, #357 and #325?

## Method

Desk review, no game run. Sources: the issue text, the archived change `2026-10-21-fix-native-plunder-test` (proposal), commit `a2bfe59` (fix for #357, `ManorCore.remove_families`), the archived change `2026-10-21-fix-sack-fire-and-goods` (proposal), and `HarnessTelemetry` samples (about 1 KB per sample). The question for each bug: which events and which state fields would show the cause in a tester's bundle?

What exists today: the features already log one line per decision with `core.log.info` (about 140 call sites, for example `INVASION spawn ...`, `RAID_BEHAVIOR start/end ...`, `SACK ...`, `VASSALS ...`). A telemetry sample has the date, the player values and the regions (population, food, approval), plus a `custom` object that mods fill with metrics.

## #337 raid tracker keeps dead raiders alive (and no leave line)

- Cause (from the fix): the 18 Brigands lost the fight with the village, the raid ended `destroyed`, and the tracker counted a raider as living until later than the game census did.
- Bundle today: `RAID_BEHAVIOR start id day squads raiders` and `RAID_BEHAVIOR end id state=destroyed` are in the log. A reader sees "destroyed after 13 days, no leave line". That explains the first symptom (no leave line).
- Missing for the second symptom (tracker 3 to 4 living, census 0): a state sample with the tracker count and the game census count for each active raid. Without both numbers nobody sees the difference.
- Needs:
  - events: raid start, raid end with state and day, first death of a raid unit (once), the raid composition;
  - sample field `raids[]` with `id`, `tracker_living`, `census_living`, `state`, once per game day (it is the existing `custom` object).

## #357 `remove_families` crashes the game

- Cause: the helper walked the family array while the deaths changed it. The game crashed (UE crash folder with a minidump).
- Bundle today: the marker plus a new crash folder says "crash". The mod log ends at the last line before the kill, which is flushed (note `crash-safe-log.md`). The helper writes no line of its own, so the last line is the one before the sack or the wipe, and the reader cannot see which call died.
- Needs:
  - an intent line before every call that can kill the game, flushed before the call: `CORE remove_families region=<name> count=<n> families=<n>`; this is the key rule, because the crash gives no later line;
  - the minidump and `CrashContext.runtime-xml` of the newest crash folder (the call stack is a native game fault; the mod cannot symbolize it, the owner can);
  - the save (ticked by default), so the village can be loaded and the sack repeated.

## #325 sack fire leaves no rubble

- Cause: villagers put out the fires when no enemy soldiers are in the village. The test set the fires with no raiders present.
- Bundle today: `SACK ...` lines say a sack ran, but not how many buildings burned, how many became rubble, and whether raiders were in the village. A daily sample is too slow: the fires burned out within 40 game seconds (one game day).
- Needs:
  - an event line with the inputs at the call: `SACK fire region=<name> buildings=<n> raiders_in_region=<n> raid_state=<s>`;
  - an event-driven result line at +40 game seconds: `SACK result burning=<n> rubble=<n> of <n>`; the two numbers (and the raider count) show the cause at once;
  - no extra periodic sample.

## Verdict

- A bundle with the existing decision lines finds the cause of #337 (first symptom) and narrows #357 to "a sack or wipe call", but it does not find the second symptom of #337 or the cause of #325.
- Two additions close the gaps: (1) intent lines before risky calls and result lines after timed effects (at +N game seconds), (2) a `custom` sample of tracker values next to game values, once per game day.
- A tester's bug that is a wrong decision (for example #325) is only readable if the line holds the inputs of the decision, not only the result. This is a rule for the log lines of the feature change (see `recommendation.md`).

## Not verified

- No bundle was built for a real past run: the runs are archived without a mod log in the repo.
- Whether the owner can read a minidump of the game (no game symbols; the call stack shows module offsets).
