scout: skipped — pure bugfix (fix condition: `shutil.rmtree` lacks read-only retry handler; expected behavior is a standard stdlib pattern, no product/design decision open).

# Current-state survey — issue #229

## Symptom site

`spawn.py:2137-2180`, `clean` role handler in `main()`. Loop over workspace
dirs under `wb`; for each dir judged safe (no uncommitted changes, no
unpushed commits), calls `shutil.rmtree(w)` at line 2169 with no error
handler. Go module cache files under `.muster-cache/gomod/...` are laid
down read-only by `go mod download`; `rmtree`'s default unlink fails on
them with `PermissionError`, which is unhandled — the exception propagates
out of the `for w in ...` loop, aborting the whole `clean` run and leaving
every workspace after the failing one (in `sorted(wb.glob("*"))` order)
untouched.

## Write set

- `spawn.py` — the `rmtree` call site (~line 2169) and its immediate
  surroundings (the `for w in ...` loop body, lines 2147-2179).
- `test_spawn.py` — new regression test(s) for the `clean` role: a
  read-only file inside a workspace judged safe must not abort the whole
  clean pass, and the workspace must still be removed.

No other file references `shutil.rmtree` (`grep -rn rmtree` outside tests
returns only this one call site). No env var, dependency, or schema
changes.

## Existing test coverage

`test_spawn.py` has no test currently exercising `role == "clean"` (no
hit for `"clean"` role dispatch in existing tests). Tests in this file
follow a `unittest.TestCase` + `tempfile`/`Path` + `mock.patch` pattern,
with `spawn` imported directly and `subprocess.run`/network calls
monkeypatched. A `clean`-focused test will need to build a fake
`MUSTER_WORK_DIR` tree with a `.git` dir (git status/log calls are real
`subprocess.run` — the existing safe-workspace judgment path shells out to
real `git`, so tests will need a real git repo scaffolded under `tmp_path`
rather than mocking `subprocess.run`, matching how `clean`'s own git
calls are unmocked in production use).

## Fix shape (no design decision — standard library pattern)

Python's own `shutil.rmtree` docs recommend the `onexc` (3.12+) /
`onerror` (pre-3.12) callback pattern: on `PermissionError`, `os.chmod`
the offending path writable and retry the failed function. This project's
`test_spawn.py` doesn't currently pin a minimum Python version away from
this ambiguity, so the fix should support both `onexc` and `onerror`
depending on availability (`shutil.rmtree` raises `TypeError` if you pass
an unsupported kwarg on the wrong Python version) — or just target
whichever `shutil.rmtree` signature the running interpreter has via a
runtime check (`sys.version_info`).

Failure isolation: wrap the per-workspace body (the `rmtree` call plus
sibling-file cleanup, lines 2168-2178) in a `try/except`, so one
workspace's unrecoverable removal failure (e.g. a genuinely undeletable
path even after chmod retry) is logged/counted and the loop continues to
the next workspace, rather than aborting the whole `clean` pass. This
directly matches the issue's "기대 동작": "실패 시에도 한 워크스페이스
실패가 나머지 정리를 중단시키지 않는다."

## Alternatives considered

- Shelling out to `rm -rf` instead of `shutil.rmtree`: would sidestep the
  read-only-file problem (unlink of a read-only file only requires write
  permission on the *parent* dir, which `rm` handles fine on POSIX) but
  introduces a platform dependency (no `rm` on Windows) the rest of
  `spawn.py` doesn't currently have, and swaps a catchable Python
  exception for parsing subprocess exit codes/stderr — worse failure
  isolation, not better. Rejected in favor of the stdlib `onexc`/`onerror`
  retry pattern, which is portable and keeps errors as catchable Python
  exceptions for the per-workspace isolation wrapper.
