# Reconciled spec index

Issue #336: several repos build against this engine's spec, but no
document lists or hashes the others, so contradictions between
documents survive indefinitely. This file is the single reconciled
reading — every spec-shaped document, its recorded content hash, and
(below) the ambiguities already found and resolved.

`gates/spec_index.py` recomputes each listed file's SHA256 and fails
when it no longer matches what's recorded here. Regenerate with
`python3 gates/spec_index.py --update` after reading what changed and
updating "Resolved ambiguities" if the edit touches a resolved point.

## Tracked documents

| path | sha256 |
| --- | --- |
| `protocol.md` | `de8db1cbe6e95856ff36639e9d84ccd5606cce291f13303e11258db4f7f29e24` |
| `protocol.ko.md` | `f539ac81d281df7c66933720d9c20cca107d32cde39fcc8b09dfaafeeb885ad7` |
| `README.md` | `9b76bea1a2fae899bf7632c47139bbcd1ab2ba35ebc1d0eb29eb1338d7f6205a` |
| `README.ko.md` | `dcf2c9d28a6c1058eb0950a5fc0a15c2883d95da081d65e0531cdac168873f16` |
| `docs/specs/approvers.md` | `bbcb4e239a5aed872956a01acc04c9431027a1f2df483b53265f72577ba16ab9` |
| `docs/specs/flows-schema.md` | `1a5bbd9cc1c3f75785c74a9c4276ecca8aef243d60acb1b39a369d124588d038` |
| `docs/handbooks/on-the-record.md` | `21dbff37005e7601c201fc626fb39cbac8c3055190b64867df3dfb6db7880fbe` |
| `docs/handbooks/operations.md` | `7424add4f836f0d6ef1f22c7ccd839575bdc352927d6beaa40241dda99de296f` |
| `docs/handbooks/setup.md` | `df9c710683663f260679d3629ce8733c7f0af60196dbfbaf6b92d8e2205f3e73` |
| `on-the-record/commands/run.md` | `6fa8d3285877d0b850a4d51203693106b10515b7b78e43885fb513bf670983b0` |

## Resolved ambiguities

- **Ledger storage location.** Canonical storage is `runs/ledger.jsonl`
  (per `docs/handbooks/operations.md:159,405`,
  `docs/specs/flows-schema.md:243-252`, and
  `on-the-record/commands/run.md:340`, all of which agree).
  `ledger/collect.py` (repo-root script) is an aggregator that *reads*
  `runs/ledger.jsonl` — it is not itself the storage location.
  `docs/handbooks/on-the-record.md`'s architecture diagram previously
  labeled `ledger/` as "the scorecard" without naming it as an
  aggregator, which read as if `ledger/` were the storage; corrected in
  this change (both the Korean and English diagram lines) to name it as
  the aggregator over `runs/ledger.jsonl`. `protocol.md` does not
  mention the ledger at all and is not in contradiction with the above —
  it is simply silent on this topic.
