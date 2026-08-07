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

A third, narrower kind (issue #435): a test-built `lambda` that stands in
for one of *this repo's own* functions (e.g. tests monkeypatch
`spawn._issue_comments`). The two interfaces above never covered this —
they verify external payload shapes (`gh` JSON, Claude CLI events), not
an internal function's own return-shape. `#287` changed
`spawn._issue_comments`'s return from `list[dict]` to
`tuple[list[dict], bool]`; the four production call sites were all
updated by that same change, but stub lambdas built to replace the
function during tests kept returning the old bare list — a divergence
invisible to a call-site search because a stub is not a call site.
`assert_stub_return_shape` closes that: it checks a stub's return value
against the real function's `-> ...` annotation.
"""

from __future__ import annotations
import inspect
import typing


def _fail(path: str, msg: str) -> None:
    raise AssertionError(f"{path}: {msg}")


def _check_shape(path: str, value, ann) -> None:
    """One level of `value` against `ann`, then recurse into `tuple`/`list`
    element types (warrant-hunter before-landing finding, issue #435:
    checking only the outer container let a same-arity tuple/list of
    arbitrary element types — e.g. `(5, "not-a-bool")` against
    `tuple[list[dict], bool]` — pass as a "match")."""
    origin = typing.get_origin(ann) or ann
    if isinstance(origin, typing.TypeVar) or origin is typing.Any:
        return
    if not isinstance(origin, type):
        return  # unsupported annotation shape (e.g. a bare TypeVar/Union) — skip, don't false-positive
    if not isinstance(value, origin):
        origin_name = getattr(origin, "__name__", str(origin))
        _fail(path, f"got {type(value).__name__}, expected {origin_name} (from annotation {ann!r})")
    args = typing.get_args(ann)
    if not args:
        return
    if origin is tuple:
        if len(args) != len(value):
            _fail(path, f"tuple of length {len(value)}, expected length {len(args)} (from annotation {ann!r})")
        for i, (elem, elem_ann) in enumerate(zip(value, args)):
            _check_shape(f"{path}[{i}]", elem, elem_ann)
    elif origin in (list, set, frozenset):
        for i, elem in enumerate(value):
            _check_shape(f"{path}[{i}]", elem, args[0])


def assert_stub_return_shape(stub, real, *args, **kwargs) -> None:
    """Call `stub(*args, **kwargs)` and check the result matches `real`'s
    `-> ...` return annotation (a runtime type, e.g. `tuple[list, bool]`
    or `list[dict]`), including `tuple`/`list`/`set` element types one
    level of nesting deep. Raises `AssertionError` naming the mismatch.

    `real` must carry a return annotation — this only checks stubs for
    functions that declare one (`spawn._issue_comments` does).
    """
    ann = inspect.signature(real, eval_str=True).return_annotation
    if ann is inspect.Signature.empty:
        _fail(getattr(real, "__qualname__", repr(real)),
              "has no return annotation to check a stub against")
    result = stub(*args, **kwargs)
    _check_shape(getattr(real, "__qualname__", repr(real)), result, ann)


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
