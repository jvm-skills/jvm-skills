#!/usr/bin/env python3
"""Speaker-Scout v3: resolve + throttled tree-scan -> structured JSON for human eval.
Usage: scout.py <speakers.json> <out.json>
Reads db/speakers.csv + db/resolutions.csv for dedupe/reuse. Does NOT write the db.
"""
import json, subprocess, re, time, unicodedata, sys, csv, os

DB = "/Users/tschuehly/IdeaProjects/jvm-skills/skill-scout/db"
# Two modes:
#   scout.py <speakers.json> <out.json>          resolve roster + scan HIGH handles
#   scout.py --logins a,b,c <out.json>           scan only these logins (investigate-accepted MEDs)
_ARGS = sys.argv[1:]
LOGINS_MODE = None
if _ARGS and _ARGS[0] == "--logins":
    LOGINS_MODE = [x.strip() for x in _ARGS[1].split(",") if x.strip()]
    OUT = _ARGS[2]
    SPEAKERS = []
else:
    SPEAKERS_FILE, OUT = _ARGS[0], _ARGS[1]
    SPEAKERS = json.load(open(SPEAKERS_FILE))
STOP = {"ag","inc","the","team","group","labs","llc","gmbh","co","corp","ltd","sa","systems","it"}
SKILL_RE = re.compile(r"(^|/)(SKILL\.md|AGENTS\.md|CLAUDE\.md|\.cursorrules)$", re.I)

def norm(s):
    s = unicodedata.normalize("NFKD", s or ""); s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
def gh(args):
    try:
        o = subprocess.run(["gh"]+args, capture_output=True, text=True, timeout=60)
        return o.stdout if o.returncode == 0 else ""
    except Exception: return ""
def ghj(args):
    out = gh(args)
    try: return json.loads(out) if out.strip() else None
    except Exception: return None
def wait_search():
    for _ in range(180):
        out = gh(["api","rate_limit","--jq",".resources.search.remaining"])
        if out.strip().isdigit() and int(out) >= 2: return
        time.sleep(1)
def search_users(q):
    wait_search()
    d = ghj(["api","-X","GET","search/users","-f",f"q={q}","-f","per_page=5"])
    return [it["login"] for it in d.get("items",[])] if d else []
def enrich(l):
    out = gh(["api",f"users/{l}","--jq","[.login,(.name//\"\"),(.company//\"\"),(.bio//\"\"),(.followers|tostring)]"])
    try:
        d = json.loads(out); return {"login":d[0],"name":d[1],"company":d[2],"bio":d[3],"flw":int(d[4] or 0)}
    except Exception: return None

JVM_LANGS = {"java","kotlin","groovy","scala","clojure"}
def deep_signals(login):
    """Extra corroboration for a name-match without affiliation match: orgs + a JVM-repo signal.
    Gated (called only when needed) to bound core-API cost."""
    orgs = ghj(["api",f"users/{login}/orgs","--jq","[.[].login]"]) or []
    langs = ghj(["api",f"users/{login}/repos?sort=pushed&per_page=10&type=owner","--jq","[.[].language]"]) or []
    jvm_repo = any((l or "").lower() in JVM_LANGS for l in langs)
    return {"orgs":[o for o in orgs if o], "jvm_repo":jvm_repo}

# ---- load db state for dedupe/reuse ----
def load_csv(name):
    p = os.path.join(DB, name)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []
seen = {r["norm_name"] for r in load_csv("speakers.csv")}
res_db = {r["norm_name"]: r for r in load_csv("resolutions.csv")}
# alias ledger (authoritative human/auto overrides). confirm -> force login HIGH; reject -> never pick.
ALIAS, REJECT = {}, {}
for a in load_csv("aliases.csv"):
    nn = norm(a.get("norm_name","")); lg = (a.get("github_login") or "").strip()
    if not nn or not lg: continue
    if a.get("decision") == "confirm": ALIAS[nn] = lg
    elif a.get("decision") == "reject": REJECT.setdefault(nn, set()).add(lg)

