#!/usr/bin/env python3
"""Generate a self-contained HTML review page from db/*.csv -> skill-scout/review.html.
Shows every decision with its reasoning: found / needs-review / reviewable non-JVM /
promote-worthy JVM-collection / vendored leads / manual-confirm / parked / filtered noise."""
import csv, os, html, datetime
DB = "/Users/tschuehly/IdeaProjects/jvm-skills/skill-scout/db"
OUT = "/Users/tschuehly/IdeaProjects/jvm-skills/skill-scout/review.html"
TODAY = datetime.date.today().isoformat()
def load(n):
    p = os.path.join(DB, n)
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []
conf=load("conferences.csv"); spk=load("speakers.csv"); sc=load("speaker_conferences.csv")
res=load("resolutions.csv"); repos=load("repos.csv"); sf=load("skill_files.csv")
rej=load("rejected.csv"); runs=load("runs.csv"); bun=load("bundles.csv")

res_by_login={r["github_login"]:r for r in res if r["github_login"]}
name_by_norm={s["norm_name"]:s["name"] for s in spk}
stars_by={(r["login"],r["name"]):r["stars"] for r in repos}
confs_by_norm={}
for r in sc: confs_by_norm.setdefault(r["norm_name"],[]).append(r["conference"])
def author(login): return res_by_login.get(login,{}).get("gh_name",login)
def e(s): return html.escape(str(s or ""))
def gh(login,repo,path=None):
    u=f"https://github.com/{login}/{repo}"+(f"/blob/HEAD/{path}" if path else "")
    label=f"{login}/{repo}"+(f" :: {path.split('/')[-2] if '/' in path else path}" if path else "")
    return f'<a href="{e(u)}" target="_blank">{e(label)}</a>'
def stars(login,repo): return stars_by.get((login,repo),"")

CAT_LANG={"language":["java"],"testing":["java","kotlin"],"build":["java"],"data":["java"],"database":["java"]}
def yaml_snippet(r):
    login,repo,path=r["login"],r["repo"],r.get("path","")
    skill=path.split("/")[-2] if "/" in path else path.rsplit(".",1)[0]
    name=skill.replace("-"," ").replace("_"," ").strip().title() or repo
    desc=" ".join((r.get("notes") or r.get("reasoning") or "").split())
    cat=r.get("category") or "tool"
    langs=CAT_LANG.get(cat,["java","kotlin"])
    jvm=(r.get("jvm_fit") or "").lower()
    trust="curated"
    lg="\n".join(f"  - {l}" for l in langs)
    return (f"name: {name}\n"
            f"description: >-\n  {desc}\n"
            f"repo: {login}/{repo}\n"
            f'skill_path: "{path}"\n'
            f"category: {cat}\n"
            f"languages:\n{lg}\n"
            f"trust: {trust}\n"
            f"author: {author(login)}\n"
            f'version: "1.0.0"\n'
            f'last_updated: "{TODAY}"\n'
            f"scope: focused\n"
            f"tech:\n  - # TODO\n"
            f"tags:\n  - # TODO")
def promote_cell(r):
    return (f'<details class=yd><summary title="copy-paste promotion YAML">📋 yaml</summary>'
            f'<div class=ybox><button class=cp onclick="cpy(this)">copy</button>'
            f'<pre class=yaml>{e(yaml_snippet(r))}</pre></div></details>')

def bundle_yaml(b):
    members=[m for m in (b.get("members") or "").split(";") if m]
    root=(b.get("root") or "").strip()
    name=(b.get("name") or "").replace("-"," ").replace("_"," ").strip().title() or b["repo"]
    desc=" ".join((b.get("reasoning") or "").split())
    cat="workflow" if b.get("kind")=="workflow" else "framework"
    langs=["java","kotlin"] if b.get("kind")=="jvm" else ["agnostic"]
    lg="\n".join(f"  - {l}" for l in langs)
    sk="\n".join(f'  - "{(root + "/") if root else ""}{m}/SKILL.md"' for m in members) or "  # (members)"
    return (f"name: {name}\n"
            f"description: >-\n  {desc}\n"
            f"repo: {b['login']}/{b['repo']}\n"
            f'skill_path: "{root}"\n'
            f"category: {cat}\n"
            f"languages:\n{lg}\n"
            f"trust: curated\n"
            f"author: {author(b['login'])}\n"
            f'version: "1.0.0"\n'
            f'last_updated: "{TODAY}"\n'
            f"scope: bundle\n"
            f"skills:\n{sk}\n"
            f"tags:\n  - # TODO")
