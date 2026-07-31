# Scout brief — issue-162 (role rename execution ①)

Mode: batched-sequential fallback (2 WebSearch calls in one turn, no parallel Agent fan-out — internal tooling migration, not product-shaped). Stages used: 1 sweep only; stopped at judge point 1 (saturation — narrow scope, no further round would change a build decision).

## Angles run
1. CLI deprecated-name error/alias patterns.
2. GitHub repo-rename redirect semantics.

## Findings (must-bes / patterns)
- **Alias-then-error is the industry default**, not silent passthrough: dbt raises a *warning* on the old flag first, escalating to an *error* later (progressive deprecation), rather than either silently aliasing forever or hard-failing immediately. Docker/Click-style CLIs keep an explicit `deprecated_aliases` mechanism rather than ad-hoc catch blocks. → adopt: old role name should fail loudly and name the new one, not silently alias — this repo has zero in-flight history under the old names yet (no role has executed under round-5 naming), so there is no deprecation grace period to protect; a hard, clear error is proportionate, not a bare alias.
- **Error messages should be specific and actionable** — name what went wrong and the fix, not just "invalid". → this repo's existing generic-role-not-found error already does this cheaply once `roles/*.json` is renamed (`role_settings()` at spawn.py:330-333 lists all known roles on miss) — worth confirming whether that fallback text is enough, or whether the 9 renamed roles need one explicit old→new line each for a faster fix without reading the list.
- **`git clone`/`fetch`/`push` against a renamed GitHub repo keep working via redirect indefinitely** (until the old name is reused), but **redirects do NOT cover GitHub Actions references**. → adopt: spawn.py's `git clone https://github.com/{repo}.git` call (rulebook_checkout) will keep working unpushed-code-wise even before `roles/*.json` is updated, i.e. the GH-side rename is not blocking for clone continuity — but this repo hardcodes repo names in `roles/*.json` and `.claude-plugin/marketplace.json` regardless, and those must still be updated per the issue's own instruction (redirect is a safety net, not a substitute — matches issue-160 proposal's existing language on this point).

## Gap line
Current state (issue-160 proposal, already merged) already specifies the rename mapping and the "redirect is a safety net not a substitute" stance — the gap this scout closes is only the *silent-alias vs. hard-error* decision, which round-1 left as "proposal in this issue judges." Verdict: hard error, no alias — no in-flight history to protect yet.

## Pattern adopted / skipped
- Adopt: hard, named error on old role names (no silent alias).
- Skip: progressive warn-then-error rollout — unnecessary here since nothing has run under the old-name files yet at Track A time; that staging exists for the previously-shipped 9 repos' rulebook clone, not for the role JSON lookup.

Sources:
- [Error Handling in CLI Tools: A Practical Pattern](https://medium.com/@czhoudev/error-handling-in-cli-tools-a-practical-pattern-thats-worked-for-me-6c658a9141a9)
- [dbt Deprecations](https://docs.getdbt.com/reference/deprecations)
- [Duration of Web Traffic Redirection After Renaming a GitHub Repository](https://github.com/orgs/community/discussions/110367)
- [Renaming a repository — GitHub Docs](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository)
