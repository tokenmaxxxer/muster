# Survey — issue #336

## Scale

~9 spec-shaped documents describe the engine, none cross-referenced:
`protocol.md`, `protocol.ko.md`, `README.md`, `README.ko.md` (top level),
`docs/specs/approvers.md`, `docs/specs/flows-schema.md`,
`docs/handbooks/on-the-record.md`, `docs/handbooks/operations.md`,
`docs/handbooks/setup.md`. Plus `on-the-record/commands/run.md`
(plugin-side restatement of engine behavior) and `docs/decisions/*.md`.
No document lists or hashes the others; nothing ties them together.

## Confirmed contradiction (ledger location)

- `docs/handbooks/on-the-record.md:27,51` — architecture diagram shows
  `ledger/` as a top-level repo directory ("성적표" / "the scorecard"),
  peer of `gates/`, `roles/`, `spawn.py`.
- `docs/handbooks/operations.md:159,405` — says spawn appends one line
  per session to `runs/ledger.jsonl`.
- `docs/specs/flows-schema.md:243-252` — confirms `runs/ledger.jsonl`
  as the actual source, explicitly local-orchestrator data.
- `on-the-record/commands/run.md:340` — also cites `runs/ledger.jsonl`.
- `protocol.md` (the top-level contract) never mentions the ledger at
  all — the document an operator would check first is silent.

3 of 4 documents that discuss it agree on `runs/ledger.jsonl`;
`on-the-record.md`'s diagram contradicts them by depicting a top-level
`ledger/` directory as the storage location. (`ledger/collect.py` does
exist at the repo root, but it is an aggregator that reads
`runs/ledger.jsonl` — it is not itself the storage the diagram implies.)
This is exactly the fragmentation the operator reported: reconciling
this required reading four documents and the actual script; nothing
forces that reconciliation to happen once and stay found.

## Existing tooling

None. Searched `gates/*.py`, `tests/`, `conftest.py`, `test_*.py` for
"doc lint" / "spec check" / "consistency" — no hits. No script computes
or checks anything about document content vs. other documents.

## Related issues

- #310 (already binding on this proposal): acceptance must name an
  executable artifact that fails on regression.
- #328: unrelated problems must not be merged into one issue — this
  proposal stays inside "who owns the reconciled reading," not general
  doc quality or #321's requirement-dilution problem (separate root
  cause: erosion of the *operator's* stated requirements over session
  turns, not fragmentation across *documents*).
- No prior `docs/decisions/` or `docs/proposals/` work references #304
  or a requirement-dilution issue by number — issue #336's "related"
  pointers are context, not a found artifact to build on.

## Skip conditions

Neither scout-directive skip condition applies (not a pure bugfix; the
spec leaves open how reconciliation is enforced) — scouting was run:
see `docs/issue-336/reports/implementation/scout-brief.md`.
