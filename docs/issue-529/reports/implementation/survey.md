# Survey — issue-529 (phase 1)

## Tree-walking helpers in gates/

| file | function | line | walk mechanism | prunes `.git` | prunes gitignored dirs (e.g. `runs/`) |
|---|---|---|---|---|---|
| `gates/gates.py` | `duplicate_test_basenames` | 943 | `os.walk(root)` | yes (`dirnames[:] = [d for d in dirnames if d != ".git"]`) | no |
| `gates/gates.py` | `schema_field_orphans` | 1157 | `root.rglob("*.py")` + `root.rglob("*.sh")` | filtered post-hoc (`".git" not in p.parts`) | no |
| `gates/gates.py` | `subprocess_call_shape_divergence` | 1002 | `git -C work ls-files "*.py"` (subprocess) | n/a (git-native) | yes, implicitly (git never lists gitignored files) |
| `gates/record_lint.py` | `find_records` | 194 | `os.walk(root)` | yes | not needed — output is post-filtered through `RECORD_PATH.match(rel)`, which only matches `docs/issue-*/reports/*.md`; `runs/` never matches this pattern, so it is unaffected by the contamination class |
| `gates/claims.py` | `_check_producer_exists` | 115 | `repo.rglob(filename)` | filtered post-hoc | no — same class, but produces a false **pass** (an orphan copy under `runs/` satisfies `producer-exists`) rather than a false **failure**; still worth fixing under the issue's "audit other tree walkers" requirement |

`subprocess_call_shape_divergence` (added for issue #419, landed on main) is the one walker in this file that already solved this: it shells out to `git ls-files` instead of walking the filesystem, so it never sees anything git doesn't track — including `runs/rulebooks/` session checkouts, which are gitignored and never `git add`-ed.

## Why `duplicate_test_basenames` and `schema_field_orphans` are the ones that fail live

Both walk `root` (the repo working tree) directly with no gitignore awareness. On a clean checkout, `runs/` doesn't exist, so both pass. On the live marketplace repo, `runs/rulebooks/` accumulates session checkouts of the *same repository* (containing their own `gates/`, `docs/specs/`, `test_*.py` copies) — these are real filesystem content, gitignored, never committed, but indistinguishable from real repo content to a raw walk. That produces:
- `duplicate_test_basenames`: every test basename in a `runs/rulebooks/<session>/...` checkout collides with the same basename in the real tree → false positive.
- `schema_field_orphans`: `.py`/`.sh` files inside `runs/rulebooks/<session>/...` get scanned as "code" and can shift orphan/non-orphan verdicts depending on what's inside the checkout at scan time → flaky verdict, not a deterministic failure either.

## Existing test fixtures for the two gates (constrains the fix)

- `gates/test_capability_gates.py`'s `t_schema_field_orphans_flags_documented_unread_field` and `t_schema_field_orphans_passes_when_field_is_read_elsewhere` build a plain `tempfile.TemporaryDirectory()`, not a git repo, and call `gates.schema_field_orphans(d, {})` directly.
- `gates/test_duplicate_test_basenames.py`'s four tests likewise build plain tempdirs (no git init anywhere in that file) and call `gates.duplicate_test_basenames(root)` directly.
- `gates/test_recurrence.py` has a `_git_repo(...)` helper (git init + commit) used by `subprocess_call_shape_divergence`'s own tests — proof the codebase already has the fixture shape needed if a gate requires a real git repo.

This matters for the fix direction: a pure git-ls-files-based rewrite (mirroring `subprocess_call_shape_divergence`) would return nothing on the two gates' existing plain-tempdir fixtures (no git repo → git ls-files fails/returns empty), silently breaking `t_schema_field_orphans_flags_documented_unread_field` and all four `duplicate_test_basenames` tests, none of which currently exercise git at all. Rewriting those fixtures to add git-repo scaffolding is itself a legitimate direction but is a materially larger diff than the issue's stated minimum.

## Acceptance requirements recap (from issue #529)

1. `python3 -m pytest gates/ -q` exits 0 on the live repo with `runs/rulebooks/` populated (needs a fixture simulating this).
2. A fixture creating a fake duplicate/orphan under a temp `runs/` shows the gate skipping it, while the same file outside `runs/` is still caught.
3. Provenance: executed-unit — the fix must be exercised by a real pytest run, not just asserted.
4. Empty-state: no `runs/` dir → same pass, same fixture.

## Alternatives visible in the current code

- **A: git-ls-files-based enumeration**, matching `subprocess_call_shape_divergence`. Fully correct against `.gitignore` (any gitignored path, not just `runs/`) but requires both target gates' existing tempdir-based test fixtures to become real git repos (`_git_repo`-style), a materially larger touch than the issue's stated minimum.
- **B: explicit path-prefix exclusion** — prune a fixed set of top-level directory names (starting with `runs`) during the walk, no git dependency. Matches the issue's literal minimum ("exclude gitignored paths (at minimum `runs/`)"), keeps existing plain-tempdir fixtures passing unmodified, but only covers the named directories, not arbitrary `.gitignore` entries.
- **C: hybrid** — prune the fixed name set (B) unconditionally, and when the target directory is actually inside a git working tree, additionally consult `git check-ignore` per-subdirectory during the walk for full `.gitignore` coverage; when not in a git repo (as in the existing tempdir tests), the git check is skipped/no-ops and behavior reduces to (B).
