---
kind: proposal
date: 2026-07-29
status: proposed
subject: issue-73
role: coding
---

# Sync `protocol.md`/`protocol.ko.md`/`README.md`/`ledger/collect.py` to contract v3, and retire `docs/superpowers/` into `docs/decisions/`

## files

Frozen write set for phase 2 (this proposal freezes it; it does not expand):

1. `protocol.md` (repo root) — the six v2 statements issue #73 names, plus the
   extra v2 residue this survey found at `:84` and `:228-229`.
2. `protocol.ko.md` (repo root) — the same six, plus residue at `:80` and
   `:204-207`.
3. `README.md` — remove the `spawn.py approve` row from the "Every command"
   table at `:280`, and fix the adjacent `--unattended` line (`:277`) that
   names the deleted "mint" machinery.
4. `ledger/collect.py` — the v2 comments at `:26` and `:69`.
5. `spawn.py`, `wakes.py`, and `test_gates.py` (the gates test file; resolved
   repo-relative path is `test_gates.py`, at repo root, not under a
   subdirectory) — touched ONLY to remove any remaining
   `docs/reports/records/` string. Verified by
   `rg -n "docs/reports/records" .` (2026-07-29): `spawn.py` and `wakes.py` do
   **not** contain the string and stay untouched; `test_gates.py:21` does
   (`"""계약 v2 §10 의 블랙보드를 만든다: docs/reports/records/<subject>/<역할>.md"""`)
   and needs it removed.
6. `docs/decisions/2026-07-29-headless-cli-measured-facts.md` — NEW. The
   measured CLI facts extracted from `docs/superpowers/` before it is
   retired.
7. `docs/decisions/2026-07-29-permanently-closed-alternatives.md` — NEW. The
   permanently-rejected alternatives with their reasons (MCP board server,
   stream-json as an approval channel, `--bare`/`CLAUDE_CONFIG_DIR`, the
   Agent SDK as driver, containers, a model as scheduler, cloud cron).
