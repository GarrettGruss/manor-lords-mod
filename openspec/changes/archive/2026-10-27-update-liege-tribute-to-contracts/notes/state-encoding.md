# Encoding of the saved contract text (task 3.1)

ModState string values allow only `A-Z a-z 0-9 _ . -` (`mod/shared/ModState/ModState.lua`, `STRING_PATTERN`). The spec text "key=value pairs separated by semicolons" cannot be saved.

Decision: `contracts_progress` and `contracts_baseline` hold entries `o<index>-<value>`, separated by dots. The index is the 0-based position of the objective in the contract. Example: `o0-12.o1-40`. No entries is the empty text.
`contracts_offer` holds contract ids separated by dots (ids may hold letters, digits, `_` and `-`, as the loader checks).
