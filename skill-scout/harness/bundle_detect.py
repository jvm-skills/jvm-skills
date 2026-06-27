#!/usr/bin/env python3
"""Detect skill BUNDLES — cohesive sets of dependent skills (e.g. a numbered pipeline
01-spec -> 06-execute) that should be evaluated and listed as ONE unit, not per step.

Usage: bundle_detect.py <scout.json> <out_bundles.json>

Signal: >=2 SKILL.md whose skill-dir name is numbered (^\\d{1,2}[-_]) inside the same repo
skills-root = a bundle candidate. The same pipeline is often copied across an author's repos
(sdd-demo, sdd-workshop, agentskills) and across .claude/.agents/.junie roots, frequently as
PARTIAL copies — so candidates are clustered per author by member-name OVERLAP (>=2 shared
steps), the most-complete non-demo copy is the canonical, the rest are recorded as copies.

Output: {"candidates":[ {login,repo,root,stars,members:[{skill,path}],signature:[skill...],
                         copies:[{repo,root,stars,members:[{skill,path}]}] } ]}
The LLM bundle-eval reads each canonical, decides cohesive/kind/status, and claims member skills;
the workflow then suppresses those member paths (canonical + copies) from the per-file results.
"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skilldedup import DEMO_RX

SCOUT, OUT = sys.argv[1], sys.argv[2]
scout = json.load(open(SCOUT))
NUM_RE = re.compile(r"^\d{1,2}[-_]")


def split_member(path):
    """A bundle member is a dir-based SKILL.md: <root>/<skill>/SKILL.md (root '' = repo root)."""
    parts = path.split("/")
    if parts[-1].lower() != "skill.md" or len(parts) < 2:
        return None
    return "/".join(parts[:-2]), parts[-2]   # (root, skill)


# 1) gather dir-based SKILL.md members per (login, repo, root)
groups = {}
for login, sc in scout.get("scans", {}).items():
    for h in sc.get("hits", []):
        repo, stars = h["repo"], int(h.get("stars", 0) or 0)
        for p in h.get("paths", []):
            sm = split_member(p)
            if not sm:
                continue
            root, skill = sm
            g = groups.setdefault((login, repo, root),
                                  {"login": login, "repo": repo, "root": root, "stars": stars, "members": {}})
            g["members"][skill] = p

# 2) a group with >=2 NUMBERED members is a raw bundle candidate (numbered members only)
raw = []
for g in groups.values():
    numbered = {s: p for s, p in g["members"].items() if NUM_RE.match(s)}
    if len(numbered) >= 2:
        raw.append({"login": g["login"], "repo": g["repo"], "root": g["root"], "stars": g["stars"],
                    "members": [{"skill": s, "path": p} for s, p in sorted(numbered.items())],
                    "signature": sorted(numbered.keys())})

# 3) cluster per author by member-name overlap (>=2 shared steps), canonical = most members,
#    then non-demo repo, then most stars; the rest become `copies`.
def rank(c):
    return (-len(c["members"]), bool(DEMO_RX.search(c["repo"])), -int(c["stars"] or 0), c["repo"], c["root"])

by_login = {}
for c in raw:
    by_login.setdefault(c["login"], []).append(c)

candidates = []
for login, cands in by_login.items():
    clusters = []  # each: {"names":set, "items":[cand]}
    for c in sorted(cands, key=rank):
        names = set(c["signature"])
        for cl in clusters:
            if len(names & cl["names"]) >= 2:
                cl["items"].append(c); cl["names"] |= names; break
        else:
            clusters.append({"names": set(names), "items": [c]})
    for cl in clusters:
        items = sorted(cl["items"], key=rank)
        canon = dict(items[0])
        canon["copies"] = [{"repo": x["repo"], "root": x["root"], "stars": x["stars"], "members": x["members"]}
                           for x in items[1:]]
        candidates.append(canon)

json.dump({"candidates": candidates}, open(OUT, "w"), indent=2)
print(f"bundles: {len(candidates)} candidate(s) from {len(raw)} raw group(s)")
for c in candidates:
    print(f"  {c['login']}/{c['repo']} :: {c['root'] or '<root>'}  "
          f"({len(c['members'])} steps, {len(c['copies'])} copies)  steps={c['signature']}")
