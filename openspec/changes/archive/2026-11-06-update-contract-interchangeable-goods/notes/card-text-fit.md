# Card text fit

- First real run with the label "berries or mushrooms" (run `20261107-001203-d7f9`): the text "Deliver 40 BERRIES OR MUSHROOMS" is about 31 characters and runs over the card edge into the next card (checked in the screenshot).
- The longest text that fits today is "Cost: TRIBUTE FOR 3 MONTHS" (it touches the edge). The room after "Deliver 40 " is about 14 characters.
- Decision: the label of the berries group is "berries/fungi" (13 characters). "hides or pelts" fits. The owner can change the label in `contracts.json` (field `label`), but a longer one must be checked in a screenshot. Open owner question: a better short word for "berries or mushrooms".
- Pak note: `--pak InvasionMod` installs `modtools/work/out/InvasionMod_P.pak`, which is stale (27 Oct). With it the menu says "class not found" and the old scenario `liege-contracts-window` fails the same way (runs `20261107-000437-ed0f`, `20261107-000858-5c8a` are harness errors for that reason). The passing runs used a copy of `mod/InvasionMod/paks/InvasionMod_P.pak` in a private work folder given by `--pak-config`. No file outside the repo was changed.
- Config note: `liege_contracts.weight[279]` has no effect now; berries use `weight[171]`.