def bundle_cell(b):
    return (f'<details class=yd><summary title="copy-paste bundle promotion YAML">📋 yaml</summary>'
            f'<div class=ybox><button class=cp onclick="cpy(this)">copy</button>'
            f'<pre class=yaml>{e(bundle_yaml(b))}</pre></div></details>')
def bundle_rows(rows):
    out=[]
    for b in rows:
        members=[m for m in (b.get("members") or "").split(";") if m]
        copies=[c for c in (b.get("copies") or "").split(";") if c]
        dupes=f'<div class=dupes>also copied in: {e(", ".join(copies))}</div>' if copies else ""
        steps=f'<div class=dupes>{e(" → ".join(members))}</div>'
        kind=e(b.get("kind") or "")
        out.append(f'<tr data-text="{e((b["login"]+" "+b["repo"]+" "+(b.get("name") or "")+" "+(b.get("reasoning") or "")).lower())}">'
                   f'<td class=sk>{e(b.get("name") or "")}</td>'
                   f'<td>{gh(b["login"],b["repo"])}{steps}</td>'
                   f'<td>{e(author(b["login"]))}</td>'
                   f'<td><span class=badge>{kind}</span></td>'
                   f'<td>{len(members)}</td>'
                   f'<td>{e(stars(b["login"],b["repo"]))}</td>'
                   f'<td>{e(b.get("reasoning") or "")}{dupes}</td>'
                   f'<td>{bundle_cell(b)}</td></tr>')
    return "\n".join(out)

def skill_rows(rows, cols_extra):
    out=[]
    for r in rows:
        path=r.get("path",""); skill=path.split("/")[-2] if "/" in path else path
        cells="".join(f"<td>{c}</td>" for c in cols_extra(r))
        out.append(f'<tr data-text="{e((r.get("login","")+" "+r.get("repo","")+" "+path+" "+r.get("reasoning","")).lower())}">'
                   f'<td class="sk">{e(skill)}</td><td>{gh(r["login"],r["repo"],path)}</td>'
                   f'<td>{e(author(r["login"]))}</td>{cells}</tr>')
    return "\n".join(out)

from skilldedup import dedup_found, found_keys, skill_name
_found_raw=[s for s in sf if s["status"]=="found"]
found=dedup_found(_found_raw, stars_by)  # one canonical row per (author, skill); copies -> r["_dupes"]
found.sort(key=lambda s:-int(stars_by.get((s["login"],s["repo"]),0) or 0))
needs=[s for s in sf if s["status"]=="needs_review"]
jvm_bundles=[b for b in bun if b.get("status") in ("found","needs_review") and b.get("kind")=="jvm"]
wf_bundles=[b for b in bun if b.get("status") in ("found","needs_review") and b.get("kind")!="jvm"]
_promoted=found_keys(_found_raw)  # hide copies of a promoted skill from the reject piles (no found+rejected dup)
rej=[r for r in rej if (r["login"],skill_name(r["path"])) not in _promoted]
offtopic=[r for r in rej if r["reason"].startswith("off-topic")]
jvmcoll=[r for r in rej if r["reason"]=="jvm-collection"]
vendored=[r for r in rej if r["reason"]=="vendored"]
review_q=[r for r in rej if r["reason"]=="review"]
noise=[r for r in rej if r["reason"] in ("boilerplate","demo","project-doc","test-fixture","already-listed")]
med=sorted([r for r in res if r["confidence"]=="MED"], key=lambda r:-int(r["followers"] or 0))
park=[r for r in res if r["confidence"]=="UNRESOLVED"]

