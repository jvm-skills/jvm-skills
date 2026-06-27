#!/usr/bin/env python3
"""Split a scout.json's skill-file hits into cheap-skip (heuristic; no value in reading) vs
judge (an LLM reads and reasons about every one). Usage: prefilter.py <conf>_scout.json
Writes <conf>_prefilter.json = {skip:[{login,repo,path,reason,reasoning}], judge:[{login,repo,path,stars}]}
and prints "judge=N skip=M -> <file>".

cheap-skip families add nothing when read: exact-duplicate boilerplate template sets (OpenSpec/SDD/iikit),
vendored 3rd-party plugins, and already-listed (EXCLUDE) repos. EVERYTHING else — demo, project-doc,
off-topic-*, review, jvm-collection, and every genuine SKILL.md — goes to the LLM judge.
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify import classify

CHEAP = {"boilerplate", "vendored", "already-listed"}
src = sys.argv[1]
scout = json.load(open(src))
# optional bundles.json (bundle_detect output): exclude bundle member paths from per-file judging —
# they are evaluated as a unit by the bundle-eval stage instead.
bundle_paths = set()
if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
    for c in json.load(open(sys.argv[2])).get("candidates", []):
        for m in c["members"]:
            bundle_paths.add((c["login"], c["repo"], m["path"]))
        for cp in c.get("copies", []):
            for m in cp["members"]:
                bundle_paths.add((c["login"], cp["repo"], m["path"]))
skip, judge = [], []
for login, s in scout.get("scans", {}).items():
    for h in s.get("hits", []):
        for path in h["paths"]:
            if (login, h["repo"], path) in bundle_paths:
                continue  # handled by bundle-eval
            reason, reasoning = classify(login, h["repo"], path)
            if reason in CHEAP or h.get("already_listed"):
                skip.append({"login": login, "repo": h["repo"], "path": path, "reason": reason, "reasoning": reasoning})
            else:
                judge.append({"login": login, "repo": h["repo"], "path": path, "stars": h.get("stars", 0)})

out = src[:-len("_scout.json")] + "_prefilter.json" if src.endswith("_scout.json") else src + ".prefilter.json"
json.dump({"skip": skip, "judge": judge}, open(out, "w"), indent=2)
print(f"judge={len(judge)} skip={len(skip)} -> {out}")