# EXCLUDE: repos already listed in skills/**/*.yaml (so the loop never re-promotes them)
SKILLS_DIR = "/Users/tschuehly/IdeaProjects/jvm-skills/skills"
EXCLUDE = set()
for root, _, files in os.walk(SKILLS_DIR):
    for fn in files:
        if fn.endswith((".yaml", ".yml")):
            for ln in open(os.path.join(root, fn), errors="replace"):
                m = re.match(r"\s*repo:\s*['\"]?([^'\"#\s]+)", ln)
                if m: EXCLUDE.add(m.group(1).strip().lower())

CAND_KEYS = ("login","name","company","bio","flw","nm","am","orgs","jvm_repo")
def _cand_out(c): return {k: c.get(k) for k in CAND_KEYS if k in c}

def resolve(name, aff):
    nn = norm(name)
    # 1) alias ledger is authoritative — force the confirmed login (HIGH), one enrich for display fields
    if nn in ALIAS:
        c = enrich(ALIAS[nn]) or {}
        return {"norm_name":nn,"name":name,"aff":aff,"login":ALIAS[nn],"confidence":"HIGH",
                "gh_name":c.get("name",""),"gh_company":c.get("company",""),
                "followers":int(c.get("flw") or 0),"method":"alias","reused":False,"cands":[]}
    if nn in seen:  # reuse existing resolution
        r = res_db.get(nn, {})
        return {"norm_name":nn,"name":name,"aff":aff,"login":r.get("github_login",""),
                "confidence":r.get("confidence","?"),"gh_name":r.get("gh_name",""),
                "gh_company":r.get("gh_company",""),"followers":int(r.get("followers") or 0),
                "method":"reused-from-db","reused":True,"cands":[]}
    logins = search_users(f"{name} in:fullname")
    method = "fullname"
    if not logins and norm(name) != name.lower():
        logins = search_users(f"{norm(name)} in:fullname"); method = "fullname-ascii"
    if not logins:
        wait_search(); d = ghj(["search","users",name,"--json","login","--limit","5"])
        logins = [x["login"] for x in d] if d else []; method = "broad"
    rej = REJECT.get(nn, set())
    cands = [c for c in (enrich(l) for l in logins) if c and c["login"] not in rej]
    nt = nn.split(); first, last = (nt[0], nt[-1]) if nt else ("","")
    aff_t = [t for t in norm(aff).split() if t not in STOP and len(t) >= 3]
    for c in cands:
        gnt = set(norm(c["name"]).split())
        c["nm"] = (first in gnt and last in gnt)
        c["am"] = any(t in norm(c["company"]+" "+c["bio"]) for t in aff_t) if aff_t else False
    namematch = sorted([c for c in cands if c["nm"]], key=lambda c: -c["flw"])
    aff_high = [c for c in namematch if c["am"]]
    chosen, conf = None, "UNRESOLVED"
    if aff_high:
        chosen, conf = max(aff_high, key=lambda c: c["flw"]), "HIGH"
    elif namematch:
        top = namematch[0]; runner = namematch[1]["flw"] if len(namematch) > 1 else 0
        # permissive + investigative: a name match needs only ONE corroborating signal for HIGH.
        ds = deep_signals(top["login"])           # gated: only when no aff-match winner exists
        top["orgs"], top["jvm_repo"] = ds["orgs"], ds["jvm_repo"]
        org_match = bool(aff_t) and any(t in norm(o) for o in ds["orgs"] for t in aff_t)
        dominant = bool(top["company"]) and top["flw"] >= 50 and top["flw"] >= 3*runner
        if top["am"] or org_match or ds["jvm_repo"] or dominant:
            chosen, conf = top, "HIGH"
            method += "+" + ("aff" if top["am"] else "org" if org_match else "jvmrepo" if ds["jvm_repo"] else "dominant")
        else:
            chosen, conf = top, "MED"
    return {"norm_name":nn,"name":name,"aff":aff,
            "login":chosen["login"] if chosen else "",
            "confidence":conf,"gh_name":chosen["name"] if chosen else "",
            "gh_company":chosen["company"] if chosen else "",
            "followers":chosen["flw"] if chosen else 0,
            "method":method,"reused":False,
            "cands":[_cand_out(c) for c in cands]}

