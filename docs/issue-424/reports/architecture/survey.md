# Current-state survey — issue #424

**Scope correction (2026-08-07, two operator comments, both after this survey's facts were
gathered)**: the facts below (call sites, line numbers, existing gates) are unchanged and still
load-bearing. What changed is the question asked of them — from "how much duplication/drift/growth
exists" (withdrawn) to "is there wiring making symptom-handling structurally unreachable at each
instance" (current, see proposals/accumulation-gate.md). This survey's facts are read against the
new question directly in the proposal; no re-survey was needed since the tree state didn't move.

## What exists today

- `gates/gates.py` (786 lines) is the gate registry; individual gate modules live beside it
  (`gates/ci.py`, `gates/acceptance_gate.py`, `gates/closure_sweep.py`, `gates/spec_index.py`,
  `gates/skip_gate.py`, `gates/issue_bundling.py`, `gates/spawn_coverage.py`, `gates/risk_report.py`,
  `gates/pr_reference.py`, `gates/flows.py`), each mirrored by a `gates/test_*.py`.
- `gates/gates.py:738` has one existing dedup check, `duplicate_test_basenames()` — it checks that
  no two test files share a basename. It does not check invocation shapes, call-site signatures, or
  list growth. No other gate touches duplication, signature consistency, or list-growth today.
- **Instance 1 (duplicate `gh api` shapes).** `gates/ci.py` has 6 subprocess/`gh` call sites
  (`ci.py:59,79,104,122,204,256`), each with its own inline `import subprocess` +
  `subprocess.run(cwd=repo, capture_output=True, text=True)`. Three share the `gh pr view --json <field>`
  shape; two share `gh api repos/{slug}/...`; none go through a shared helper. `ci.py:188`'s comment
  explicitly tells the next author to reuse the `gh api repos/{slug}/...` shape — a documented
  convention, not an enforced one.
- **Instance 2 (`_phase2_record_evidence` signature drift).** Defined `gates/ci.py:223`, signature
  `(repo, pr, branch, issue) -> bool`. Two call sites today — `gates/ci.py:377` and
  `gates/closure_sweep.py:113` — both consistent. Nothing in the tree records that
  `closure_sweep.py` depends on this signature; #369 changing it silently would only be caught by
  running `closure_sweep`'s own tests, if someone remembers to.
- **Instance 3 (`PACKAGE_REGISTRY_HOSTS`-shaped constant).** The named constant lives in `spawn.py:118`
  (not `gates/`), introduced fully-formed in one commit (`f6b30b3`, issue #38) — not itself a
  live "grew every delivery" example in this repo's git history. #303's precedent (refused after the
  operator caught it once) is the closer match; no automated check currently watches for
  "same list touched N deliveries in a row."
- **Instance 4 (a second notion of "delivered").** No structural artifact exists that would catch two
  parallel definitions of the same concept; #383's author avoided it by convention and said so in
  prose, not because anything would have flagged it.
- **Instance 5 (43 identical one-line edits to `roles/*.json`).** No mechanism anywhere asks whether a
  repeated identical diff across many files is itself a signal that the value belongs in one place
  instead of N.

## Test/CI baseline

`python3 -m pytest -q --ignore=gates`: 406 passed, 1 failed (`test_spec_index.py::t_baseline_repo_passes`,
pre-existing `docs/specs/reconciled-index.md` hash drift against `protocol.md` — unrelated to this
issue, not touched by this proposal). `gates/` itself does not collect under this invocation (#398,
confirmed: `gates/` is a separate package with import-path assumptions main's collection doesn't
satisfy) — `gates/test_*.py` were exercised only via the direct survey run, not via this command.

## Gap this proposal targets

Nothing in `gates/` or elsewhere checks accumulation shape. The only existing dedup gate
(`duplicate_test_basenames`) is same-family (naming collisions) but does not generalize to
invocation-shape or signature-consistency checking. Scout coverage: see `scout-brief.md`.
