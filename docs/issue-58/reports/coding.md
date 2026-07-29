# Coding record — issue-58

loop_state: landed

## What was done
Executed the approved phase-1 proposal (`docs/issue-58/proposals/coding.md`)
by extending the issue-38 `allowedDomains` merge mechanism in
`role_settings()` so every sandboxed role also gets web-access domains,
per the operator's "option B: all roles" decision:

- `spawn.py`: added module-level constant `WEB_ACCESS_DOMAINS = ["*"]`
  right after `PACKAGE_CACHE_DIRS`. Extended the existing merge block at
  `spawn.py:344-352` (previously only looped `PACKAGE_REGISTRY_HOSTS`)
  with a second, identically-shaped additive/dedup-safe loop over
  `WEB_ACCESS_DOMAINS` — same block, not a new merge site.
  `PACKAGE_REGISTRY_HOSTS`, `PACKAGE_CACHE_DIRS`, and `go_proxy_layer()`
  are unchanged.
- `README.md`: added a "Web-access allowlist (issue #58)" section
  immediately after "Package-registry access (issue #38)", mirroring its
  structure (mechanism paragraph, then an explicit "Trade-off, explicit:"
  paragraph naming the prompt-injection risk and muster's human gate
  chain — phase-1 proposal → human Approve → PR diff review → human merge
  — as the compensating control; no technical content filter added).
- `test_spawn.py`: added
  `PackageRegistryAccess.test_web_access_domain_merged_alongside_registry_hosts`,
  asserting `spawn.WEB_ACCESS_DOMAINS` entries, the role-declared domains
  from `roles/coding.json`, and `PACKAGE_REGISTRY_HOSTS` are all present
  together in the merged `allowedDomains` for the `coding` role.

## Why
Upstream basis: issue #58 requirement + approved proposal
`docs/issue-58/proposals/coding.md` + phase-1 survey
`docs/issue-58/reports/coding/survey.md`. Every role's sandbox allowlist
covered only 3 hosts plus registry hosts, silently denying `WebSearch`/
`WebFetch` for all roles (measured symptom: issue #43, 3/6 survey targets
unverified). The operator picked option B (all roles, not per-role
opt-in), and the proposal named the same merge site as issue-38's fix,
extended rather than duplicated.

### Schema open question, resolved
The phase-1 survey left open whether Claude Code's sandbox schema accepts
a literal `"*"` in `allowedDomains`. No schema file exists in this repo,
and `WebSearch` tool access was denied in this session, so the check was
done directly against the installed Claude Code CLI binary:
`/home/jwjung/.local/bin/claude -> .../versions/2.1.220`. Extracting the
domain-matcher function used at the sandbox's actual request-decision
site:

```js
function Kat(e,t){let r=e.toLowerCase();if(t==="*")return!0;
  if(t.startsWith("*.")){...}
  return r===t.toLowerCase()}
```

`t==="*"` returns `true` unconditionally, so a literal `"*"` entry in
`allowedDomains` matches every host at the layer the sandbox runtime
actually enforces. This confirms the proposal's candidate value directly
from the enforcing code path (stronger evidence than a doc search would
give), so `WEB_ACCESS_DOMAINS = ["*"]` was used as-is — no fallback to an
explicit host-list was needed. (Per the phase-1 survey's own reasoning, a
fixed list would not fit anyway: WebFetch/WebSearch targets are not
enumerable in advance.)

## What did not work
Nothing was reverted. One deviation from the phase-1 plan: `WebSearch`
tool verification of the schema value (as originally planned) was
unavailable in this session (tool permission denied), so verification
switched to direct inspection of the installed CLI binary's compiled JS
instead.

## Verification
```
$ python3 -m pytest test_spawn.py -q
.............................................                            [100%]
45 passed in 0.32s
```
45/45 pass, including the new
`test_web_access_domain_merged_alongside_registry_hosts` and all
pre-existing issue-38 `PackageRegistryAccess` cases (unaffected).

## Closed checks
- closed_checks: web-access-domain-merged (verified via
  `role_settings("coding")` output — `WEB_ACCESS_DOMAINS`,
  `PACKAGE_REGISTRY_HOSTS`, and role-declared domains all present in
  merged `allowedDomains`, none deduped away).
- closed_checks: no-scope-creep (diff touches only `spawn.py`,
  `README.md`, `test_spawn.py`, this record file — `spawn_cmd`/config
  paths untouched, out of scope per issue #60).

## Hunt
warrant-hunter not dispatched: change is a same-shape extension of an
already-landed, already-tested merge block (issue #38), with an added
test asserting the merge is additive and non-destructive — the change
surface is small and directly covered by the new test plus the full
existing suite.

## Open findings
None.