P=[]; W=P.append
W(f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Skill-Scout review</title>
<style>
:root{{--bg:#0f1115;--card:#171a21;--line:#2a2f3a;--fg:#e6e9ef;--mut:#9aa4b2;--acc:#6ea8fe;
--ok:#3fb950;--warn:#d29922;--rev:#a371f7;--jvm:#3fb950;--ven:#db6d28;--noise:#6e7681}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.5 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif}}
header{{position:sticky;top:0;background:#0f1115ee;backdrop-filter:blur(6px);
border-bottom:1px solid var(--line);padding:14px 20px;z-index:5}}
h1{{font-size:18px;margin:0 0 4px}} .sub{{color:var(--mut);font-size:13px}}
.wrap{{max-width:1180px;margin:0 auto;padding:20px}}
.stats{{display:flex;gap:18px;flex-wrap:wrap;margin-top:8px}}
.stat b{{font-size:18px}} .stat span{{color:var(--mut);font-size:12px;display:block}}
#q{{width:100%;padding:9px 12px;margin:14px 0;background:var(--card);border:1px solid var(--line);
border-radius:8px;color:var(--fg);font-size:14px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:16px 0;overflow:hidden}}
section>h2{{font-size:15px;margin:0;padding:12px 16px;border-bottom:1px solid var(--line);
display:flex;align-items:center;gap:8px}} section>h2 .n{{color:var(--mut);font-weight:400;font-size:13px}}
.blurb{{color:var(--mut);font-size:13px;padding:8px 16px 0}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:7px 16px;border-top:1px solid var(--line);vertical-align:top}}
th{{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.03em}}
td.sk{{font-weight:600;white-space:nowrap}} a{{color:var(--acc);text-decoration:none}} a:hover{{text-decoration:underline}}
.reason{{font-size:11px;padding:2px 7px;border-radius:20px;white-space:nowrap;border:1px solid var(--line)}}
.r-off-topic-workflow{{color:var(--rev);border-color:var(--rev)}}
.r-off-topic-service,.r-off-topic-tech{{color:#c08bff;border-color:#5a3a8a}}
.badge{{font-size:11px;padding:1px 6px;border-radius:4px;background:#222834;color:var(--mut)}}
details summary{{cursor:pointer;padding:12px 16px;color:var(--mut)}}
.lead-ok{{color:var(--ok)}} .lead-warn{{color:var(--warn)}}
.ledger td{{font-size:12px;color:var(--mut)}} .hide{{display:none}}
.pill{{display:inline-block;background:#222834;border-radius:6px;padding:1px 7px;margin:2px 0;font-size:12px}}
details.yd summary{{padding:0;color:var(--acc);font-size:12px;list-style:none;white-space:nowrap}}
details.yd summary::-webkit-details-marker{{display:none}}
.ybox{{position:relative;margin-top:6px}}
pre.yaml{{background:#0b0d11;border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:0;
font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#c9d3e0;white-space:pre;overflow:auto;max-width:520px}}
.cp{{position:absolute;top:6px;right:6px;background:#222834;color:var(--fg);border:1px solid var(--line);
border-radius:6px;padding:3px 9px;font-size:11px;cursor:pointer;z-index:1}} .cp:hover{{background:#2a3140}}
.cp.done{{color:var(--ok);border-color:var(--ok)}}
.hero{{border-color:var(--ok)}} .hero>h2{{background:#15291b}}
.dupes{{color:var(--mut);font-size:11px;margin-top:4px;font-style:italic}}
</style></head><body>
<header><h1>🔭 Skill-Scout — review</h1>
<div class=sub>Generated {TODAY} from <code>db/*.csv</code>. Every scanned skill carries a decision + reasoning. <b style="color:var(--ok)">Review ✅ Found</b> → click <b>📋 yaml</b> → paste into <code>skills/&lt;category&gt;/&lt;slug&gt;.yaml</code>.</div>
<div class=stats>
<div class=stat><b class=lead-ok>{len(found)}</b><span>found</span></div>
<div class=stat><b class=lead-warn>{len(needs)}</b><span>needs review</span></div>
<div class=stat><b style="color:var(--acc)">{len(review_q)}</b><span>needs classify</span></div>
<div class=stat><b style="color:var(--rev)">{len(offtopic)}</b><span>non-JVM (review)</span></div>
<div class=stat><b class=lead-ok>{len(jvmcoll)}</b><span>JVM collection</span></div>
<div class=stat><b>{len(noise)}</b><span>filtered noise</span></div>
<div class=stat><b>{len(conf)}</b><span>conferences</span></div>
<div class=stat><b>{len(spk)}</b><span>speakers</span></div>
</div></header>
<div class=wrap>
<input id=q placeholder="Filter all tables by repo / skill / author / reasoning…" oninput="filt(this.value)">
""")

W(f"""<section class=hero><h2>✅ Found skills <span class=n>· {len(found)} · ready to promote</span></h2>
<table><thead><tr><th>Skill</th><th>Repo</th><th>Author</th><th>Cat</th><th>Depth</th><th>★</th><th>Why included (reasoning)</th><th>Promote</th></tr></thead><tbody>
{skill_rows(found, lambda r:[e(r["category"]), e(r["depth"]), e(stars(r["login"],r["repo"])), e(r.get("reasoning") or r.get("notes"))+(f'<div class=dupes>also copied in: {e(", ".join(r["_dupes"]))}</div>' if r.get("_dupes") else ""), promote_cell(r)])}
</tbody></table></section>""")

_BUNDLE_HEAD="<table><thead><tr><th>Bundle</th><th>Repo · steps</th><th>Author</th><th>Kind</th><th>#</th><th>★</th><th>Why included (reasoning)</th><th>Promote</th></tr></thead><tbody>"
if jvm_bundles:
    W(f"""<section class=hero><h2>📦 JVM skill bundles <span class=n>· {len(jvm_bundles)} · dependent suites, promote as a unit</span></h2>
    {_BUNDLE_HEAD}
    {bundle_rows(jvm_bundles)}
    </tbody></table></section>""")
if wf_bundles:
    W(f"""<section><h2>📦 Workflow bundles <span class=n>· {len(wf_bundles)} · general agentic workflows (non-JVM)</span></h2>
    <div class=blurb>Cohesive, dependent workflow suites (e.g. a spec-driven-dev pipeline). Not JVM, but listable under the <code>workflow</code> category if you want them — evaluated as a whole.</div>
    {_BUNDLE_HEAD}
    {bundle_rows(wf_bundles)}
    </tbody></table></section>""")

if needs:
    W(f"""<section><h2>🟡 Needs review <span class=n>· {len(needs)} · borderline, your call</span></h2>
    <table><thead><tr><th>Skill</th><th>Repo</th><th>Author</th><th>★</th><th>Why borderline (reasoning)</th><th>Promote</th></tr></thead><tbody>
    {skill_rows(needs, lambda r:[e(stars(r["login"],r["repo"])), e(r.get("reasoning") or r.get("notes")), promote_cell(r)])}
    </tbody></table></section>""")

if review_q:
    W(f"""<section><h2>🔍 Needs human classification <span class=n>· {len(review_q)} · the promotion queue</span></h2>
    <div class=blurb>Real <code>SKILL.md</code> files the auto-classifier could not judge JVM-vs-offtopic from the path. <b>Read these and promote the JVM ones</b> to <code>skills/*.yaml</code>.</div>
    <table><thead><tr><th>Skill</th><th>Repo</th><th>Author</th><th>Reasoning</th></tr></thead><tbody>
    {skill_rows(review_q, lambda r:[e(r["reasoning"])])}
    </tbody></table></section>""")

W(f"""<section><h2>♻️ Real but non-JVM skills <span class=n>· {len(offtopic)} · reviewable</span></h2>
<div class=blurb>Well-formed, reusable skills that are <b>not JVM-specific</b> — generic agent/dev <b>workflow</b>, external-<b>service</b> integrations, or non-JVM <b>tech</b>. Candidates for a separate directory.</div>
<table><thead><tr><th>Skill</th><th>Repo</th><th>Author</th><th>Reason</th><th>Why rejected (reasoning)</th></tr></thead><tbody>
{skill_rows(sorted(offtopic,key=lambda r:(r["reason"],r["login"])), lambda r:[f'<span class="reason r-{e(r["reason"])}">{e(r["reason"].replace("off-topic-",""))}</span>', e(r["reasoning"])])}
</tbody></table></section>""")

W(f"""<section><h2>🧩 JVM skills in a found collection <span class=n>· {len(jvmcoll)} · promote-worthy</span></h2>
<div class=blurb>JVM skills inside an already-found collection, not yet listed individually.</div>
<table><thead><tr><th>Skill</th><th>Repo</th><th>Author</th><th>Reasoning</th></tr></thead><tbody>
{skill_rows(jvmcoll, lambda r:[e(r["reasoning"])])}
</tbody></table></section>""")

if vendored:
    W(f"""<section><h2>🔁 Vendored third-party skills <span class=n>· {len(vendored)} · author leads</span></h2>
    <div class=blurb>JVM skills copied into a speaker's repo but authored by someone else — chase the original author.</div>
    <table><thead><tr><th>Skill</th><th>Repo</th><th>In repo of</th><th>Reasoning</th></tr></thead><tbody>
    {skill_rows(vendored, lambda r:[e(r["reasoning"])])}
    </tbody></table></section>""")

# manual-confirm + parked
medrows="\n".join(f'<tr data-text="{e((name_by_norm.get(r["norm_name"],r["norm_name"])+" "+r["github_login"]).lower())}">'
    f'<td>{e(name_by_norm.get(r["norm_name"],r["norm_name"]))}</td>'
    f'<td><a href="https://github.com/{e(r["github_login"])}" target=_blank>{e(r["github_login"])}</a></td>'
    f'<td>{e(r["gh_company"].strip())}</td><td>{e(r["followers"])}</td>'
    f'<td>{e(", ".join(confs_by_norm.get(r["norm_name"],[])))}</td></tr>' for r in med)
W(f"""<section><h2>✋ Manual-confirm queue (MED) <span class=n>· {len(med)}</span></h2>
<div class=blurb>Name matched but not auto-accepted (blank GH company / no dominant winner). A human confirms, then they get scanned.</div>
<table><thead><tr><th>Speaker</th><th>GitHub</th><th>Company</th><th>Followers</th><th>Conference(s)</th></tr></thead><tbody>
{medrows}</tbody></table></section>""")

W(f"""<section><h2>📇 Parked — UNRESOLVED <span class=n>· {len(park)}</span></h2>
<div class=blurb style="padding-bottom:12px">{" ".join(f'<span class=pill>{e(name_by_norm.get(r["norm_name"],r["norm_name"]))}</span>' for r in park) or "none"}</div></section>""")

# filtered noise (collapsible)
W(f"""<section><details><summary>🗑️ Filtered noise — {len(noise)} hits (boilerplate / demo / project-doc / test-fixture / already-listed)</summary>
<table><thead><tr><th>Skill</th><th>Repo</th><th>Author</th><th>Reason</th><th>Reasoning</th></tr></thead><tbody>
{skill_rows(sorted(noise,key=lambda r:(r["reason"],r["login"])), lambda r:[f'<span class=badge>{e(r["reason"])}</span>', e(r["reasoning"])])}
</tbody></table></details></section>""")

# ledger
ledrows="\n".join(f'<tr><td>{e(r["conference"])}</td><td>{e(r["speakers"])}</td><td>{e(r["resolved"])}</td>'
    f'<td>{e(r["scanned_repos"])}</td><td>{e(r["found"])}</td><td>{e(r["parked"])}</td><td>{e(r["notes"])}</td></tr>' for r in runs)
W(f"""<section class=ledger><h2>🏃 Run ledger</h2>
<table><thead><tr><th>Conference</th><th>Speakers</th><th>HIGH</th><th>Scanned</th><th>Found</th><th>Parked</th><th>Notes</th></tr></thead><tbody>
{ledrows}</tbody></table></section>""")

W("""</div><script>
function filt(v){v=v.toLowerCase().trim();
 document.querySelectorAll('tbody tr').forEach(tr=>{
   const t=tr.getAttribute('data-text')||tr.textContent.toLowerCase();
   tr.classList.toggle('hide', v && !t.includes(v));});}
function cpy(btn){const pre=btn.parentNode.querySelector('pre.yaml');
 navigator.clipboard.writeText(pre.innerText).then(()=>{const o=btn.textContent;
   btn.textContent='copied ✓';btn.classList.add('done');
   setTimeout(()=>{btn.textContent=o;btn.classList.remove('done')},1400);});}
</script></body></html>""")
open(OUT,"w").write("\n".join(P))
print(f"wrote {OUT}")
