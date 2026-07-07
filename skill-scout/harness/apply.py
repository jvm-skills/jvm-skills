#!/usr/bin/env python3
"""Upsert a scout run into db/*.csv by natural key (idempotent, RFC-4180 quoted).
Usage: apply.py <conf.json>
conf.json = {
  "conference": "jPrime 2026", "url": "https://jprime.io/speakers",
  "roster_fetched_at": "2026-06-26", "today": "2026-06-26",
  "scout": "<path to scout output json>",
  "skills": [ {login,repo,path,status,depth,jvm_fit,category,lines,notes} ... ],  # one per evaluated hit
  "run_notes": "..."
}
Derives speakers/resolutions/repos from the scout json; skills come from the eval overlay.
Pass --dry to print the diff without writing.
"""
import json, csv, os, sys, datetime, io

# Portable: resolve db/ relative to this script, with an env override for CI / non-standard layouts.
_HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("SKILL_SCOUT_DB") or os.path.join(_HERE, "..", "db")
DRY = "--dry" in sys.argv
CHECKPOINT = "--checkpoint" in sys.argv  # write only speakers/speaker_conferences/resolutions for cross-conf dedup; skip stamp/skills/rejected/ledger
cfg = json.load(open([a for a in sys.argv[1:] if not a.startswith("-")][0]))
scout = json.load(open(cfg["scout"]))
TODAY = cfg["today"]
RECHECK = (datetime.date.fromisoformat(TODAY) + datetime.timedelta(days=90)).isoformat()
CONF = cfg["conference"]

COLS = {
  "conferences.csv": ["name","url","roster_fetched_at"],
  "speakers.csv": ["name","norm_name","affiliation"],
  "speaker_conferences.csv": ["norm_name","conference"],
  "resolutions.csv": ["norm_name","github_login","confidence","gh_name","gh_company","followers","method","resolved_at","recheck_after"],
  "repos.csv": ["login","name","is_fork","stars","pushed_at","head_sha","last_scanned_at"],
  "skill_files.csv": ["login","repo","path","status","depth","jvm_fit","category","lines","notes","reasoning","first_seen","last_seen"],
  "rejected.csv": ["login","repo","path","reason","reasoning","first_seen","last_seen"],
  "bundles.csv": ["login","repo","root","name","kind","status","depth","members","copies","reasoning","first_seen","last_seen"],
}
KEY = {
  "conferences.csv": ("name",), "speakers.csv": ("norm_name",),
  "speaker_conferences.csv": ("norm_name","conference"), "resolutions.csv": ("norm_name",),
  "repos.csv": ("login","name"), "skill_files.csv": ("login","repo","path"),
  "rejected.csv": ("login","repo","path"), "bundles.csv": ("login","repo","root"),
}

def load(name):
    p = os.path.join(DB, name)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []
def keyof(name, row): return tuple(row[k] for k in KEY[name])

changes = {}
def upsert(name, row, preserve_first_seen=False):
    rows = changes.setdefault(name, load(name))
    idx = {keyof(name, r): i for i, r in enumerate(rows)}
    k = keyof(name, row)
    if k in idx:
        existing = rows[idx[k]]
        if preserve_first_seen and existing.get("first_seen"):
            row["first_seen"] = existing["first_seen"]
        rows[idx[k]] = row
        return "update"
    rows.append(row); return "insert"

log = []
# 1) conference (skip under --checkpoint — don't stamp roster_fetched_at until eval + final apply)
if not CHECKPOINT:
    log.append(("conferences.csv", upsert("conferences.csv",
        {"name":CONF,"url":cfg["url"],"roster_fetched_at":cfg["roster_fetched_at"]})))

