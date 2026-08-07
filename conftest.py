"""역할 세션 샌드박스(네트워크 차단)에서 `_spawn_one`이 부르는
`rulebook_checkout`/`core_root`(spawn.py)가 로컬 체크아웃 오버라이드
(`$TOKENMAXXXER_RULEBOOKS`/`$TOKENMAXXXER_CORE`)를 기본값으로 찾도록,
최소 픽스처 트리(`tests/fixtures/rulebooks/`)를 채운다. `setdefault`라
이미 값이 설정된 환경(실제 로컬 체크아웃을 가리키는 경우)은 그대로 둔다
— issue #204, docs/issue-204/proposals/rulebook-checkout-test-fixture.md.
"""

import os
import subprocess
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).parent / "tests" / "fixtures" / "rulebooks"

os.environ.setdefault("TOKENMAXXXER_RULEBOOKS", str(_FIXTURES))
os.environ.setdefault("TOKENMAXXXER_CORE", str(_FIXTURES / "tokenmaxxxer-core"))

# issue #360: test_approve_scope.py used to monkeypatch spawn.subprocess.run
# (and spawn._repo_slug/_pr_for_branch/_issue_comments) with raw attribute
# assignment and no teardown, leaking process-wide state into every test
# collected after it. A per-test isolation check can't catch this — it only
# observes state at its own fixed collection position, so a leak from a file
# collected later is invisible to it. This session-scoped fixture snapshots
# the guarded attributes once at session start and compares again at session
# teardown, which sees every module regardless of collection order.
_GUARDED = [
    ("spawn", "_repo_slug"),
    ("spawn", "_pr_for_branch"),
    ("spawn", "_issue_comments"),
]


@pytest.fixture(scope="session", autouse=True)
def _no_global_state_leak():
    import spawn

    before_run = subprocess.run
    before_attrs = [getattr(spawn, name) for _mod, name in _GUARDED]
    yield
    assert subprocess.run is before_run, (
        "subprocess.run was left patched after the test session — "
        "some test replaced it without restoring it on teardown"
    )
    after_attrs = [getattr(spawn, name) for _mod, name in _GUARDED]
    for (mod, name), before, after in zip(_GUARDED, before_attrs, after_attrs):
        assert after is before, (
            f"{mod}.{name} was left patched after the test session — "
            "some test replaced it without restoring it on teardown"
        )
