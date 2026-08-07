"""Shape assertions for hand-typed test fixtures that stand in for
external interfaces (issue #335).

A fake that isn't checked against the real interface it mimics is a
private, unmaintained spec: it drifts, and the tests built on it keep
passing while meaning less and less. These functions walk a fixture's
structure and raise `AssertionError` naming the exact missing/wrong-typed
field on mismatch, so drift fails loudly at fixture-construction time
instead of silently passing forever.

Two interfaces are covered, per the issue-335 proposal:
- `assert_gh_paginate_slurp_shape`: `gh api --paginate --slurp` envelope,
  verified against a real captured sample
  (`tests/fixtures/golden/gh_paginate_slurp_sample.json`).
- `assert_claude_stream_event_shape`: Claude Code CLI `stream-json`
  events, derived from what `spawn.py`'s parser actually reads
  (internal-consistency check only — see the proposal's Out of scope).
"""

from __future__ import annotations


def _fail(path: str, msg: str) -> None:
    raise AssertionError(f"{path}: {msg}")


def assert_gh_paginate_slurp_shape(payload) -> None:
    """`gh api --paginate --slurp` output: a list of pages, each page a
    list of comment objects with `user.login` (str) and `body` (str) —
    the two fields `spawn.py._issue_comments` reads (`spawn.py:948`).
    """
    if not isinstance(payload, list):
        _fail("$", f"expected list of pages, got {type(payload).__name__}")
    for pi, page in enumerate(payload):
        if not isinstance(page, list):
            _fail(f"$[{pi}]", f"expected page to be a list, got {type(page).__name__}")
        for ci, comment in enumerate(page):
            base = f"$[{pi}][{ci}]"
            if not isinstance(comment, dict):
                _fail(base, f"expected comment object, got {type(comment).__name__}")
            if "user" not in comment:
                _fail(base, "missing required field 'user'")
            user = comment["user"]
            if not isinstance(user, dict):
                _fail(f"{base}.user", f"expected object, got {type(user).__name__}")
            if "login" not in user:
                _fail(f"{base}.user", "missing required field 'login'")
            if not isinstance(user["login"], str):
                _fail(f"{base}.user.login", f"expected str, got {type(user['login']).__name__}")
            if "body" not in comment:
                _fail(base, "missing required field 'body'")
            if not isinstance(comment["body"], str):
                _fail(f"{base}.body", f"expected str, got {type(comment['body']).__name__}")


_TOP_LEVEL_TYPES = {"result", "user", "assistant"}
_BLOCK_TYPES = {"tool_result", "tool_use"}


def assert_claude_stream_event_shape(event: dict) -> None:
    """Claude Code CLI `stream-json` event, shaped per what
    `spawn.py`'s parse loop actually reads (`spawn.py:3161-3230`,
    `classify` at `spawn.py:1268`, `_tool_result_text` at
    `spawn.py:1608`, `_prior_event_details` at `spawn.py:1717`).

    Internal-consistency check only: verifies a fixture matches
    `spawn.py`'s own expectations, not that those expectations still
    match Anthropic's live CLI output (proposal's Out of scope).
    """
    if not isinstance(event, dict):
        _fail("$", f"expected event object, got {type(event).__name__}")
    if "type" not in event:
        _fail("$", "missing required field 'type'")
    ev_type = event["type"]
    if ev_type not in _TOP_LEVEL_TYPES:
        _fail("$.type", f"expected one of {sorted(_TOP_LEVEL_TYPES)}, got {ev_type!r}")

    if ev_type == "result":
        if "permission_denials" in event:
            denials = event["permission_denials"]
            # spawn.py:3170-3182 explicitly tolerates absent/None/non-list;
            # only a present *list* is walked further, and each item that
            # is a dict is checked for 'tool_name'.
            if isinstance(denials, list):
                for i, d in enumerate(denials):
                    if isinstance(d, dict) and "tool_name" not in d:
                        _fail(f"$.permission_denials[{i}]",
                              "dict present but missing 'tool_name'")
        return

    # user / assistant events carry message.content[]
    if "message" not in event:
        _fail("$", f"'{ev_type}' event missing required field 'message'")
    message = event["message"]
    if not isinstance(message, dict):
        _fail("$.message", f"expected object, got {type(message).__name__}")
    if "content" not in message:
        _fail("$.message", "missing required field 'content'")
    content = message["content"]
    if not isinstance(content, list):
        _fail("$.message.content", f"expected list, got {type(content).__name__}")

    for i, block in enumerate(content):
        base = f"$.message.content[{i}]"
        if not isinstance(block, dict):
            _fail(base, f"expected block object, got {type(block).__name__}")
        if "type" not in block:
            _fail(base, "missing required field 'type'")
        btype = block["type"]
        if btype not in _BLOCK_TYPES:
            continue  # other block types (e.g. 'text') are outside this parser's reads
        if btype == "tool_result":
            for field in ("is_error", "content", "tool_use_id"):
                if field not in block:
                    _fail(base, f"tool_result block missing required field '{field}'")
            if not isinstance(block["is_error"], bool):
                _fail(f"{base}.is_error", f"expected bool, got {type(block['is_error']).__name__}")
            if not isinstance(block["tool_use_id"], str):
                _fail(f"{base}.tool_use_id", f"expected str, got {type(block['tool_use_id']).__name__}")
            tr_content = block["content"]
            if not isinstance(tr_content, (str, list)):
                _fail(f"{base}.content", f"expected str or list, got {type(tr_content).__name__}")
        elif btype == "tool_use":
            for field in ("id", "name"):
                if field not in block:
                    _fail(base, f"tool_use block missing required field '{field}'")
                if not isinstance(block[field], str):
                    _fail(f"{base}.{field}", f"expected str, got {type(block[field]).__name__}")
