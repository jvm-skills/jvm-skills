#!/usr/bin/env python3
"""Deterministically assemble a conf.json for apply.py from on-disk judge verdicts + a SMALL overlay.

Why this exists: the Apply step used to ask an agent to inline-write the full conf.json (skills[] +
rejected[], each with reasoning text). For large conferences that JSON is 100k+ tokens, which blew the
agent's 32k output-token cap and silently dropped the conference (jax / devoxxfrance / digitalcraftsday,
batch 1). The heavy arrays are fully reconstructable from <slug>_verdicts_*.json, so the agent now only
emits a tiny overlay and this script builds the rest — no per-conf size limit.

Usage: build_conf.py <slug> <overlay.json> <out_conf.json>

overlay.json (small, written by the apply agent):
  {
    "conference": "JAX 2026", "url": "...", "today": "2026-06-27", "roster_fetched_at": "2026-06-27",
    "drops": { "login|repo|path": "<opus recheck reason>", ... },   # promotions Opus rechecked-out (optional)
    "bundle_verdicts": { "repo|root": {...}, ... },                  # cohesive-bundle verdicts (optional)
    "run_notes": "..."                                              # optional; auto-generated if absent
  }
"""
import json, glob, os, sys

H = os.path.dirname(os.path.abspath(__file__))
slug, overlay_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
ov = json.load(open(overlay_path))
drops = ov.get("drops", {}) or {}
today = ov["today"]

# 1) gather every judge verdict for this conference (batches cover disjoint ranges; dedup defensively)
verdicts = []
for f in sorted(glob.glob(os.path.join(H, f"{slug}_verdicts_*.json"))):
    try:
        verdicts += json.load(open(f)).get("verdicts", [])
    except Exception as e:
        print(f"  warn: {os.path.basename(f)}: {e}", file=sys.stderr)

seen, skills, rejected = set(), [], []
for v in verdicts:
    key = (v.get("login"), v.get("repo"), v.get("path"))
    if None in key or key in seen:
        continue
    seen.add(key)
    dk = f"{v['login']}|{v['repo']}|{v['path']}"
    promoted = v.get("status") in ("found", "needs_review")
    if promoted and dk not in drops:
        skills.append({"login": v["login"], "repo": v["repo"], "path": v["path"], "status": v["status"],
                       "depth": v.get("depth", 0), "jvm_fit": v.get("jvm_fit", ""), "category": v.get("category", ""),
                       "lines": v.get("lines", 0), "notes": v.get("notes", ""), "reasoning": v.get("reasoning", "")})
    elif promoted:  # Opus recheck dropped this promotion -> rejected with the recheck rationale
        rejected.append({"login": v["login"], "repo": v["repo"], "path": v["path"], "reason": "review",
                         "reasoning": f"Opus recheck rejected promotion: {drops[dk]}. (judge: {v.get('reasoning','')})"})
    else:
        rejected.append({"login": v["login"], "repo": v["repo"], "path": v["path"],
                         "reason": v.get("reason", "review"), "reasoning": v.get("reasoning", "")})

nf = sum(1 for s in skills if s["status"] == "found")
nr = len(skills) - nf
nb = sum(1 for x in (ov.get("bundle_verdicts", {}) or {}).values()
         if x.get("cohesive") and x.get("status") in ("found", "needs_review"))
conf = {
    "conference": ov["conference"], "url": ov.get("url", ""),
    "roster_fetched_at": ov.get("roster_fetched_at", today), "today": today,
    "scout": os.path.join(H, f"{slug}_scout.json"),
    "skills": skills, "rejected": rejected,
    "bundle_detect": os.path.join(H, f"{slug}_bundles.json"),
    "bundle_verdicts": ov.get("bundle_verdicts", {}) or {},
    "run_notes": ov.get("run_notes") or f"{nf} found, {nr} needs_review, {nb} bundle(s), {len(rejected)} rejected.",
}
json.dump(conf, open(out_path, "w"))
print(f"{slug}: built {os.path.basename(out_path)}  skills={len(skills)} (found={nf} nr={nr}) "
      f"rejected={len(rejected)} bundles={nb} drops={len(drops)}")
