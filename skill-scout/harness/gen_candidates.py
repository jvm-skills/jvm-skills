#!/usr/bin/env python3
"""Regenerate candidates.md as a human view of db/*.csv (system of record)."""
import csv, os
DB = "/Users/tschuehly/IdeaProjects/jvm-skills/skill-scout/db"
OUT = "/Users/tschuehly/IdeaProjects/jvm-skills/skill-scout/candidates.md"
def load(n): return list(csv.DictReader(open(os.path.join(DB, n))))
conf = load("conferences.csv"); spk = load("speakers.csv"); sc = load("speaker_conferences.csv")
res = load("resolutions.csv"); repos = load("repos.csv"); sf = load("skill_files.csv"); runs = load("runs.csv")
rej = load("rejected.csv") if os.path.exists(os.path.join(DB, "rejected.csv")) else []

res_by_login = {r["github_login"]: r for r in res if r["github_login"]}
res_by_norm = {r["norm_name"]: r for r in res}
name_by_norm = {s["norm_name"]: s["name"] for s in spk}
stars_by = {(r["login"], r["name"]): r["stars"] for r in repos}
confs_by_norm = {}
for r in sc: confs_by_norm.setdefault(r["norm_name"], []).append(r["conference"])

def gh_name(login): return res_by_login.get(login, {}).get("gh_name", login)
L = []
W = L.append
W("# Skill Candidates — generated from `db/*.csv`\n")
W("**Do not edit by hand** — regenerate with `gen_candidates.py` after each scout run. The CSVs in")
W("`db/` are the system of record; this is a read-only view. Loop: `speaker-scout-loop.md`.\n")
W(f"State: {len(conf)} conferences · {len(spk)} speakers · "
  f"{sum(1 for r in res if r['confidence']=='HIGH')} HIGH / "
  f"{sum(1 for r in res if r['confidence']=='MED')} MED / "
  f"{sum(1 for r in res if r['confidence']=='UNRESOLVED')} UNRESOLVED · "
  f"{sum(1 for s in sf if s['status']=='found')} skills found.\n")

W("## ✅ Found skills (created by speakers)\n")
W("| Skill | Repo | Author | Category | Depth | JVM | ★ | Why included (reasoning) |")
W("|---|---|---|---|---|---|---|---|")
for s in sorted([s for s in sf if s["status"] == "found"], key=lambda s: -int(stars_by.get((s["login"], s["repo"]) , 0) or 0)):
    star = stars_by.get((s["login"], s["repo"]), "?")
    skill = s["path"].split("/")[-2] if "/" in s["path"] else s["path"]
    W(f"| {skill} | `{s['login']}/{s['repo']}` | {gh_name(s['login'])} | {s['category']} | "
      f"{s['depth']} | {s['jvm_fit']} | {star} | {s.get('reasoning') or s['notes']} |")

needs = [s for s in sf if s["status"] == "needs_review"]
if needs:
    W("\n## 🟡 Needs review (borderline)\n")
    W("| Skill | Repo | Author | Why borderline (reasoning) |"); W("|---|---|---|---|")
    for s in needs:
        W(f"| {s['path']} | `{s['login']}/{s['repo']}` | {gh_name(s['login'])} | {s.get('reasoning') or s['notes']} |")

W("\n## ✋ Manual-confirm queue (MED — name match, not auto-accepted)\n")
W("| Speaker | GitHub | GH name | Company | Followers | Conference(s) |")
W("|---|---|---|---|---|---|")
for r in sorted([r for r in res if r["confidence"] == "MED"], key=lambda r: -int(r["followers"] or 0)):
    nm = r["norm_name"]
    W(f"| {name_by_norm.get(nm, nm)} | `{r['github_login']}` | {r['gh_name']} | {r['gh_company'].strip()} | "
      f"{r['followers']} | {', '.join(confs_by_norm.get(nm, []))} |")

W("\n## 📇 Parked — UNRESOLVED (recheck later)\n")
park = [r for r in res if r["confidence"] == "UNRESOLVED"]
W(", ".join(f"{name_by_norm.get(r['norm_name'], r['norm_name'])}" for r in park) or "_none_")

if rej:
    def rtab(reasons, title, blurb):
        sel = [r for r in rej if r["reason"] in reasons]
        if not sel: return
        W(f"\n## {title} ({len(sel)})\n"); W(blurb + "\n")
        W("| Skill | Repo | Author | Reason | Note |"); W("|---|---|---|---|---|")
        for r in sorted(sel, key=lambda r: (r["login"], r["repo"], r["path"])):
            skill = r["path"].split("/")[-2] if "/" in r["path"] else r["path"]
            W(f"| {skill} | `{r['login']}/{r['repo']}` | {gh_name(r['login'])} | {r['reason']} | {r['reasoning']} |")
    rtab({"off-topic-workflow", "off-topic-service", "off-topic-tech"},
         "♻️ Real but non-JVM skills (reviewable)",
         "Well-formed, reusable skills that are **not JVM-specific** — generic agent/dev workflow, "
         "external-service integrations, or non-JVM tech. Surfaced for review (e.g. a separate directory).")
    rtab({"jvm-collection"}, "🧩 JVM skills inside a found collection (promote-worthy)",
         "JVM skills that belong to an already-found collection but are not yet listed individually.")
    rtab({"vendored"}, "🔁 Vendored third-party skills (lead: scan the real author)",
         "JVM skills copied into a speaker's repo but authored by someone else — chase the original author.")
    rtab({"review"}, "🔍 Needs human classification (the promotion queue)",
         "Real SKILL.md files the auto-classifier could not judge JVM-vs-offtopic — read and promote the JVM ones.")
    from collections import Counter
    junk = Counter(r["reason"] for r in rej if r["reason"] in
                   {"boilerplate", "demo", "project-doc", "test-fixture", "already-listed"})
    if junk:
        W("\n## 🗑️ Filtered noise (counts only — see `db/rejected.csv`)\n")
        W(" · ".join(f"**{k}** {v}" for k, v in sorted(junk.items(), key=lambda x: -x[1])))

W("\n\n## 🏃 Run ledger\n")
W("| Date | Conference | Speakers | HIGH | Scanned | Found | Parked | Notes |")
W("|---|---|---|---|---|---|---|---|")
for r in runs:
    W(f"| {r['started_at']} | {r['conference']} | {r['speakers']} | {r['resolved']} | "
      f"{r['scanned_repos']} | {r['found']} | {r['parked']} | {r['notes']} |")

scanned_n = sum(1 for c in conf if c["roster_fetched_at"])
W(f"\n## 📅 Conferences ({scanned_n} scanned / {len(conf)-scanned_n} queued)\n")
for c in conf:
    st = f"scanned {c['roster_fetched_at']}" if c["roster_fetched_at"] else "queued"
    W(f"- {'✅' if c['roster_fetched_at'] else '⏳'} **{c['name']}** — {c['url']} ({st})")
W("")
open(OUT, "w").write("\n".join(L))
print(f"wrote {OUT} ({len(L)} lines)")