# 2/3/4) per speaker
for r in scout["resolutions"]:
    nn = r["norm_name"]
    log.append(("speakers.csv", upsert("speakers.csv",
        {"name":r["name"],"norm_name":nn,"affiliation":r["aff"]})))
    log.append(("speaker_conferences.csv", upsert("speaker_conferences.csv",
        {"norm_name":nn,"conference":CONF})))
    if r.get("reused"):  # don't overwrite an existing resolution
        continue
    conf = r["confidence"]
    log.append(("resolutions.csv", upsert("resolutions.csv",
        {"norm_name":nn,"github_login":r["login"],"confidence":conf,
         "gh_name":r["gh_name"],"gh_company":r["gh_company"],
         "followers":str(r["followers"]) if r["login"] else "",
         "method":r["method"],"resolved_at":TODAY,
         "recheck_after":"" if conf=="HIGH" else RECHECK})))

# 5) repos — any repo that has >=1 written skill_file row
repo_meta = {}  # (login,repo) -> {stars,pushed_at,head_sha}
for login, s in scout["scans"].items():
    for h in s["hits"]:
        repo_meta[(login, h["repo"])] = {"stars":h["stars"],"pushed_at":h["pushed_at"],"head_sha":h["head_sha"]}
# ---- bundles: assemble from bundle_detect candidates + the LLM bundle verdicts (keyed "repo|root") ----
# A cohesive bundle becomes ONE canonical row and CLAIMS all its member paths (canonical + copies) so
# they are never individually listed/rejected. A non-cohesive numbered group is released to rejected.
bundle_rows, claimed, bundle_rejected = [], set(), []
if not CHECKPOINT and cfg.get("bundle_detect") and os.path.exists(cfg["bundle_detect"]):
    verdicts = cfg.get("bundle_verdicts", {})
    for c in json.load(open(cfg["bundle_detect"])).get("candidates", []):
        v = verdicts.get(f'{c["repo"]}|{c["root"]}') or {}
        all_paths = [(c["login"], c["repo"], m["path"]) for m in c["members"]]
        for cp in c.get("copies", []):
            all_paths += [(c["login"], cp["repo"], m["path"]) for m in cp["members"]]
        if v.get("cohesive"):
            claimed.update(all_paths)
            bundle_rows.append({"login":c["login"],"repo":c["repo"],"root":c["root"],
                "name":v.get("name") or "-","kind":v.get("kind",""),"status":v.get("status",""),
                "depth":str(v.get("depth",0)),"members":";".join(m["skill"] for m in c["members"]),
                "copies":";".join(sorted({cp["repo"] for cp in c.get("copies",[])})),
                "reasoning":v.get("reasoning","")})
        else:  # not a cohesive bundle -> members fall back to individual rejected rows
            for (lg, rp, pa) in all_paths:
                bundle_rejected.append({"login":lg,"repo":rp,"path":pa,"reason":v.get("reason","review"),
                    "reasoning":v.get("reasoning","numbered group judged not a cohesive bundle")})

repos_to_write = {(s["login"], s["repo"]) for s in cfg["skills"]} | {(b["login"], b["repo"]) for b in bundle_rows}
for (login, repo) in sorted(repos_to_write):
    m = repo_meta.get((login, repo), {"stars":0,"pushed_at":"","head_sha":""})
    log.append(("repos.csv", upsert("repos.csv",
        {"login":login,"name":repo,"is_fork":"0","stars":str(m["stars"]),
         "pushed_at":m["pushed_at"],"head_sha":m["head_sha"],"last_scanned_at":TODAY})))

# 6) skill_files
for s in cfg["skills"]:
    log.append(("skill_files.csv", upsert("skill_files.csv",
        {"login":s["login"],"repo":s["repo"],"path":s["path"],"status":s["status"],
         "depth":str(s["depth"]),"jvm_fit":str(s["jvm_fit"]),"category":s["category"],
         "lines":str(s["lines"]),"notes":s.get("notes",""),"reasoning":s.get("reasoning",""),
         "first_seen":TODAY,"last_seen":TODAY}, preserve_first_seen=True)))

# 6a) bundles.csv — cohesive dependent skill-sets, one canonical row each (copies recorded inline).
for b in bundle_rows:
    log.append(("bundles.csv", upsert("bundles.csv",
        {**b, "first_seen":TODAY, "last_seen":TODAY}, preserve_first_seen=True)))

