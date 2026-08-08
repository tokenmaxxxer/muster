---
proposal: docs/issue-466/proposals/2026-08-08-decision-queue-stophook-and-respawn-branch-fix.md
---

# Hunt record — decision-queue-stophook-and-respawn-branch-fix

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — decision-queue-stopgate.sh's comment claims its checkout-resolution is "the same way directive.sh does", but the pasted `_checkout_resolve()` silently drops directive.sh's self-clone fallback, so the two copies already diverge on day one and nothing keeps the three pasted copies (directive.sh, self-update.sh, decision-queue-stopgate.sh) in sync going forward.
Kind: design-error
Seed: on-the-record/hooks/decision-queue-stopgate.sh (new), on-the-record/hooks/directive.sh, on-the-record/hooks/self-update.sh, on-the-record/hooks/hooks.json
cap_seconds: 180
tier: default
diff_stat_lines: 460 lines / 6 files
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:35:00Z

### Reproduce
`on-the-record/hooks/decision-queue-stopgate.sh` line 15 says (comment):
"Resolves the on-the-record checkout the same way directive.sh does."

Diff the two `_checkout_resolve()` bodies:
```
cd on-the-record/hooks
diff <(sed -n '/_checkout_resolve/,/^}/p' directive.sh) \
     <(sed -n '/_checkout_resolve/,/^}/p' decision-queue-stopgate.sh)
```
Output shows decision-queue-stopgate.sh's version is missing the `mkdir -p .../own && git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own"` fallback block that directive.sh has.

Confirmed behaviorally: extracted each file's `_checkout_resolve()` verbatim and ran it in an isolated dir tree with none of TOKENMAXXXER_CHECKOUT / 4-ancestor-walk / marketplace path / own path / old path present, with a stubbed `git` on PATH that just logs invocations instead of hitting the network (see /tmp scratchpad `run_resolve.sh`):

- directive.sh's `_checkout_resolve`: attempts `git clone -q https://github.com/tokenmaxxxer/on-the-record.git <own-path>` (logged the clone invocation) before giving up.
- decision-queue-stopgate.sh's `_checkout_resolve`: returns 1 immediately, no clone attempt logged at all.

### Observed
In an environment where the checkout can only be found by self-cloning (fresh machine, no dev override, no existing on-the-record checkout in any of the fixed lookup paths), `directive.sh` would clone it and continue; `decision-queue-stopgate.sh` returns rc=1 from `_checkout_resolve`, hits `[ -n "$CHECKOUT" ] || { trap - EXIT; exit 0; }` and silently exits 0 with no output — the Stop hook never even attempts to call `spawn.py flows --json`, so an aged decision-queue item is never surfaced, and nothing distinguishes this from "queue was empty."

### Expected
Either the comment should not claim parity it doesn't have, or (since a Stop hook running "no clone attempted, checkout not found this turn" is arguably the correct/safer choice — self-cloning from a Stop hook mid-session has its own risks) the three independent pasted copies of the ~20-line lookup logic should share one source so that when the lookup order/paths are fixed in one copy (e.g. directive.sh already carries house-style comments about specific bugs like the plugin-root/../.. dead path), the other two do not silently keep stale logic. As written, nothing in the repo enforces the three stay in sync, and the new copy already ships with an unstated behavioral gap from the file it claims to match.
