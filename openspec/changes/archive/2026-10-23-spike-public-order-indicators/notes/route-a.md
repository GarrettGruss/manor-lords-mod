# Route A: the factor list (tasks 2.1 to 2.4)

Runs: `ord-h-193058` (fixture `base`, region Nusslohe "Riesenbuckel", paused unless noted). Pictures: `evidence/o1`, `o2`, `o7`.

## Verdict

**Partly works.** The tooltip reads `Region.summedPublicOrderFactors` (and its `past` entries). An appended entry shows in the tooltip at once, with the **native label of its enum value**. The game rebuilds the list each game day, so the mod must append again after every day change. `publicOrderMemory` is not read by the tooltip.

## 2.1 Data source

- Native function `Region:getSummedFactorsRecentPast(factors, ReturnValue)`: the tooltip calls it with the region's list and gets the sums and the two lists (recent, past). The list is `summedPublicOrderFactors`: entries `ApprovalMemory` with `Type` (enum), `day`, `expirationDay`, `count`, `past`, `effectByPopulation`. Read directly: `arr[i].Type`, no `:get()`.
- Start (fixture `base`, day 205): `[1] Type 17 day 205 exp 210 count 1 past false eff -10.0` and `[2] Type 19 ... eff +10.0`. `publicOrderMemory` empty. The tooltip shows "Unemployment -10%" and "Administrative Buildings +10%", header "Recent Factors +0%" (`o1-tooltip-baseline.jpg`).

## 2.2 Append to `summedPublicOrderFactors`

- `arr[n + 1] = { Type = 23, day = day, expirationDay = day + 5, count = 1, past = false, effectByPopulation = -40.0 }` works (no error, no crash). Read back: 3 entries.
- Tooltip after moving the cursor away and back: a third row **"Unburied Bodies -40%"** and the header "Recent Factors -40%" (the sum -10 +10 -40) (`o2-route-a-append.jpg`). The label comes from the enum value (23 `unburied`). **There is no way to give it another text with route A.** The 34 labels are the only ones.
- Does the game clear it? Yes. At the next day change (`daysTotal` 205 to 206) the list was rebuilt with 2 entries; the appended entry was gone. A poll every 3 s (about 1 to 2 game days at speed 3) shows `n=2` after each day change until the entry is appended again.
- With an "append if missing" step each poll: `added=true` after each day change, `n=3`, and the entry shows on each later day (day 214 to 221 checked). 7 of 7 polls had the entry.
- Effect on `publicOrder`: none. It stayed 42 (with the known transient 40 and 100 samples) while the entry was present. The entry changes the tooltip only. This fits the owner decision of #403 (the mod writes `publicOrder` itself).

## 2.3 `past` entries and `publicOrderMemory` ("Lingering Memories")

- An entry with `past = true` in `summedPublicOrderFactors` (Type 5, -20) gives **"Lingering Memories -20%"** and a "TAB" hint (details open with TAB). I could not open the details: a real TAB key press (`osinput.press_key`) changed nothing visible, so the label of the past row is not seen (`o7-route-a-past-and-memory.jpg`).
- An entry appended to `publicOrderMemory` (Type 16, -10): the header stayed -20%. So this list is not read by the tooltip (as #403 found for `publicOrder`).

## 2.4 Verdict

Partly works: visible and kept (when appended again after each day), but only with the native labels. Good enough for a few existing meanings, for example `unburied` (23), `homelessness` (5), `drinking` (16), `taxation` (24), `no_administration` (20), `missingEntertainment` (22). Not good for "Bandit fear" or "Raid". Route B gives the custom text.

## Not verified

The details view of the past rows (TAB); append in the middle of a day change (race with the rebuild); several regions; save and load.