# 6b) rejected.csv — every scanned hit NOT promoted (no silent drops). Prefer the LLM's per-row
#     verdict (cfg["rejected"] + released non-cohesive bundle members); fall back to classify.py.
#     Member paths of a COHESIVE bundle are claimed by it and never rejected here.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify import classify
kept = {(s["login"], s["repo"], s["path"]) for s in cfg["skills"]}
overlay = {(r["login"], r["repo"], r["path"]): (r["reason"], r.get("reasoning", ""))
           for r in (cfg.get("rejected", []) + bundle_rejected)}
for login, s in ({} if CHECKPOINT else scout.get("scans", {})).items():  # no rejected rows under --checkpoint
    for h in s.get("hits", []):
        for path in h["paths"]:
            if (login, h["repo"], path) in kept or (login, h["repo"], path) in claimed:
                continue
            if (login, h["repo"], path) in overlay:
                reason, reasoning = overlay[(login, h["repo"], path)]
            else:
                reason, reasoning = classify(login, h["repo"], path)
            log.append(("rejected.csv", upsert("rejected.csv",
                {"login":login,"repo":h["repo"],"path":path,"reason":reason,
                 "reasoning":reasoning,"first_seen":TODAY,"last_seen":TODAY}, preserve_first_seen=True)))

# 7) runs ledger (append)
nres = sum(1 for r in scout["resolutions"] if r["confidence"]=="HIGH")
scanned = sum(s["scanned_repos"] for s in scout["scans"].values())
found = sum(1 for s in cfg["skills"] if s["status"]=="found")
parked = sum(1 for r in scout["resolutions"] if r["confidence"] in ("MED","UNRESOLVED"))
if not CHECKPOINT:  # no ledger row for a checkpoint write
    runs = changes.setdefault("runs.csv", load("runs.csv"))
    runs.append({"started_at":TODAY,"conference":CONF,"speakers":str(len(scout["resolutions"])),
        "resolved":str(nres),"scanned_repos":str(scanned),"skipped_repos":"0",
        "found":str(found),"parked":str(parked),"notes":cfg.get("run_notes","")})

# write
def render(name, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS[name], lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    for r in rows: w.writerow({c: r.get(c,"") for c in COLS[name]})
    return buf.getvalue()

print(f"=== apply: {CONF} (today={TODAY}, dry={DRY}) ===")
from collections import Counter
for name in COLS:
    c = Counter(act for n, act in log if n == name)
    if c: print(f"  {name:<26} {dict(c)}")
if not CHECKPOINT: print(f"  runs.csv                   append 1 row")
for name, rows in changes.items():
    if name == "runs.csv":
        cols = ["started_at","conference","speakers","resolved","scanned_repos","skipped_repos","found","parked","notes"]
        buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows: w.writerow({c: r.get(c,"") for c in cols})
        content = buf.getvalue()
    else:
        content = render(name, rows)
    if DRY:
        print(f"\n----- {name} -----\n{content}")
    else:
        open(os.path.join(DB, name), "w").write(content)
if not DRY:
    print("\nWROTE all files.")
    # self-validate: re-parse every db file, check column counts + duplicate natural keys
    ok = True
    for name in list(COLS) + ["runs.csv"]:
        rows = list(csv.DictReader(open(os.path.join(DB, name))))
        ncols = len(rows[0]) if rows else 0
        ragged = [i for i, r in enumerate(rows) if len(r) != ncols or any(v is None for v in r.values())]
        dup = []
        if name in KEY:
            s = set()
            for r in rows:
                k = keyof(name, r)
                if k in s: dup.append(k)
                s.add(k)
        status = "ok" if not ragged and not dup else "FAIL"
        if status == "FAIL": ok = False
        print(f"  validate {name:<24} rows={len(rows):<4} {status}"
              + (f" ragged={ragged}" if ragged else "") + (f" dup={dup}" if dup else ""))
    print("VALIDATION", "PASS" if ok else "FAIL")
