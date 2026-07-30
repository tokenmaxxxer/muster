---
proposal: docs/proposals/2026-07-30-issue-140-routing-residue.md
---

# Hunt record — issue-140-routing-residue

## after-proposal — stance 1: consumers may depend on exact roles/*.json wording (produces/use_when strings)

Verdict: NO FINDING
Seed: roles/ux-design.json produces-field edit, roles/verify.json use_when-field edit, new test_vocab_coherence_roles.py

Searched spawn.py, test_spawn.py, test_gates.py, and all *.py for verbatim matches of the removed parenthetical
("reviewed 가 coding 을 깨운다"), the old verify.json use_when text ("주장을 눈으로 검증할 수 없을 때... 적대적으로 찾는다"),
and any string-equality/substring assertions against roles/*.json decides/use_when/produces fields. Only spawn.py:2041
reads meta.get('use_when','') for display printing (no assertion on content), and test_spawn.py's only hit is an
unrelated comment. Ran test_vocab_coherence_roles.py against the full roles/ directory (8 files) — passes, no false
positive from any other role's decides/use_when/produces text (none contain "wake", "wakes", "깨운", or "라우팅").
