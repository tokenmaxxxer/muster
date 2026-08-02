"""역할 세션 샌드박스(네트워크 차단)에서 `_spawn_one`이 부르는
`rulebook_checkout`/`core_root`(spawn.py)가 로컬 체크아웃 오버라이드
(`$TOKENMAXXXER_RULEBOOKS`/`$TOKENMAXXXER_CORE`)를 기본값으로 찾도록,
최소 픽스처 트리(`tests/fixtures/rulebooks/`)를 채운다. `setdefault`라
이미 값이 설정된 환경(실제 로컬 체크아웃을 가리키는 경우)은 그대로 둔다
— issue #204, docs/issue-204/proposals/rulebook-checkout-test-fixture.md.
"""

import os
from pathlib import Path

_FIXTURES = Path(__file__).parent / "tests" / "fixtures" / "rulebooks"

os.environ.setdefault("TOKENMAXXXER_RULEBOOKS", str(_FIXTURES))
os.environ.setdefault("TOKENMAXXXER_CORE", str(_FIXTURES / "tokenmaxxxer-core"))
