# Command line facts for repak and UAssetGUI

Date read: 2026-10-10.
Sources: `https://github.com/trumank/repak` (README), `https://raw.githubusercontent.com/trumank/repak/master/repak_cli/src/main.rs` (clap definitions and output code),
`https://github.com/atenfyr/UAssetGUI` (README, command line section).
The first part was read from the source and README. The parts marked VERIFIED were run on the real game with repak 0.2.3 and UAssetGUI 1.1.0 (spike, 2026-10-10, `pak-spike-findings.md`). The pages were summarized by a fetch tool, so check the exact text against your installed version with `repak --help` and `repak <command> --help`.

## repak

Global option (before the command): `-a, --aes-key <KEY>`: 256 bit AES key as base64 or hex string, if the pak is encrypted. `--version` prints the crate version (clap `version`).

| Command | Arguments (positional unless noted) | Output |
|---|---|---|
| `info` | `<pak>` | stdout: lines `key: value` (mount point, version, encryption, compression, path hash seed), then `<n> file entries` |
| `list` | `<pak>`, `-s, --strip-prefix <p>` (default `../../../../../docs/`) | stdout: one entry path per line, forward slashes, prefix stripped. Not sorted |
| `hash-list` | same as `list` | stdout: `<sha256 hex> <path>` per line, sorted by path |
| `unpack` | `<pak>...`, `-o, --output <dir>`, `-s`, `-v`, `-q`, `-f, --force`, `-i, --include <glob>` (repeatable) | writes files below the output folder |
| `pack` | `<input dir>` `[<output>]`, `-m, --mount-point <p>` (default `../../../../../docs/`), `--version <V>` (default `V8B`), `--compression <C>`, `-p, --path-hash-seed <n>` (default 0), `-v`, `-q` | stdout: `Packed <n> files to <output>` unless `-q` |
| `get` | `<pak>` `<file>`, `-s, --strip-prefix <p>` | stdout: the raw bytes of the file, no added newline |

- `pack` output: the second positional is documented as "Output directory". VERIFIED: it is the output FILE (`...\out\name_P.pak`).
- Version names: `--version` accepts the names of `repak::Version` (values are listed by `repak pack --help`). The README table says versions 1 to 11 exist and 11 is supported for read and write. `V11` is our default. VERIFIED: the game paks are V11 (`Fnv64BugFix`), mount point `../../../../../docs/`, encrypted index. The game loads our unencrypted V11 pak.
- Compression names: Zlib, Gzip, Zstd (README). The README says that writing does not support compression or encryption yet. The harness packs without compression.
- VERIFIED: `pack` with `--aes-key` before the command still writes an UNENCRYPTED pak (`repak info`: `encrypted index: false`). The game accepts it.
- VERIFIED: `repak get` with `-s ../../../` and a path like `ManorLords/Content/.../DT_Items.uasset` works. `list` shows paths without the `../../../../../docs/` prefix.
- Exit codes are not set in the source. A Rust `main` that returns an error exits with code 1 (standard behavior, not read from the code).

Command templates used by `pakmod.py` (the tool path and `--aes-key` are added in front; `{...}` are placeholders):

```
list  : list -s {mount_point} {pak}
get   : get -s {mount_point} {pak} {file}
pack  : pack --mount-point {mount_point} --version {pak_version} {input} {output}
```

## UAssetGUI

```
UAssetGUI tojson <source> <destination> <engine version> [mappings name]
UAssetGUI fromjson <source> <destination> [mappings name]
```

- Engine version: VERIFIED for v1.1.0: use the enum name `VER_UE5_5`. The string `5.5` makes `tojson` exit with 0 and write NO file.
- Mappings: VERIFIED for v1.1.0: pass the NAME of a file in `%LOCALAPPDATA%\UAssetGUI\Mappings\<name>.usmap` (without extension). A path is silently ignored, and so is a name that does not exist: the tool still exits with 0 and writes a `RawExport` JSON (about 140 KB, no fields). With the mapping the DT_Items JSON is 6.3 MB with a `DataTableExport`. Setting `LOCALAPPDATA` for the process does not move the folder. `pakmod.py` has the config key `usmap_name` for this and checks the installed file.
- VERIFIED: the command line prints nothing, exits with 0 also on errors, and returns at once (under 1 s for `tojson` of DT_Items). `fromjson` writes the `.uexp` next to the `.uasset`. `pakmod.py` checks that the destination exists and is not empty, and that `tojson` did not write a `RawExport`.

```
tojson  : tojson {source} {destination} {engine_version} {usmap}   (usmap = the mapping NAME when config has usmap_name)
fromjson: fromjson {source} {destination} {usmap}
```

## Overriding a template

The local config can hold `"templates": {"tojson": ["tojson", "{source}", "{destination}", "{engine_version}", "{usmap}"]}`.
A key replaces the default for that command. Known placeholders: `{pak}`, `{file}`, `{input}`, `{output}`, `{source}`, `{destination}`, `{mount_point}`, `{pak_version}`, `{engine_version}`, `{usmap}`.
An unknown placeholder is an error. The AES key is never a placeholder: `pakmod.py` adds `--aes-key <key>` in front of the `repak` command itself.
Note: the key is then visible in the process list while repak runs. This is how repak takes the key.
