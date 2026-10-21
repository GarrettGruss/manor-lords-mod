# Native bandit messages (task 1.1)

Question: which messages does the game show when the mod sends the native settle letter?

Method: hidden test scenario `probe-bandit-messages` (fixture `base`, slot 0). It spawns one raid (+18 bandit units), sets the tag `attacking`,
sends `raider_suggestSettle+30` (the same call as `send_settle_letter` of the mod), runs the game in 6 s steps, and reads InBox, pop-ups,
widget counts and hook events. Screenshots are in `evidence/`. No save call, no raw eval.

Messages seen, in order:

| When | What the player sees | Data |
|---|---|---|
| Letter sent | Silver goes down ("Treasury change registered: -30"). Nothing else for about 6 game seconds. | `outbox` 1, `bandit_inbox` 1 |
| About 6 game seconds later | Banner "A New Message" (a number 2 appears on it). It stays until the player acts. | One new `questMessageElaborate_C` widget (1 to 2). InBox holds one letter from the bandit lord: `raider_refuseSettle`, `raider_acceptSettle`, `read` true, `wasOpened` false. |
| Same time | The bandit units lose their squad and are removed. | bandit units 36 to 0 |

- A banner "A New Message" without a number is on screen at the start of every new game (1 `questMessageElaborate_C` widget before any raid). It is not a bandit message.
  The raid spawn alone adds no `questMessageElaborate_C` widget (runs `s343-b1`, `s343-e1`: 1 before the raid, 1 after the raid, 1 right after the letter).
- No pop-up opened (`popup_state` was empty in every run). `genericAchievement_EventMessage_C` widgets (the `playEventMessage` banner) come and go during every run, also without letters.
- No greeting letter from the bandit lord was seen.

Runs: `s343-d2` (function list; the game crashed, see side-effects.md), `s343-h1` (hooks), `s343-c1` (control), `s343-b1` (best screenshots).

Not verified: a natural raid (not spawned by the harness); a settle price that the game refuses (the game takes any price).
