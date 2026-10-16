# Spec 24: Mod state across saves (spike)

Status: spike done (2026-10-15). Option A works: names in `Tags` arrays of the player pawn and the player region survive a save and a load. Open: one manual menu-save check (see Open questions). Issue: #128. Branch: `feat/24-mod-save-state`.
Needed by: the Invasion Mod (M00 feasibility decision 9). Every feature that keeps values needs it.

## Goal
Find a safe way for a Lua mod to keep its own state with each save of the player, and to get it back after a load.
The state is small: the great raid countdown, vassal loyalty, liege influence, the leadership path, tech nodes, deposit stock, the raid schedule. A few kB at most.

## Constraints
- The user approved that the harness makes saves (2026-10-15). The harness saves only through one guarded save action (plan step 2, CLAUDE.md Safety). Scenarios and ad hoc probes never call a save function directly.
- The finished MOD never calls a save function. In play the PLAYER saves; the mod only reacts (hooks).
- The state must belong to the right save: two saves of the same game, or two games, must not mix their state.
- A load of an old save (from before the mod) must work: the mod starts with default state.
- Write files atomically (`.tmp`, then rename).

## Options to test
A. **Write into the save.** Store the values in game fields that the game saves and loads. Candidates: unused or free number fields on objects that are saved (region, pawn, buildings, data table rows changed at run time). Check what survives a load.
B. **Side file next to the save.** A mod file (for example `InvasionMod/<slot>.json`) written when the player saves, read when the player loads. Needs: a hook that fires on a player save and on a load, the slot name or a save id, and a key that tells two saves apart (slot, game date, a mod-made id stored in the save by option A).
C. **Hybrid.** Option A stores only a small id; option B stores the data under that id.

## Questions
- Q1: Which reflected functions fire when the PLAYER saves and loads (menu save, quick save, autosave)? Can Lua hook them without calling them? (A post-hook only observes. The mod must work from hooks, because players save through the menu.)
- Q2: Can a hook read the slot name or file path of the save?
- Q3: Which fields does the game save that Lua can write: a region field, a building field, a data table value changed by Lua, an unused property? (Spec 09 notes: a Lua write to a data table is not verified to persist over a load.)
- Q4: Where are save files and how are they named? Is there a game date or a unique id in them that Lua can read?
- Q5: What happens on a crash before a save, and on a load of an older save of the same game?