8. `docs/superpowers/` — DELETED entirely (4 files, 3282 lines, per
   `docs/issue-73/reports/coding/survey-superpowers.md`'s inventory). The
   survey established zero inbound references from outside the directory.
9. `docs/issue-73/reports/coding.md` — the phase-2 record, written in phase 2
   only. Listed here so the write set is honest; phase 1 does not touch it.

## Request

Issue #73, "docs lag the code after the v3 migration": the contract v3
migration moved the code but left the prose behind, and a contract-adjacent
document that is behind the code is called out as the most dangerous kind of
drift in this repository. The issue enumerates four items and one "Done
when":

1. `protocol.md` / `protocol.ko.md` carry six v2 statements: the abolished
   per-repo contract-copy claim (canonical contract now lives only at
   `core/contract/role-handoff-contract.md` in `tokenmaxxxer-core`); the
   abolished board path `docs/reports/records/<subject>/<role>.md` (now
   `docs/issue-<n>/reports/<role>.md`, `main`-merged only, opt-in marker
   `docs/specs/approvers.md`); "all six roles" (now nine); §5's title
   "Approval — tokens" (v3 deleted the token machinery whole; approval is a
   GitHub act — an `APPROVED` review, or a comment that is exactly
   `APPROVE issue-<n>/<role>`, from a login in `approvers.md`, kept honest by
   `gh-guard` in the default single-account setup); invariant 4 "An actor
   cannot mint its own approval" (nothing left to mint); shipping-order row 5
   "a token minted by a separate context"; and §8's "buildable but not yet
   built" WAKES-ON watcher (`wakes.py` + `spawn.py drive` are that watcher).
2. `README.md:280` advertises `python3 spawn.py approve <kind> --subject <s>`
   in the "Every command" table, contradicting `README.md:83` ("`spawn.py
   approve` is gone") and the code (hard-exit at `spawn.py:1388-1390`). The
   adjacent `--unattended` line describes "mint off", naming machinery that
   no longer exists.
3. `ledger/collect.py:26,69` — comments say "계약 v2 의 보드 자리" and "v2 를
   먼저 보고"; the code already globs the v3 path
   `docs/issue-*/reports/review.md`.
4. `docs/superpowers/` sits outside the six standing buckets, itself a
   contract v3 §10 layout violation. Before retiring it, the issue requires
   extracting the part that does not expire into `docs/decisions/`: the
   measured CLI facts (headless default permissions silently deny Write;
   `--plugin-dir` loads hooks fully in headless; `--tools ""` is the
   disable-all spelling, not `--allowed-tools ''`; `--settings`/`--plugin-dir`
   are not restored on `--resume`; hooks fire for subagent tool calls), and
   the permanently closed alternatives with their reasons (MCP board server,
   stream-json as an approval channel, `--bare`/`CLAUDE_CONFIG_DIR`, the
   Agent SDK as driver, containers, a model as scheduler, cloud cron).

Done when: no `docs/reports/records/` string remains in the repository; the
removed `approve` command is gone from `README.md`; `python3 gates/ci.py .` is
clean apart from the expected protected-path report for `protocol.md` /
`protocol.ko.md`.

This proposal follows those four items and that "Done when" exactly; it does
not add scope beyond the frozen write set above.

## Constraints

- **Two decision files, not one.** The extraction splits into
  `docs/decisions/2026-07-29-headless-cli-measured-facts.md` and
  `docs/decisions/2026-07-29-permanently-closed-alternatives.md`. Measured
  facts and permanent rejections are different kinds of durable content and
  do not belong in one file. This is decided, not open for phase 2 to
  re-litigate.
- **`docs/decisions/` does not exist on disk.** It is named by the contract's
  six standing buckets but currently holds zero files. These two files are
  its first inhabitants. They follow the `docs/proposals/` frontmatter
  convention (`kind:`/`date:`/`status:`/`subject:`), with `kind: decision`.
- **`protocol.md` and `protocol.ko.md` are gate-protected root paths**
  (`gates/gates.py:27-30`, `PROTECTED_ROOT_FILES`). `python3 gates/ci.py .`
  reporting a change to them in phase 2 is correct behaviour, not a failure —
  a human reviews it on the PR. This is stated here so phase 2 does not treat
  that report as a blocker to fix around.
- **`spawn.py` and `wakes.py` are conditional.** Verified 2026-07-29 via
  `rg -n "docs/reports/records" .`: neither file contains the string today.
  If phase 2's own re-check confirms the same, both stay untouched — only
  `test_gates.py` in that group needs an edit.
- No file outside the frozen write set above is in scope. Per the
  scope-exceeded rule, if phase 2 finds it needs to touch a file not listed
  here, that is a STOP-and-re-propose condition, not a judgment call to make
  silently.

## What will be done

1. **`protocol.md` / `protocol.ko.md`** — apply the six issue-cited
   corrections plus the two extra residues the survey found by grep for the
   same "v2"/"six roles"/"eight rulebooks" pattern outside the issue's cited
   lines:
   - `:44-47` / `:43-46` — replace the "v2, `status: final`, lives in
     `review-agent-rulebook`, all six roles" authority statement with: the
     contract is v3, lives only at `core/contract/role-handoff-contract.md`
     in `tokenmaxxxer-core` (repos carry no copy), and covers nine roles.
   - `:49-51` / `:48-50` — replace the abolished board path
     `docs/reports/records/<subject>/<role>.md` with
     `docs/issue-<n>/reports/<role>.md`, `main`-merged only, plus the
     `docs/specs/approvers.md` opt-in marker.
   - `:96` / `:91` — the same abolished path repeated for the `qa` record
     example; same replacement.
   - `:175-194` / `:161-179` (§5) — retitle "Approval — tokens" to name
     approval as a GitHub act, and replace the verdict-token description with
     the `APPROVED` review / `APPROVE issue-<n>/<role>` comment mechanism
     from a login in `approvers.md`, kept honest by `gh-guard`.
   - `:203-204` / `:186` (invariant 4) — replace "mint its own approval" with
     "approve its own change", naming the GitHub-act mechanism and the
     separate-session relay.
   - `:221` / `:200` (shipping-order row 5) — replace "a token minted by a
     separate context" with "a GitHub approval (review/comment) relayed by a
     separate context".
   - `:228-229` / `:206-207` (§8 unsettled) — replace "buildable but not yet
     built" with "`wakes.py` plus `spawn.py drive` are that watcher — built".
   - `:84` / `:80` (extra residue, transition-state paragraph) — "all eight
     rulebooks ... v2 board" → "all nine rulebooks ... v3 board".
   - `:85-90` / `:81-85` (extra residue, same paragraph) — "muster reads the
     v2 board first ... has not moved to v2 yet" → the v3 equivalents.
2. **`README.md`** — delete the `python3 spawn.py approve <kind> --subject
   <s>` row at `:280` from the "Every command" table (no replacement row: the
   mechanism it advertised does not exist; `README.md:79-85` already
   documents the real GitHub-act mechanism). Fix the adjacent `:277`
   `--unattended` line so it no longer says "mint off" — restate in terms of
   what `--unattended` actually gates (human absent, human gates still stand)
   without naming deleted machinery.
3. **`ledger/collect.py`** — `:26` "계약 v2 의 보드 자리" → describes the v3
   board path the code already globs (`docs/issue-<n>/reports/review.md`).
   `:69` docstring "v2 를 먼저 보고" → "v3 를 먼저 보고". No code logic
   changes; `records()`'s glob and `report()`'s v3 wording (`:126-127`)
   already match v3 and are left as-is.
4. **`test_gates.py`** — `:21` docstring's
   `docs/reports/records/<subject>/<역할>.md` reference → the v3 board path,
   consistent with what `spawn.BOARD`/`_board()` actually construct in the
   test helper. `spawn.py` and `wakes.py` — no edit, per the conditional
   above (re-verify with `rg` at the start of phase 2; if either has since
   gained the string, extend the edit to it and note the addition in the
   phase-2 record).
5. **`docs/decisions/2026-07-29-headless-cli-measured-facts.md`** (new) —
   `kind: decision`, `date: 2026-07-29`, `status: proposed` (or `landed` per
   phase-2 convention), `subject: issue-73` frontmatter, English prose, one
   entry per issue-enumerated fact (headless default permissions silently
   deny Write; `--plugin-dir` loads hooks fully in headless; `--tools ""` is
   the disable-all spelling, not `--allowed-tools ''`;
   `--settings`/`--plugin-dir` not restored on `--resume`; hooks fire for
   subagent tool calls), each cited to its `path:line` source inside
   `docs/superpowers/` before that directory is deleted in the same change.
6. **`docs/decisions/2026-07-29-permanently-closed-alternatives.md`** (new) —
   same frontmatter shape, one entry per permanently-rejected alternative
   (MCP board server; stream-json as an approval channel;
   `--bare`/`CLAUDE_CONFIG_DIR`; the Agent SDK as driver; containers; a model
   as scheduler; cloud cron), each with its rejection reason, cited to its
   `path:line` source inside `docs/superpowers/`.
7. **`docs/superpowers/` deletion** — once both decision files carry the
   extracted material, delete the directory in full (`plans/` and `specs/`
   subdirectories and all 4 files), in the same phase-2 change that adds the
   two new files, so the extraction and the retirement land atomically.

## Out of scope

- No behaviour change to any Python code beyond comment/string edits — no
  logic, glob pattern, control flow, or function signature changes in
  `ledger/collect.py`, `test_gates.py`, `spawn.py`, or `wakes.py`.
- No new dependency.
- No new environment variable.
- No migration (of data, of board records, or of any repo other than this
  one).
- No edits to `docs/superpowers/plans/*.md` or `docs/superpowers/specs/*.md`
  content beyond what is needed to extract quotations into the two new
  decision files — the directory is deleted, not reworked in place.
- No changes to `core/contract/role-handoff-contract.md` or anything in
  `tokenmaxxxer-core` — that repo is out of this repo's reach entirely.
- Anything not named in the frozen write set under `## files`. If phase 2
  discovers it needs to touch a file outside that set, that is a
  scope-exceeded condition: phase 2 stops and this proposal is re-opened
  rather than silently expanded.

## How I will know it worked

Restating the issue's own "Done when" as checkable commands, to run after
phase 2 lands:

```
rg 'docs/reports/records/' .
```
returns nothing (no output, exit status indicating no matches).

```
grep -n 'spawn.py approve' README.md
```
returns nothing — the `approve` row is gone from the "Every command" table.

```
python3 gates/ci.py .
```
is clean apart from the expected protected-path report for `protocol.md` and
`protocol.ko.md` (per `gates/gates.py:27-30`'s `PROTECTED_ROOT_FILES`) — that
report is the correct signal that a human should review those two files on
the PR, not a failure to fix around.
