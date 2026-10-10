# Command line facts for repak and UAssetGUI

Date read: 2026-10-10.
Sources: `https://github.com/trumank/repak` (README), `https://raw.githubusercontent.com/trumank/repak/master/repak_cli/src/main.rs` (clap definitions and output code),
`https://github.com/atenfyr/UAssetGUI` (README, command line section).
These facts come from reading the source and README only. No tool was downloaded or run. The pages were summarized by a fetch tool, so check the exact text against your installed version with `repak --help` and `repak <command> --help`.

## repak

Global option (before the command): `-a, --aes-key <KEY>`: 256 bit AES key as base64 or hex string, if the pak is encrypted. `--version` prints the crate version (clap `version`).

| Command | Arguments (positional unless noted) | Output |
|---|---|---|
| `info` | `<pak>` | stdout: lines `key: value` (mount point, version, encryption, compression, path hash seed), then `<n> file entries` |
| `list` | `<pak>`, `-s, --strip-prefix <p>` (default `../../../`) | stdout: one entry path per line, forward slashes, prefix stripped. Not sorted |
| `hash-list` | same as `list` | stdout: `<sha256 hex> <path>` per line, sorted by path |
| `unpack` | `<pak>...`, `-o, --output <dir>`, `-s`, `-v`, `-q`, `-f, --force`, `-i, --include <glob>` (repeatable) | writes files below the output folder |
| `pack` | `<input dir>` `[<output>]`, `-m, --mount-point <p>` (default `../../../`), `--version <V>` (default `V8B`), `--compression <C>`, `-p, --path-hash-seed <n>` (default 0), `-v`, `-q` | stdout: `Packed <n> files to <output>` unless `-q` |
| `get` | `<pak>` `<file>`, `-s, --strip-prefix <p>` | stdout: the raw bytes of the file, no added newline |

- `pack` output: the second positional is documented as "Output directory. Defaults to next to input dir". It is the output file in practice (UNCERTAIN). `build` checks that the file exists.
- Version names: `--version` accepts the names of `repak::Version` (values are listed by `repak pack --help`). The README table says versions 1 to 11 exist and 11 is supported for read and write. `V11` is our default (UNCERTAIN: the game's real pak version is not known yet; `repak info` on a game pak tells it).
- Compression names: Zlib, Gzip, Zstd (README). The README says that writing does not support compression or encryption yet. The harness packs without compression.
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

- Engine version: a `major.minor` string such as `5.5` (v1.1.1 and later), or an `EngineVersion` enum name such as `VER_UE5_5`, or an integer.
- Mappings: optional. Either the path of a mappings file on disk with its extension (v1.1.1 and later), or the name of a file in the UAssetGUI Mappings config folder without extension.
- The README does not describe exit codes, output text, or what happens to the `.uexp` file. UNCERTAIN: whether `fromjson` writes the `.uexp` next to the `.uasset`, and whether a GUI build returns to the shell at once. `pakmod.py` only checks that the destination file exists and is not empty, with a 120 s limit.

```
tojson  : tojson {source} {destination} {engine_version} {usmap}
fromjson: fromjson {source} {destination} {usmap}
```

## Overriding a template

The local config can hold `"templates": {"tojson": ["tojson", "{source}", "{destination}", "{engine_version}", "{usmap}"]}`.
A key replaces the default for that command. Known placeholders: `{pak}`, `{file}`, `{input}`, `{output}`, `{source}`, `{destination}`, `{mount_point}`, `{pak_version}`, `{engine_version}`, `{usmap}`.
An unknown placeholder is an error. The AES key is never a placeholder: `pakmod.py` adds `--aes-key <key>` in front of the `repak` command itself.
Note: the key is then visible in the process list while repak runs. This is how repak takes the key.
