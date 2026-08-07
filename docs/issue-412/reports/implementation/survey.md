# Survey — issue #412 (shallow re-clone silently invalidates history checks)

## Write set surveyed
- `on-the-record/hooks/self-update.sh` — the SessionStart hook whose self-clone
  fallback (`_checkout_resolve`, final branch, lines 30-32) produced the
  shallow checkout in the reported incident.
- Nothing else under `on-the-record/hooks/` touches clone/pull.

## Current behavior (read, not run)
`_checkout_resolve()` tries, in order: `TOKENMAXXXER_CHECKOUT` env override,
ancestor directories of the hook itself, the marketplace clone, an
already-present new-path checkout, an already-present old-path checkout,
and only then `git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own"`
with no `--depth` flag. After resolving, the script runs
`git -C "$CHECKOUT" pull -q --ff-only` unconditionally and exits 0 regardless
of outcome (the EXIT trap swallows non-zero/non-2 codes).

Two things follow from reading this:
1. The script's own `git clone` call carries no `--depth`, so it is not
   shallow by construction. I checked this repo's global/system git config
   (`git config --global --list`, `git config --system --list`) and the
   session's `GIT_*` env vars for a default depth/filter override
   (`clone.defaultDepth`, `partialClone*`, `GIT_DEPTH`-style vars) — found
   none. So the shallow result in the incident was not reproduced by reading
   this script alone; the incident's shallow depth-1 history most plausibly
   came from whatever produced the "작업 디렉터리를 읽을 수 없습니다" failure
   beforehand (a different tool's checkout, or an environment-level
   shallow-clone default not visible from this static read) rather than from
   `git clone` in this file. This is a **read-only finding, not a run** — per
   #416 it does not settle the question; it only narrows where the
   instrumentation needs to sit.
2. Regardless of root cause, the script has no step anywhere that checks
   `git rev-parse --is-shallow-repository` on the checkout it just resolved
   or pulled, and no place it would record such a finding for the
   orchestrator to see. This is the actual gap named in scope item 1: "must
   not produce a shallow checkout, **or must record that it did** somewhere
   the orchestrator will see before trusting history."

## Item 3 — other history-dependent checks in the codebase
Searched (per #358, recording what was searched):
```
grep -rln -E "git (rev-list|log|merge-base|describe|shallow)" \
  --include="*.sh" --include="*.py" --include="*.js" --include="*.ts" . \
  | grep -v /docs/
```
No matches outside `docs/`. Every hit for that pattern lives under
`docs/**/reports` or `docs/**/proposals` (prior issues' written records
quoting git commands in prose), not in executable code. **Absence recorded**:
as of this survey, no other executable check in the repo reads git history
(rev-list/log/merge-base/describe) to draw a conclusion — this hook is the
only such site. If one is added later, it inherits the same shallow-check
obligation this proposal establishes here.

## Item 2 — why the working directory disappeared
Not independently reproducible from this session (different session, past
incident). Searched the reflog quoted in the issue and this repo's shell
history/session logs for a second occurrence — found none accessible from
this checkout. Recording per #358: searched `git reflog` here (this
session's checkout is not shallow: `git rev-parse --is-shallow-repository`
→ `false`, `git rev-list --count HEAD` → the full ~history), and found no
local artifact (crash log, orphaned lock file) explaining the prior
session's directory disappearance. This is an absence I can record, not one
this session can close — item 2 stays open as an unexplained upstream event.

## Existing related work
- `docs/issue-218/proposals/core-checkout-freshness-reporting.md` (issue
  #218, "orchestrator's clone drifts behind remote") — same file family
  (`self-update.sh`-adjacent checkout-freshness reporting), explicitly
  scoped as boundary-distinct from this issue in #412's own text (#392 is
  "old but complete"; #412 is "current but truncated"). Confirms the
  pattern of adding a status-reporting side-channel is the established
  approach in this codebase for checkout-state facts the orchestrator can't
  otherwise see.

## Skip-condition check (scout-directive)
This is not a pure bugfix with a single obvious code change (the fix must
choose *where* to check shallowness and *how* to surface it to the
orchestrator — a design decision), so scouting would normally apply. No
external product/library research is relevant here — this is an internal
git-plumbing correctness fix with no ecosystem best-in-class to compare
against (git itself has no external competitor to scout). Skipping the
external sweep on that basis; the "scout" here is this repo-internal survey.
