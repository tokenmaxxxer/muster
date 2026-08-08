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
| `protocol.md` | `b3d92e9fa8e27ed34d027ffa961279c5b39c6cf7b865b00c67f74622c0ce3ee8` |
| `protocol.ko.md` | `03ba195003285a20d0d1d7df5d914ef68f122672d39a7dba042fb5f6c184433a` |
| `README.md` | `9b76bea1a2fae899bf7632c47139bbcd1ab2ba35ebc1d0eb29eb1338d7f6205a` |
| `README.ko.md` | `dcf2c9d28a6c1058eb0950a5fc0a15c2883d95da081d65e0531cdac168873f16` |
| `docs/specs/approvers.md` | `bbcb4e239a5aed872956a01acc04c9431027a1f2df483b53265f72577ba16ab9` |
| `docs/specs/flows-schema.md` | `cb19ed6d9b209733f0ad3b02ed7e0bb8c395c5bce9a28b3c563b1e3d64bc5623` |
| `docs/handbooks/on-the-record.md` | `9e314a347f6265950b2eedc791891e329255ee4adf9f6b5ffab5554f2e6e20f1` |
| `docs/handbooks/operations.md` | `c60d8e137f6b76a83c9a25a6ae014843693a13a984f6f3b4488cacee3c604379` |
| `docs/handbooks/setup.md` | `df9c710683663f260679d3629ce8733c7f0af60196dbfbaf6b92d8e2205f3e73` |
| `on-the-record/commands/run.md` | `32262bac5f219b0a39b62fda256c942a539535bfab6c91e7c3ffd0307ab9c957` |

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
