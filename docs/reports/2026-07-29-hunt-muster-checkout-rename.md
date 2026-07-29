---
proposal: docs/issue-87/proposals/coding.md
---

# Hunt record — muster-checkout-rename

## after-proposal — stance 1: env-override contract break for existing users

Verdict: FINDING — the old `TOKENMAXXXER_MUSTER` env override is silently ignored after the rename, with no back-compat shim (unlike the filesystem path, which does keep an old-path fallback), so a dev/CI relying on it silently falls through to a fresh `git clone` every session instead of using their pinned checkout.
Kind: composition
Seed: rename of `_muster_resolve`→`_checkout_resolve` / `TOKENMAXXXER_MUSTER`→`TOKENMAXXXER_CHECKOUT` in on-the-record/hooks/directive.sh and on-the-record/hooks/self-update.sh, with a new-path/old-path filesystem fallback but no equivalent env-var fallback.

### Reproduce
Extracted `_checkout_resolve()` verbatim from `on-the-record/hooks/directive.sh` (post-rename) into a throwaway script, with `HOME` pointed at an empty fake dir (so no marketplace/own/old paths exist on the probe host) and the *old* env var name exported instead of the new one:

```bash
export HOME=/tmp/fakehome; mkdir -p "$HOME"
export TOKENMAXXXER_MUSTER=/tmp/fakecheckout   # old name, still what a pre-rename dev has in their shell profile
# ... _checkout_resolve() body copied verbatim from directive.sh ...
CHECKOUT="$(_checkout_resolve || true)"
echo "RESOLVED=[$CHECKOUT]"
```

Run it.

### Observed
```
WOULD_CLONE
RESOLVED=[] (env var carrying old name was set but ignored -> falls to clone)
```
The function never even looks at `TOKENMAXXXER_MUSTER`; it falls straight through every other probe and attempts a live `git clone`, with zero message telling the user their override was dropped.

### Expected
Either the rename should not be user-facing without a deprecation shim (accept the old env var name with a one-line stderr notice, mirroring the filesystem old-path fallback the same commit added), or the commit/report should flag this as a breaking change for anyone with `TOKENMAXXXER_MUSTER` already exported (shell profile, CI env, docs). Currently it is a plain silent behavior change: the same shell state that worked before the rename now produces different, unannounced behavior (re-clone instead of using the pinned checkout).
