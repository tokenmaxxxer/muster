---
proposal: docs/proposals/2026-07-27-remote-github-marketplace.md
---

# Hunt record — remote-github-marketplace

## after-proposal — stance 1: cancelling-pair with another plugin's rule

Verdict: FINDING — the proposal's own planned README wording claims `claude plugin update` pulls remote GitHub HEAD for the newly-listed rulebook plugins, directly cancelling this repo's own measured statement, in the same file, that `claude plugin update` cannot do that for these plugins.
Kind: composition
Seed: docs/proposals/2026-07-27-remote-github-marketplace.md ("What will be done" section, README.md/README.ko.md update instructions)

### Reproduce
```
grep -n "claude plugin update" docs/proposals/2026-07-27-remote-github-marketplace.md
grep -n "version.*string\|이미 최신\|already at the latest" README.md README.ko.md
sed -n '86,95p' README.md
```

### Observed
The proposal's "What will be done" section (line ~119) directs adding to README.md/README.ko.md:
"claude plugin update then pulls remote GitHub HEAD for those [rulebook plugins newly listed
in muster's marketplace]".

But README.md already carries, in the very same file, a measured finding (line 86-91) that
directly contradicts this: "`claude plugin update` compares the `version` *string* in
plugin.json, and every rulebook sits at 0.1.0 forever, so it answers 'already at the latest
version' however many commits behind the cache is. Measured 2026-07-27: clone 2018d54, cache
7107a49, and a gate fix merged minutes earlier was not what ran." README.md goes on to say the
*only* route that actually moves the cache is `spawn.py update [role]`, not `claude plugin
update`. Since every rulebook plugin listed in the marketplace this proposal is adding sits at
the same permanent `0.1.0` version (checked across all nine rulebooks' plugin.json), the
"pulls remote HEAD" claim applies to exactly the plugins for which the file's own prior
measurement says it does not.

### Expected
The proposal should not instruct adding a claim that `claude plugin update` refreshes these
plugins; per the file's own established measurement, only `spawn.py update <role>` moves the
cache for them. As written, landing the proposal produces a single README with a warning
telling readers `claude plugin update` is stale-by-design for rulebook plugins directly next
to new text telling the same readers that command "pulls remote GitHub HEAD" for those same
plugins — whichever a reader reads last is the one they will act on, and half of them will
silently run stale rulebook code while `claude plugin update` reports success.

## before-landing — stance 2: assume this guard goes silent when its own input is malformed — make it go silent

Verdict: FINDING — `_installed_sha` swallows a corrupted `installed_plugins.json` and returns `""`, so `rulebook_version` reports "설치본 없음" (nothing installed) identically for "genuinely nothing installed" and "install tracking file is corrupted" — the exact false-confidence this function's own docstring says it exists to prevent.
Kind: silent-failure
Seed: .claude-plugin/marketplace.json now lists 33 plugins with `{"source":"github","repo":...}`; README/protocol updated to say refresh goes through `spawn.py update <role>`, and `rulebook_version()`/`_installed_sha()` are the functions the new remote-install flow leans on to tell the operator "what actually ran" after a remote fetch/update.

### Reproduce
```
cd /home/jwjung/tokenmaxxxer/muster
mkdir -p /tmp/fakehome/.claude/plugins
printf '{ not valid json\n' > /tmp/fakehome/.claude/plugins/installed_plugins.json
python3 - <<'PYEOF'
import sys
sys.path.insert(0, "/home/jwjung/tokenmaxxxer/muster")
import spawn
spawn.Path.home = staticmethod(lambda: spawn.Path("/tmp/fakehome"))
print(spawn.rulebook_version("coding"))
PYEOF
```

### Observed
```
83a9399 (main) — 설치본 없음
```
(clone sha `83a9399` printed as if the rulebook were simply never fetched — the malformed `installed_plugins.json`, which actually has 9 real install entries elsewhere on a real machine, is silently treated the same as an empty/missing file.)

### Expected
`_installed_sha`/`rulebook_version` should distinguish "no plugins installed" from "install registry unreadable" — e.g. raise or surface the JSONDecodeError/OSError instead of catching it into the same `""` used for "not present", since the function's stated purpose is exactly to stop an operator from believing a rulebook fix is live when it isn't.
