# Survey — issue-309

## Write set (expected)
- `on-the-record/commands/run.md` — REPLY STRUCTURE section, lines 80-116

## Current state

`run.md`'s step 5 (lines 65-116) already specifies per-item flow/stage/next
anchoring (이슈-54) and link obligations (이슈-236). It has no layer above
that: when a turn spans multiple repos, the format in lines 93-104 groups
only by *flow* (issue), never by repository, and gives no instruction to
state a repo's overall direction before its items.

The Mission Board section (lines 117-194) is a separate, trigger-gated
aggregate view (renders only on explicit request or major transitions) —
it groups by state (running/waiting/done), not by repo, and is out of
scope per #309 (it is a different rendering, triggered differently, and
adding repo-grouping there is not what #309 asks for — #309 is about the
per-turn PR/decision report in step 5).

## Enforcement precedent (#298)

`on-the-record/hooks/` contains exactly `deliverable-guard.sh`,
`directive.sh`, `self-update.sh` — none inspect reply text or check
reply-shape. `grep` across `on-the-record/` for any test file or gate
referencing "REPLY STRUCTURE", "mission board", or `run.md` returns
nothing. #298 (open, unrelated fix direction — orchestrator
self-enforcement gates for approvals/merges) independently documents the
same fact: no hook or gate exists that can inspect the orchestrator's own
reply text today, only `directive.sh` (prose injection at prompt time,
not a post-hoc check). So a repo-level-grouping rule added to `run.md`
would land exactly as unchecked as the per-item rule it sits beside —
consistent with #309's own acceptance criterion #2 ("state whether and
how the rule is checked, or record explicitly that it is not").

## Overlap check

- **#298** — orchestrator self-enforcement gate (approvals/merges lack
  gates). Related root cause (no reply-inspecting hook exists) but a
  different fix target (gates for approve/merge actions, not reply
  formatting). No overlap in write set.
- **#303** — capability envelope / unverifiable verification steps in
  role sessions. Unrelated surface (role session capabilities, not
  orchestrator reply formatting).
- No other open issue found referencing `run.md`'s REPLY STRUCTURE or
  Mission Board sections via `gh issue list` search of title text
  containing "reply" or "board" (see below).

```
$ gh issue list --search "run.md reply structure" --state open
(no results beyond #309 itself)
```

## Design decision this proposal must settle

Whether the repo-level grouping is a **new top layer above flow-grouping**
(repo -> flow -> item) or a **replacement** of flow-grouping. #309's own
fix direction #1 says "adds a layer above the per-item rule; it does not
replace it" — settles this: repo is the outermost grouping, flow-headers
nest under it unchanged.
