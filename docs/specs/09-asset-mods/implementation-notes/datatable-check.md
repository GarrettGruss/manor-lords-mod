# DataTable check (spec 09, the first check)

Date: 2026-10-10. Question: can Lua read and write a DataTable row at runtime?
Table: `RTSMultiEngineCPP.itemStats` = `/Game/NotStronghold/Data/DT_Items.DT_Items`, row struct `/Script/ManorLords.Item`.
Real game, paused, runs `keepopen-3` (bridge reads) and `keepopen-4` (Lua mod commands).

## Answer

**Yes, for number fields. Pak editing is still not needed for numbers.**
The UE4SS build of the game (v3.0.1 Beta, git 5e627997) has the Lua class `UDataTable`
(`GetRowNames()`, `FindRow(name)`, `GetRowStruct()`, `#table`, `AddRow`, `RemoveRow`, `GetRowMap`; see `ue4ss/Docs/lua-api/classes/udatatable.md`).
`FindRow` returns a struct with reference access: `row.Value = x` changes the table memory.

## Reads through the bridge

| Read | Result |
|---|---|
| `get RTSMultiEngineCPP.itemStats` | safe: `{"__object": "DataTable /Game/NotStronghold/Data/DT_Items.DT_Items"}` |
| `funcs` of the table | safe, but useless: only `ExecuteUbergraph` |
| `props` or `get` of `RowStruct` on the table | **crashes the game** (access violation at 0x10, in-flight call `props DataTable.RowStruct`). The bridge gets the `UScriptStruct` object of the type `Item` and reads its fields as if it were a value (`encodeStruct`, a `StrProperty` field). The table is not the problem |
| `getItem(1)` (catalog) | **crashes**: the returned `Item` has a `SoftClassProperty` (`droppable`). UE4SS cannot convert it (see `03-run-launcher/implementation-notes/real-crash-report.md`) |
| `RowMap` (a `TMap`) | not tried. Do not read it through the bridge |

So the bridge cannot read rows. A Lua mod must do it, and read single fields by name.

## Reads and writes in a Lua mod (shared module `HarnessDataTable`, commands of `HarnessActions` version 3)

The module allows one table (`itemStats`) and the number fields `Weight`, `Value`, `spoilageRate` (floats of `Item`).
It never reads `Name`, `Icon` or `droppable`.

| Step | Result |
|---|---|
| `datatable_info` | `row_count` 213, `row_struct` "ScriptStruct /Script/ManorLords.Item", first names "-1", "0", "1" ... "10". Row names are the item ids as text. Ids are sparse (60 and 100 do not exist: "no row named") |
| `datatable_read` `Value` of rows 16, 17, 1, 5, 10, 30 | 0, 0.5, 1.5, 2, 3.5, 1 (item 16 is Timber, 17 is Planks) |
| `datatable_read` `Weight` of the same rows | 0 in all of them (a combat item field) |
| `datatable_write` row 17 `Value` 0.5 -> 0.75 | `{before: 0.5, after: 0.75}`. A new `datatable_read` gave 0.75 |
| `datatable_write` row 17 `Value` 0.75 -> 0.5 (restore) | read back 0.5 |
| A field that is not listed (`Name`) | refused before any read or write |
| Crashes in the Lua commands | none (about 30 commands) |

User save folder: 204 files hashed before the first crash test and after the last run: identical.

## Decision for spec 09

Number data in `DT_Items` can be read and changed at runtime with a Lua mod, so a pak is not needed for such changes. Spec 09 stays deferred.
This is a first check only. These points are **not verified**:

- That the game logic uses the changed value (for example a changed trade `Value` in a market, or `Weight` in a fight). Only the table memory was read back.
- Whether a change survives a new load of a save or a level change.
- Strings, names, arrays, `Icon` and `droppable` (soft references), `AddRow`, `RemoveRow` and `GetRowMap`. Soft fields are known to crash UE4SS.
- Other tables (buildings, recipes). Their structs may have soft fields too. Search the jmap for `SoftObjectProperty` and `SoftClassProperty` before any read.
- A user mod must use the same pattern (`FindRow`, then one field by name) and must not return whole rows to the bridge.
