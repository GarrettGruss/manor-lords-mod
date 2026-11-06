# Spike: bodies of removed families (2026-11-06, slot 1, fixture `playtest-noai`)

Prior art: `spike-rebel-without-corpses` (hide and `Region.corpses:Empty()` are safe, `K2_DestroyActor` crashes).

| Run | Variant | Result |
|---|---|---|
| `20261106-140856-36ad` | control: `just_die` only | 6 people died. `Region.corpses` 6 -> 12 within one game day and stays 12. The 6 new dead units are not hidden (`dead_hidden` 18 -> 18). The checks B2 to B5 fail, as expected. |
| `20261106-140343-6d10` | fix: `just_die`, `SetActorHiddenInGame(true)`, remove the new bodies from `Region.corpses` | 6 people died. `dead_hidden` 18 -> 24 (all 6 new bodies hidden). `Region.corpses` stays 6 at once, after 4 s and after 3 game days. No crash. |

## Corpse counter
The counter is `Region.corpses` (a TArray of the dead units). A death adds the unit at once or within one game day. Hiding alone does not change it (prior spike: bodies still count and expire like others).
The fix rebuilds the list without the new bodies: read all entries, `Empty()`, write back the old ones by index (`list[i] = body`). The 6 old bodies of the fixture stayed in the list and stayed visible.

## Native corpse removal
Not needed. The prior spike found no native emigrate, evict or corpse-removal function, and `K2_DestroyActor` on an `SMUnit` crashes the game. Hide plus a list rebuild works.

## Notification
No dead-bodies notification or counter showed in the pictures after the removal (`evidence/`). The game was paused by the harness in the pictures. The game's own notification rule was not found, so "no notification" is shown only for the screen at those moments. Not verified over a long unpaused time.
