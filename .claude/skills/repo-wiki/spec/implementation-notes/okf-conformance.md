# OKF conformance review

Source: a clone of `GoogleCloudPlatform/open-knowledge-format` (commit `ad30107`) in `../open-knowledge-format`, read on 2026-10-18. `SPEC.md` (OKF v0.2) is copied verbatim into `.claude/skills/repo-wiki/references/okf-spec-v0.2.md`, with the Apache 2.0 license next to it (`okf-LICENSE.md`).

## Gaps found in the first wiki format
| OKF rule | First format | Change |
|---|---|---|
| 5.1: `sources` is a list of mappings; `resource` is required in an entry | A list of path strings | `- resource: repo://<path>`. `wiki.py` reads the `repo://` entries for `stale` |
| 5.2: `generated: { by, at }`, actor convention (7), ISO 8601 with offset | Absent | Required by this wiki. `check` validates the actor and the time |
| 4.1, 11: front matter is YAML; consumers must not reject unknown keys | A YAML subset parser that rejected other syntax | PyYAML (`uv add pyyaml`). Only invalid YAML fails |
| 3.1: `index.md` and `log.md` are reserved | `log.md` would be read as a page | Both reserved. `check` validates `log.md` (9: `## YYYY-MM-DD`, newest first) |
| 8: index entries `* [Title](link) - description`; no front matter except root `okf_version` | Folder entries had no description; an HTML comment led the file | Folder entries list the page titles; comment removed |
| 4.1: `description` is a single sentence | Two pages had two or three sentences | Rewritten as one sentence |
| 5.2, 5.4, 5.5: `verified`, `status`, `stale_after` | Not checked | Checked when present. A bare `verified` mapping counts as a list |

## Kept on purpose
- **Relative links.** OKF recommends `/`-links from the bundle root (6.1) but allows relative ones. GitHub reads `/` as the repo root, so `/architecture/x.md` would break there. `check` refuses `/`-links.
- **`repo://` resources.** OKF path fields take a URL, a `/` bundle path or a relative path (6.2). Repo files are outside the bundle, so a bundle path cannot name them. `repo://<path>` is a URI, and OpenWiki uses the same form. A `sources[].resource` may also be a descriptor that a consumer cannot follow (5.1), so this is conformant in either reading.
- **Stricter producer rules.** This wiki requires `title`, `description`, `tags`, `generated` and `sources`, where OKF requires only `type`. Stricter is allowed for a producer.
- **No `verified` on the init pages.** The review checked two to five facts per page. That is a spot check, not a check of every claim against the sources, so the pages stay `unverified`. The skill says when to set `verified`.

## Independent check
The reference parser `src/reference_agent/bundle/document.py` of the OKF repo (147 lines, standard library and PyYAML only, reviewed before use) was loaded by file path and run over `docs/wiki/`. With the three conformance rules of section 11 (parseable front matter, non-empty `type`, no index front matter except root `okf_version`): no problems. Trust tiers: 24 `unverified`. The package itself was not installed; it needs Google ADK and BigQuery.