def scan(login):
    raw = gh(["api",f"users/{login}/repos?per_page=100&sort=pushed&type=owner",
              "--jq",".[]|select(.fork==false)|[.name,(.stargazers_count|tostring),(.pushed_at//\"\")]|@tsv"])
    repos = [ln.split("\t") for ln in raw.splitlines() if ln.strip()][:25]
    hits, scanned = [], 0
    for parts in repos:
        rname, stars = parts[0], parts[1]; pushed = parts[2] if len(parts) > 2 else ""
        time.sleep(0.7); scanned += 1
        tj = ghj(["api",f"repos/{login}/{rname}/git/trees/HEAD?recursive=1"])
        if not tj: continue
        tree_sha = tj.get("sha",""); paths = [n["path"] for n in tj.get("tree",[]) if n.get("type")=="blob"]
        matched = [p for p in paths if SKILL_RE.search(p)]
        if matched:
            hits.append({"repo":rname,"stars":int(stars or 0),"pushed_at":pushed,
                         "head_sha":tree_sha,"paths":matched,
                         "already_listed": f"{login}/{rname}".lower() in EXCLUDE})
    return {"scanned_repos":scanned,"hits":hits}

out = {"resolutions":[], "scans":{}}
if LOGINS_MODE is not None:  # scan-only mode (investigate-accepted MEDs)
    print(f"=== SCAN-ONLY {len(LOGINS_MODE)} login(s) ===", flush=True)
    for login in LOGINS_MODE:
        s = scan(login); out["scans"][login] = s
        n = sum(len(h["paths"]) for h in s["hits"])
        print(f"  {login:<18} {s['scanned_repos']} repos -> {len(s['hits'])} w/ skills, {n} files", flush=True)
    json.dump(out, open(OUT,"w"), indent=2)
    print(f"\nwrote {OUT}", flush=True)
    sys.exit(0)

print(f"=== RESOLVE ({len(SPEAKERS)} speakers) ===", flush=True)
for name, aff in SPEAKERS:
    r = resolve(name, aff)
    out["resolutions"].append(r)
    tag = {"HIGH":"AUTO","MED":"manual","UNRESOLVED":"park","?":"reused"}.get(r["confidence"],"?")
    note = " [reused]" if r["reused"] else ""
    print(f"  {name:<24} -> {(r['login'] or '—'):<18} {r['confidence']:<11}{tag}{note}"
          f"  (gh='{r['gh_name']}' co='{r['gh_company']}' flw={r['followers']})", flush=True)

high_new = [r for r in out["resolutions"] if r["confidence"]=="HIGH" and not r["reused"] and r["login"]]
print(f"\n=== SCAN {len(high_new)} new HIGH handles (throttled tree-scan) ===", flush=True)
for r in high_new:
    s = scan(r["login"]); out["scans"][r["login"]] = s
    n = sum(len(h["paths"]) for h in s["hits"])
    print(f"  {r['login']:<18} {s['scanned_repos']} repos -> {len(s['hits'])} repos w/ skills, {n} files", flush=True)
    for h in s["hits"]:
        mark = " [ALREADY-LISTED]" if h.get("already_listed") else ""
        for p in h["paths"]: print(f"        {h['repo']} ({h['stars']}★) :: {p}{mark}", flush=True)

json.dump(out, open(OUT,"w"), indent=2)
print(f"\nwrote {OUT}", flush=True)
