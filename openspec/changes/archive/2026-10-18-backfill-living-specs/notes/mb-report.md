# Report MB (Invasion Mod, part B)

Validation: `openspec validate backfill-living-specs --strict` shows no error or warning for my five files.

| Capability | Requirements | With a real check | Scenarios without a check |
|---|---|---|---|
| mod/unit_balance | 8 | 8 | 0 |
| mod/sack_and_terms | 10 | 10 | 0 |
| mod/vassals | 10 | 10 | 0 |
| mod/tribute | 8 | 8 | 0 |
| mod/refugees | 7 | 7 | 0 |

"Real check" means every scenario names a scenario file or a Python test. I did not run them.

## Planned iterations not built
None. All iterations of M05 to M09 are marked done in the legacy files: M05 01-04, M06 01-04, M07 01-04, M08 01-02, M09 01-02.

## Legacy claims dropped (reason)
- M05 shield and pavise counter against crossbows (iteration 04): not delivered, no stat lever. Archers against raiders is native (no code).
- M05 pak route for unit rows (open question 4) and the tunable "damage ratio 2 to 3 times": a goal, not code. Only the A/B result is a scenario.
- M05 militia factors for the tech tree (`set_militia`, M12): in the code, but not in M05. I left it out; the tech_tree spec can cover it.
- M06 loss of the great raid's final battle: TBD, no code.
- M06 terms after a sack, effect of vassalage on later raids, moving best units and removing home families to the capital: not built.
- M06 `fire` sack method, and the fatal sack ending the game in the real game: not verified. The spec says only "removes all families".
- M07 vassal paying tribute to the invader: only the flag exists.
- M07 "second vassal in the real game" (H5): fake game only.
- M07 `take_by_lord` loss: crashes, so it is not a requirement. The `forget` default is.
- M08 tribute for influence (M11): not built.
- M09 per-refugee approval penalty and food: native game effects, stated as "left to the game".
- Engine facts and run ids were left out (D2).

## Feedback files written
None. No `feedback.md` exists for M05 to M09.

## Doubts
- Tribute requirement "A long siege takes a vassal" lives in `features/tribute/init.lua` but belongs to M02.07. Check it does not duplicate `mod/invasion`. Check: fake test and `invasion/vassal_targets.py`.
- unit_balance requirement "Hussite raids use unit roles" overlaps `mod/invasion` (the plan code is in `features/invasion`). MA may state it too.
- I did not open every scenario file to confirm each THEN step. Some scenario-to-step pairings come from the legacy Result sections: `vassals/claim_without_victory.py` for the state command, `sack_and_terms/sack.py` for the second sack with fatal off and for the state command, `refugees/refugee_wave.py` for the second-wave refusal.
- Fake-test checks name the whole file, not one test. Some claims (for example "a failed rebellion", "tribute day") map to a named test I read by name only.
- The unit_balance poll default is 4000 ms in code; legacy text said 2000 ms. The spec uses the code value.
