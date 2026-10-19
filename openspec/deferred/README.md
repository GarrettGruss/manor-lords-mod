# Deferred changes

This folder holds OpenSpec changes that the project owner postponed. The `openspec` CLI does not see them, so `openspec list` stays short.

- A deferred change keeps its folder unchanged. Its issue stays open with the label `status: deferred`.
- To resume a change, move its folder back to `openspec/changes/` with `git mv`, and set the issue to `status: in progress`.

| Change | Issue | Deferred on | Reason |
|---|---|---|---|
| `add-plundered-start` | #274 | 2026-10-19 | Postponed by the owner. |
| `add-trailer-pipeline` | #133 | 2026-10-19 | Deferred by the owner. |
