# Survey conventions

## Capability and contract claims are repo-scoped

A survey or record that states a capability, contract, or feature is
absent must name the repository and commit checked. "Not present in
`<repo>` as of `<sha>`" is a defensible claim; "absent" with no
repository/commit anchor is not — the author may have checked only one
clone of a multi-repo system (issue #415: `thaki-agent-security-console`
had already implemented, in a sibling repository, eight surfaces a
session concluded were absent).

`gates/repo_scope.py::check_repo_scope` mechanically flags an unscoped
capability/contract absence sentence. It does not verify the claim's
truth or that the right repository was checked — only that a scope
statement is present (issue #358's own evidence-adjacency-not-adequacy
ceiling, reused here).
