# Record authoring

Authoring a role record used to cost one model turn per gate refusal:
`record_enums`, `record_wellformed`, the four checks
`record-claim-guard.sh` mirrored inline, and the rest of `gates.py`'s
record checks each reported only their own first failure (issue #517 —
a 7-refusal loop was observed on issue-512 phase 2).

## Run `record_lint` before writing the record

```
python3 -m gates.record_lint <path/to/docs/issue-N/reports/role.md>
```

Prints every violation in the file — enum drift, malformed frontmatter,
tool-tag residue, bare count claims, unverifiable escapes with no
reason, orphaned path references, missing `## Acceptance verification`
on a terminal record — in one pass, not one-at-a-time. Exit code is
non-zero if any violation exists.

Run against a whole repo (or with no argument, the current directory)
to sweep every `docs/issue-*/reports/*.md` record it finds:

```
python3 -m gates.record_lint
```

A repo with no records prints an explicit "no records" line and exits
0.

`record_lint.lint_record(path) -> list[str]` is also importable — the
hooks (`record-claim-guard.sh`) and `gates/ci.py` call the same
functions this module aggregates, so there is exactly one place each
rule's logic lives.

## Scaffold a new record

```
on-the-record/hooks/record-scaffold.sh <role> <issue-n> [target-repo-root]
```

Writes `docs/issue-<n>/reports/<role>.md` with every field
`roles/<role>.json`'s `record_fields` declares present as a
`PLACEHOLDER: <field>` token, plus the standard section skeleton
(Summary of work, Why, What did not work, Open findings, Next steps,
Resolution path). `record_lint` treats a surviving placeholder as a
violation — run it after filling the skeleton in to confirm nothing
was missed. Refuses to overwrite an existing record. This is a CLI
command, not a `PreToolUse` hook — nothing in the write path fires
"author is about to start a record," so there is no lifecycle event to
register it against in `hooks.json`.