## Plan
1. Static: list save and load related functions and classes in the jmap (`IoHandler`, `MLGameInstance`, `PawnCPP`, save game objects). Note which are safe to hook. Write `implementation-notes/save-hooks.md`.
2. Guarded harness save action `save_game` (replaces the `save_state` stub that raises today, spec 07):
   - back up the user's save folder first (copy outside the game folder, keep the newest backups);
   - snapshot the file list and hashes of the save folder;
   - call the save function that the static step picks (`PawnCPP:requestSaveFile`) with the next free slot `saveGame_<N>` (above the highest existing one, as fixtures do), never an existing slot and never `Request Autosave`. The Python guard checks that no file of the slot exists; the Lua command checks it again with `DoesSaveGameExist` and accepts only `saveGame_<number>`;
   - after the save: exactly one new file (plus the game's thumbnail or meta file, if any) may appear; any change to an existing file is a failure, and the action restores that file from the backup and fails loudly;
   - the run guard (save hashes before and after) expects only the files that `save_game` reported;
   - at run end, delete the harness save files unless the scenario keeps them as a fixture (spec 06).
   - Fake tests for the guard first. The first real call is in a run with a fresh backup and the user informed.
3. Option A test: write a marker value into 2 or 3 candidate fields; `save_game`; load that slot in a new run (`load_save.py`); read the fields.
4. Option B test: hook the save and the load; `save_game` and a load trigger the hooks; write and read a side file keyed by slot and game date.
5. Choose an option. Write a small Lua module design (`ModState`: register, get, set, load, save hooks) and the rules for features. No feature code in this spec.

## Safety
- Back up the user's save folder before any test (CLAUDE.md).
- Save only through `save_game` (plan step 2). Never call a save function from a probe, a scenario or `eval_lua`.
- Every harness save goes into the next free `saveGame_<N>` slot. Never overwrite an existing save. If the game picks the slot by itself (as with `saveGame_9` before), stop and report before the next save.
- Why not a `harness_` prefix: the load list shows only `autosave` and `saveGame_<N>` (see `implementation-notes/save-hooks.md`), so a `harness_` slot could not be loaded for plan step 3. The next free number also needs no new slot logic. (Decision 2026-10-15.)

## Acceptance criteria
- A0 (met, `implementation-notes/first-save.md`): `save_game` exists with fake tests for the guard (new slot only, one new file, restore on change), and one real save in a run left the user's other saves unchanged (hashes).
- A1 (met for the harness save and for load, `implementation-notes/persistence-tests.md`): `implementation-notes/save-hooks.md` lists the save and load hooks with evidence (a run id where each one fired, or a note that it did not).
- A2 (met, option A with Tags): At least one option keeps a test value across a harness save and a load, shown in a run.
- A3 (met, slots 62 and 63): Two different saves keep two different values (no mixing).
- A4 (met, fixture `base`): A save made without the mod loads with default mod state and no error.
- A5 (met, section Recommendation below; M00 links here): A recommendation and the `ModState` module design are written into this spec, and M00 links to it.

## Results (2026-10-15)
Evidence and run ids: `implementation-notes/first-save.md` and `implementation-notes/persistence-tests.md`.
- The first real guarded save was clean (A0).
- Option A works with Tags: `pawn.Tags` and `region.Tags` (TArray of FName) keep a marker over save and load. Two saves keep two values (A3). A save without a marker gives no marker (A4).
- Not usable: `region.regionName` (made-up names crash the load), `region.retinueName`, `pawn.lastQuestDay`, `pawn.numTimesInDebt` (not saved). `pawn.lordsName` is saved but the player sees it.
- Option B hooks: `PawnCPP:requestSaveFile` fires on a harness save with the slot name. On load, `MLGameInstance.savefileToLoad` holds the slot name, and `ReceiveBeginPlay` of the pawn and `OnSaveLoaded_Event` of the HUD fire. A menu save was not tested.
- A bridge `set` of a `Tags` array crashes the game. A Lua `FName` write works.

## Recommendation (A5)
Use option A: keep the mod state in the Tags of the player pawn. No hook, no side file, no slot name. The state follows the save by itself, for every kind of save (the game copies the live Tags when it saves) and for copies, renames and cloud restores of save files.
- Why not B: it needs a hook on the player save path (not proven for the menu), and the slot name is not a stable key.
- Option C is only needed if the state grows past what Tags can hold. Then a Tags entry holds an id and a side file holds the data. Do not build it before it is needed.
- Use the pawn for global state. Use the region Tags for state that belongs to one region (for example the deposit stock of a region). Both objects live for the whole game.

### Module design: `ModState` (shared module `mod/shared/ModState/ModState.lua`, not built yet)
Format of one entry: a Name `<mod>:<key>=<value>`. Example: `invasion:raid_days=412`. The prefix `<mod>:` keeps the entries of one mod apart from game tags and from other mods.
- `ModState.open(mod, owner)`: owner is `"pawn"` (default) or a region object. Reads the Tags once, parses the entries of `mod`, and returns a state table. A missing entry gives the default. A missing marker gives all defaults (A4).
- `state:register(key, default, kind)`: kind is `integer`, `number`, `boolean` or `string` (no `=` or space in a string; use `[A-Za-z0-9_.-]`). Registering fixes the key set, so a typo fails loudly.
- `state:get(key)` and `state:set(key, value)`: `set` changes the table only and marks it dirty.
- `state:flush()`: writes the dirty keys into the live Tags. For each key it removes the old Name `<mod>:<key>=...` and appends the new one. It runs on the game thread, in `pcall`, and logs a stack trace on error. Call it after each change of value, or on a timer of a few game seconds. The live Tags are what the game saves, so a flush before the player saves is enough. A flush on each change needs no save hook.
- Versioning: the entry `<mod>:v=<n>`. `open` returns the stored version, so a mod can migrate old state.
- Limits: a Name has at most 1023 characters. Keep one value in one entry. A few kB of state means a few dozen entries. A limit test (many entries, long entries, save and load time) is still open.
- Rules for features: no feature writes Tags by itself; no feature uses the bridge to write Tags; no feature uses `lordsName`, `regionName` or any game tag; a mod never removes a tag that is not its own; a mod calls no save function.
- After a load: `open` runs again on `ReceiveBeginPlay` of the pawn (it fires once per load). This keeps the table equal to the loaded Tags.
- Test (harness): a command `ModState.dump` returns the table. A scenario sets values, calls `save_game(keep=True)`, loads the slot in a new run and compares (as in `probe-save-tags` and `probe-save-read`).

## Open questions
- Does `requestSaveFile` let the caller choose the slot file, or does the game pick `saveGame_N`? Static answer: the caller chooses (`save-hooks.md`). The first real save must confirm it. `save_game` raises if any other file changes.
- Which extra files does the game write for a slot (`_descr.sav`, `.png`, `_coat_<n>.png`)? `save_game` accepts exactly these names for the new slot and fails on any other new file.
- Decided (user, 2026-10-15): the harness may make saves, under the rules above.
- Answered: the game keeps the slot name given by the caller; the first real save confirmed it (`first-save.md`).
- Open: does a PLAYER save (menu, quick save, autosave) keep the Tags too? Expected yes, because the game builds every save from the live state. One manual check by the user: add a tag with the probe command, save from the menu, load it, read the tag.
- Open: size limits (many or long Names), and the Tags of AI lords and buildings.
- Open: the unrelated stale slot `saveGame_48` in the real folder (8 files, not in any ledger, present before this work). Ask the user.
