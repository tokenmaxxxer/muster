# Survey — issue-443 (contract-guard cross-repo PR resolution)

## Write set (confirmed by reading, not assumed)

- `on-the-record/hooks/contract-guard.sh` — the only file implementing the
  merge-time gate. 114 lines, embeds a Python heredoc (`GUARD`) run via
  `python3 -c "$GUARD"` with `CG_PAYLOAD` env carrying the PreToolUse JSON.
- `test_gates.py` — the repo's only gate test suite (1561 lines, pytest,
  Python gates under `gates/`). Grepped for `contract-guard` / `contract_guard`:
  no hits. **No test file for contract-guard.sh exists anywhere in the repo.**
  This must be created new (own test module, e.g.
  `on-the-record/hooks/test_contract_guard.py` or an addition to
  `test_gates.py` — decided in the proposal).
- `docs/specs/enforcement-boundary.md`, `docs/issue-441/proposals/2026-08-07-contract-enforcement-boundary.md`,
  `docs/issue-441/reports/architecture.md` — reference contract-guard.sh's
  design (issue-441/442 predecessor work) but are read-only context, not
  write targets for this issue (constraint: "판정 술어는 무변경" — behavior
  spec docs don't need edits, only the resolution mechanism).

## Current mechanism (root cause, confirmed by reading lines 34–113)

- `num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)` (line 55): matches only a
  bare whitespace-delimited digit run. A full PR URL
  (`https://github.com/o/r/pull/123`) never matches this (digits are glued
  to non-digit chars) — confirmed this is the *documented* unreached path
  the issue's repro exploited (comment lines 57–61).
- `gh_json()` (line 64) calls `subprocess.run(["gh", *args], ...)` with no
  `cwd=` and no `-R`/`--repo` flag ever appended — so `gh pr view <n>` and
  `gh issue view <n>` always resolve against the process's cwd (the
  session's cwd, i.e. on-the-record when invoked from there), regardless of
  a `cd <path> &&` prefix or `-R` flag present in the intercepted command
  string. Confirmed: the hook parses `cmd` as text only; it never executes
  or honors any `cd`/`-R` embedded in it.
- `approvers_path = os.path.join(os.getcwd(), "docs", "specs", "approvers.md")`
  (line 86): same defect — always cwd-relative, never target-repo-relative.
- No existing code anywhere in this file recognizes `-R`, `--repo`, a full
  GitHub PR URL as a repo-bearing pattern, or a leading `cd <path> &&`.
  All three of the issue's required forms are currently unhandled.

## Ecosystem / prior art

- `gh` CLI natively supports `-R owner/repo` (or `--repo`) on `pr view`,
  `issue view` to target a non-cwd repo without a local checkout — this is
  the standard idiom `gh` itself recommends for cross-repo scripting
  (confirmed via `gh pr view --help` output below).
- For the `cd <path> &&` prefix case, no `-R` is needed: running the `gh`
  subprocess with `cwd=<path>` (Python's `subprocess.run(..., cwd=path)`)
  reproduces exactly what the intercepted shell command would have done —
  `gh` infers the repo from the git remote of that directory.
- A full PR URL passed to `gh pr view <url>` is itself accepted natively by
  `gh` (no need to hand-split owner/repo) — but the hook also needs the bare
  PR number for the fail-open regex path already in place, so extracting
  `(owner/repo, number)` via one regex is simpler than a `gh pr view <url>`
  dual-path.

```
$ gh pr view --help | grep -A2 -- '-R,'
  -R, --repo [HOST/]OWNER/REPO   Select another repository using the
                                 [HOST/]OWNER/REPO format
```

## Decision this survey narrows

Three repo-identification forms in scope per the issue's requirement 1:
(a) `-R <owner/repo>` flag, (b) full PR URL, (c) `cd <path> &&` prefix.

- For (a) and (b): a target `owner/repo` string is known, but there is no
  local checkout of that repo in the session — so `docs/specs/approvers.md`
  for the target repo cannot be read from the local filesystem the way the
  existing code reads it for the cwd repo. This is a genuine capability
  gap, not a coding gap: the hook is zero-install by design (header
  comment lines 4–10) and has never fetched repo file contents over the
  API. Two real options exist: (i) fetch approvers.md via
  `gh api repos/<owner>/<repo>/contents/docs/specs/approvers.md`, adding a
  new network call class the hook doesn't currently make: or (ii) treat
  local-approvers-unavailable as fail-open/unreached, consistent with the
  file's own stated fail-open philosophy (header lines 20–26: "a lookup
  failure here is reported and passed through rather than blocking").
  The proposal must pick one and say why the other was rejected.
- For (c) `cd <path> &&`: the local path *is* a real checkout, so both the
  PR/issue `gh` lookups and the approvers.md read can resolve fully against
  the target repo with no capability gap. This form can be fully fixed, not
  just contained as unreached.

## Skip conditions checked

Neither scout-directive skip condition applies (this is not a pure bugfix
with zero design decision open — the approvers.md-for-remote-repo question
above is a real design choice) — but the "field" for this deliverable is
the `gh` CLI's own conventions, already surveyed above via `gh --help`,
which is sufficient prior art for a small internal hook fix. No
product-shaped external competitive scouting applies (this is not a
product surface a user experiences) — scout-brief.md is not written;
recorded here as the applicable narrow-scope judgment, not a blanket skip.
