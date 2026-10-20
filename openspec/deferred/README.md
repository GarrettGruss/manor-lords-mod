# Deferred changes

This folder holds OpenSpec changes that the project owner postponed. The `openspec` CLI does not see them, so `openspec list` stays short.

- A deferred change keeps its folder unchanged. Its issue stays open with the label `status: deferred`.
- To resume a change, move its folder back to `openspec/changes/` with `git mv`, and set the issue to `status: in progress`.

| Change | Issue | Deferred on | Reason |
|---|---|---|---|
| `add-plundered-start` | #274 | 2026-10-19 | Postponed by the owner. |
| `add-trailer-pipeline` | #133 | 2026-10-19 | Deferred by the owner. |
| `spike-wagenburg-manor-reskin` | #233 | 2026-10-20 | Deferred by the owner. Goal: the baron AI claims a region and builds a walled Wagenburg fort with a garrison. Includes the owner answers of PR #306. |
| `spike-wagenburg-bandit-camp` | #229 | 2026-10-20 | Deferred with #233; it is the fallback of #233. |
