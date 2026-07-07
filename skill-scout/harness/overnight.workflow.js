export const meta = {
  name: 'skill-scout-overnight',
  description: 'Overnight skill-scout: harvest conference rosters, serial chunked GitHub tree-scan (core-bucket mutex), Haiku judge + Sonnet adversarial recheck, apply to CSVs with validation. Mechanical command-runner agents run on Haiku/low-effort.',
  phases: [
    { title: 'Load queue', detail: 'read unscanned confs from conferences.csv' },
    { title: 'Harvest', detail: 'WebFetch rosters in parallel; browser fallback serial' },
    { title: 'Scan', detail: 'SERIAL chunked tree-scan (GitHub core mutex)' },
    { title: 'Eval', detail: 'Haiku judge + Sonnet adversarial recheck' },
    { title: 'Apply', detail: 'serial: build_conf.py (deterministic) + CSV upsert + self-validate' },
    { title: 'Commit', detail: 'opt-in (autoCommit): git commit ONLY skill-scout outputs' },
  ],
}

const H = '/Users/tschuehly/IdeaProjects/jvm-skills/skill-scout/harness'
// Defensive: args may arrive as an object OR a JSON-encoded string. Parse either so `limit` always applies.
const A = (typeof args === 'string') ? (args ? JSON.parse(args) : {}) : (args || {})
const TODAY = A.today || '2026-06-26'
const LIMIT = A.limit || 999
const ONLY = Array.isArray(A.slugs) ? new Set(A.slugs) : null // optional explicit slug allowlist
const CHUNK = 22 // speakers per scout.py call — under the 10-min Bash timeout; bigger = fewer scan agents
const JUDGE_MODEL = A.judgeModel || 'haiku' // bulk per-file judging — cheap model
const RECHECK_MODEL = A.recheckModel || 'sonnet' // adversarial recheck — Sonnet by default; pass recheckModel:'opus' for the hardest runs
const MECH = { model: 'haiku', effort: 'low' } // pure command-runner agents (run a python script, report ok) — no reasoning, no quality tradeoff
const EVAL_ONLY = Array.isArray(A.evalOnly) && A.evalOnly.length ? A.evalOnly : null // [{slug,name,url}] reuse existing *_scout.json
const DRY_APPLY = !!A.dryApply // apply.py --dry (render, don't mutate the CSVs) — for fast tests
const AUTO_COMMIT = !!A.autoCommit // opt-in: final step commits ONLY skill-scout outputs (db/, candidates.md, review.html, rules/*.md)
const REPO = '/Users/tschuehly/IdeaProjects/jvm-skills'
const MAX_SPEAKERS = A.maxSpeakers || 0 // optional per-conference speaker cap (small trials); 0 = full roster

const QUEUE_SCHEMA = { type: 'object', required: ['confs'], properties: { confs: { type: 'array', items: {
  type: 'object', required: ['name', 'url', 'slug'],
  properties: { name: { type: 'string' }, url: { type: 'string' }, slug: { type: 'string' } } } } } }
const HARVEST_SCHEMA = { type: 'object', required: ['ok', 'count', 'needsBrowser'], properties: {
  ok: { type: 'boolean' }, count: { type: 'integer' }, needsBrowser: { type: 'boolean' },
  method: { type: 'string' }, note: { type: 'string' } } }
const SPLIT_SCHEMA = { type: 'object', required: ['chunks'], properties: { chunks: { type: 'integer' }, note: { type: 'string' } } }
const STEP_SCHEMA = { type: 'object', required: ['ok'], properties: { ok: { type: 'boolean' }, note: { type: 'string' } } }
const PREFILTER_SCHEMA = { type: 'object', required: ['judge', 'skip'], properties: {
  judge: { type: 'integer' }, skip: { type: 'integer' } } }
// One LLM verdict per skill file. status=found/needs_review -> promote (depth/jvm_fit/category/lines/notes set);
// status=reject -> rejected.csv with `reason` from the taxonomy. `reasoning` is required & specific on every row.
const JUDGE_ITEM = { type: 'object', required: ['login', 'repo', 'path', 'status', 'reasoning'],
  properties: { login: { type: 'string' }, repo: { type: 'string' }, path: { type: 'string' },
    status: { type: 'string', enum: ['found', 'needs_review', 'reject'] },
    reason: { type: 'string', enum: ['off-topic-workflow', 'off-topic-service', 'off-topic-tech', 'demo',
      'project-doc', 'test-fixture', 'jvm-collection', 'boilerplate', 'vendored', 'review'] },
    depth: { type: 'integer' }, jvm_fit: { type: 'string' }, category: { type: 'string' },
    lines: { type: 'integer' }, notes: { type: 'string' }, reasoning: { type: 'string' } } }
const JUDGE_SCHEMA = { type: 'object', required: ['verdicts'], properties: { verdicts: { type: 'array', items: JUDGE_ITEM } } }
const RECHECK_SCHEMA = { type: 'object', required: ['keep', 'reason'], properties: { keep: { type: 'boolean' }, reason: { type: 'string' } } }
const APPLY_SCHEMA = { type: 'object', required: ['ok', 'validation'], properties: {
  ok: { type: 'boolean' }, validation: { type: 'string' }, note: { type: 'string' } } }
const PREP_SCHEMA = { type: 'object', required: ['judge', 'skip', 'bundles'], properties: {
  judge: { type: 'integer' }, skip: { type: 'integer' }, bundles: { type: 'integer' } } }
// One verdict per bundle CANDIDATE (cohesive set of dependent skills, judged as a unit).
const BUNDLE_ITEM = { type: 'object', required: ['repo', 'root', 'cohesive', 'status', 'reasoning'], properties: {
  repo: { type: 'string' }, root: { type: 'string' }, cohesive: { type: 'boolean' },
  kind: { type: 'string', enum: ['jvm', 'workflow'] }, status: { type: 'string', enum: ['found', 'needs_review', 'reject'] },
  name: { type: 'string' }, depth: { type: 'integer' }, reason: { type: 'string' }, reasoning: { type: 'string' } } }
const BUNDLE_EVAL_SCHEMA = { type: 'object', required: ['verdicts'], properties: { verdicts: { type: 'array', items: BUNDLE_ITEM } } }
const INVESTIGATE_SCHEMA = { type: 'object', required: ['decisions'], properties: { decisions: { type: 'array', items: {
  type: 'object', required: ['norm_name', 'login', 'accept', 'reasoning'], properties: {
    norm_name: { type: 'string' }, login: { type: 'string' }, accept: { type: 'boolean' }, reasoning: { type: 'string' } } } } } }
const REFINE_SCHEMA = { type: 'object', required: ['ok'], properties: { ok: { type: 'boolean' }, added: { type: 'integer' }, note: { type: 'string' } } }

let scanned
const bySlug = {}
let queued = 0, harvestedCount = 0, browserNeededSlugs = [] // summary values, hoisted above the branch
if (!EVAL_ONLY) {
// ---------------- Phase 1: load queue ----------------
phase('Load queue')
const q = await agent(
  `Run: python3 ${H}/queue.py — it prints JSON {confs:[{name,url,slug}]} of every unscanned conference with `
  + `DETERMINISTIC slugs. Return that JSON object verbatim (do not modify the slugs).`,
  { label: 'load-queue', phase: 'Load queue', schema: QUEUE_SCHEMA, ...MECH })
const allConfs = (q && q.confs || [])
const confs = (ONLY ? allConfs.filter(c => ONLY.has(c.slug)) : allConfs).slice(0, LIMIT)
Object.assign(bySlug, Object.fromEntries(confs.map(c => [c.slug, c])))
queued = allConfs.length
log(`Queue: ${allConfs.length} unscanned conferences; processing ${confs.length} this run (limit=${LIMIT}).`)

// ---------------- Phase 2: harvest rosters ----------------
phase('Harvest')
const capNote = MAX_SPEAKERS ? `\nTRIAL CAP: extract ONLY the first ${MAX_SPEAKERS} speakers, then stop — do NOT extract the full roster.` : ''
const harvest = await parallel(confs.map(c => () => agent(
  `Harvest the speaker roster for "${c.name}" from ${c.url}.${capNote}\n`
  + `Use the WebFetch tool (load it via ToolSearch "select:WebFetch" first if it is not already available). `
  + `Ask WebFetch to return every speaker's NAME and AFFILIATION/company (affiliation is the key disambiguator — `
  + `capture it whenever shown; use "" when absent).\n`
  + `If ${H}/${c.slug}_speakers.json already exists as a non-empty JSON array, SKIP and return {ok:true,count:<len>,needsBrowser:false,method:"cached"}.\n`
  + `If WebFetch returns a JS shell ("Loading speakers…"), an empty/garbage body, or a 403/bot-block, DO NOT use the browser here — `
  + `return {ok:false,count:0,needsBrowser:true,note:"<why>"}.\n`
  + `On success, write a JSON array of [name, affiliation] pairs to ${H}/${c.slug}_speakers.json and return `
  + `{ok:true,count:N,needsBrowser:false,method:"webfetch"}.`,
  { label: `harvest:${c.slug}`, phase: 'Harvest', schema: HARVEST_SCHEMA, model: 'sonnet' })
  .then(r => ({ slug: c.slug, ...(r || { ok: false, count: 0, needsBrowser: false }) }))))

const browserNeeded = harvest.filter(h => h && h.needsBrowser).map(h => bySlug[h.slug]).filter(Boolean)
log(`WebFetch harvested ${harvest.filter(h => h && h.ok).length}/${confs.length}; ${browserNeeded.length} need browser rendering.`)
const browserResults = []
for (const c of browserNeeded) { // serial — avoid parallel Chrome contention
  const r = await agent(
    `Render the JS roster for "${c.name}" at ${c.url} using the agent-browser skill (Skill tool: agent-browser): `
    + `open the url, wait for the page to settle (networkidle), take a snapshot, and extract speaker NAME and `
    + `AFFILIATION from the speaker cards/headings (affiliation "" if not shown).${capNote} `
    + `Write a JSON array of [name, affiliation] pairs to ${H}/${c.slug}_speakers.json. `
    + `If the browser cannot render it after one genuine attempt, return {ok:false,count:0,note:"<why>"}. `
    + `Return {ok:true,count:N,needsBrowser:false,method:"browser"}.`,
    { label: `harvest-browser:${c.slug}`, phase: 'Harvest', schema: HARVEST_SCHEMA, model: 'sonnet' })
  browserResults.push({ slug: c.slug, ...(r || { ok: false }) })
}
const harvestedSlugs = new Set([
  ...harvest.filter(h => h && h.ok && h.count > 0).map(h => h.slug),
  ...browserResults.filter(h => h && h.ok && h.count > 0).map(h => h.slug),
])
const toScan = confs.filter(c => harvestedSlugs.has(c.slug))
harvestedCount = harvestedSlugs.size
browserNeededSlugs = browserNeeded.map(c => c.slug)
log(`Harvest complete: ${toScan.length} conferences have a roster; scanning them serially.`)

// ---------------- Phase 3: scan — SERIAL (GitHub core bucket is a global mutex) ----------------
phase('Scan')
scanned = []
for (const c of toScan) {
  const sp = await agent(
    `Run: python3 ${H}/split_speakers.py ${H}/${c.slug}_speakers.json ${H}/${c.slug}_chunk ${CHUNK} ${MAX_SPEAKERS}\n`
    + `It prints the number of chunk files written. Return {chunks:<that integer>}.`,
    { label: `split:${c.slug}`, phase: 'Scan', schema: SPLIT_SCHEMA, ...MECH })
  const n = (sp && sp.chunks) || 0
  if (!n) { log(`  ${c.slug}: split produced 0 chunks, skipping`); continue }
  let allOk = true
  for (let k = 0; k < n; k++) { // SERIAL across chunks AND across confs — one tree-scan at a time
    // A very slow chunk (huge roster, e.g. FOSDEM) can make the scout agent end WITHOUT emitting its
    // structured result, which makes agent() THROW. Catch it so one bad chunk degrades to a [partial]
    // conf instead of killing the whole batch — the merge below still uses whatever chunks did land.
    let r = null
    try {
      r = await agent(
        `Run the GitHub tree-scan for one roster chunk. Use the Bash tool with timeout: 600000 (10 min).\n`
        + `If ${H}/${c.slug}_scout_${k}.json already exists and is valid JSON, SKIP and return {ok:true,note:"cached"}.\n`
        + `Otherwise run exactly: python3 ${H}/scout.py ${H}/${c.slug}_chunk_${k}.json ${H}/${c.slug}_scout_${k}.json\n`
        + `This is rate-limit-throttled and may take several minutes; do not interrupt it. Return {ok:true} if it wrote the `
        + `output file (the last line is "wrote ..."), else {ok:false,note:"<tail of error>"}.`,
        { label: `scout:${c.slug}#${k}`, phase: 'Scan', schema: STEP_SCHEMA, ...MECH })
    } catch (e) { log(`  ${c.slug} chunk ${k}: scout threw (${(e && e.message || String(e)).slice(0, 120)})`) }
    if (!r || !r.ok) { allOk = false; log(`  ${c.slug} chunk ${k}: scout failed (${r && r.note})`) }
  }
  const parts = Array.from({ length: n }, (_, k) => `${H}/${c.slug}_scout_${k}.json`).join(' ')
  // merge the chunk outputs, then CHECKPOINT this conf's speakers+resolutions into the DB so the NEXT
  // conference's scout.py reuses them (cross-conference dedup — skips re-resolving repeat speakers).
  const ckpt = JSON.stringify({ conference: c.name, url: c.url || '', today: TODAY, roster_fetched_at: TODAY, scout: `${H}/${c.slug}_scout.json`, skills: [], rejected: [] })
  const mg = await agent(
    `Two steps for "${c.name}" — do BOTH:\n`
    + `1. Merge scout chunks: python3 ${H}/merge_scout.py ${H}/${c.slug}_scout.json ${parts}\n`
    + `2. Checkpoint speakers+resolutions to the DB (for cross-conference dedup). Write this JSON to ${H}/${c.slug}_ckpt.json exactly:\n${ckpt}\n`
    + `   then run: python3 ${H}/apply.py ${H}/${c.slug}_ckpt.json --checkpoint  — it writes only speakers/resolutions and must print "VALIDATION PASS".\n`
    + `Return {ok:true,note:"<merge summary + checkpoint speaker/resolution counts>"} if BOTH succeed, else {ok:false,note:"<error>"}.`,
    { label: `merge+ckpt:${c.slug}`, phase: 'Scan', schema: STEP_SCHEMA, ...MECH })
  if (mg && mg.ok) { scanned.push(c); log(`  scanned+checkpointed ${c.slug} (${n} chunks)${allOk ? '' : ' [partial]'}: ${mg.note || ''}`) }
}
log(`Scan complete: ${scanned.length} conferences scanned.`)
} else {
  scanned = EVAL_ONLY // [{slug,name,url}] — reuse existing <slug>_scout.json, skip harvest+scan
  for (const c of scanned) bySlug[c.slug] = c
  queued = harvestedCount = scanned.length
  log(`EVAL-ONLY: ${scanned.map(c => c.slug).join(', ')} — reusing existing *_scout.json, skipping harvest+scan.`)
}

// ---------------- Phase 4: eval — bundle-aware, rules-driven, self-refining ----------------
phase('Eval')
const JUDGE_BATCH = 40 // files per judge agent — bigger = fewer agents (Haiku has the context budget)
const DBDIR = '/Users/tschuehly/IdeaProjects/jvm-skills/skill-scout/db'
const EVAL_RULES = `${H}/rules/eval.md`, MATCH_RULES = `${H}/rules/matching.md`

// 4a) prep per conf: detect bundles, then prefilter (excluding bundle members). One agent per conf.
const prep = (await parallel(scanned.map(c => () => agent(
  `Prepare eval inputs for "${c.name}" — run BOTH with the Bash tool, in order:\n`
  + `1. python3 ${H}/bundle_detect.py ${H}/${c.slug}_scout.json ${H}/${c.slug}_bundles.json   (prints "bundles: N candidate(s) ...")\n`
  + `2. python3 ${H}/prefilter.py ${H}/${c.slug}_scout.json ${H}/${c.slug}_bundles.json        (prints "judge=N skip=M ...")\n`
  + `Return {judge:N, skip:M, bundles:N} from those two outputs.`,
  { label: `prep:${c.slug}`, phase: 'Eval', schema: PREP_SCHEMA, ...MECH })
  .then(r => ({ slug: c.slug, judge: (r && r.judge) || 0, skip: (r && r.skip) || 0, bundles: (r && r.bundles) || 0 }))))).filter(Boolean)
const prepBySlug = Object.fromEntries(prep.map(p => [p.slug, p]))
log(`Prep: ${prep.reduce((n, p) => n + p.judge, 0)} files to judge, ${prep.reduce((n, p) => n + p.skip, 0)} cheap-skipped, ${prep.reduce((n, p) => n + p.bundles, 0)} bundle candidates.`)

// 4b) judge — fan out batches (each reads eval.md first, then reasons about ~JUDGE_BATCH files); disk verdict cache.
const batches = []
for (const p of prep) for (let i = 0; i < p.judge; i += JUDGE_BATCH) batches.push({ slug: p.slug, name: bySlug[p.slug].name, start: i, end: Math.min(i + JUDGE_BATCH, p.judge) })
const judged = (await parallel(batches.map(b => () => agent(
  `Judge GitHub skill files for the jvm-skills directory (conference "${b.name}").\n`
  + `FIRST read the evaluation rules and apply them throughout: ${EVAL_RULES}\n`
  + `RESILIENCE: if ${H}/${b.slug}_verdicts_${b.start}.json already exists and is valid JSON, return its contents verbatim as {verdicts:[...]} (do NOT re-judge).\n`
  + `Otherwise read ${H}/${b.slug}_prefilter.json and take its "judge" array entries [${b.start},${b.end}) — ${b.end - b.start} entries of {login,repo,path,stars}.\n`
  + `For EACH entry READ its content: HEAD=140 python3 ${H}/peek.py <login> "<repo>|<path>"  (batch several "repo|path" specs per peek call).\n`
  + `Assign EXACTLY one verdict per entry: status found|needs_review|reject. On reject set reason ∈ {off-topic-workflow|off-topic-service|off-topic-tech|demo|project-doc|test-fixture|jvm-collection|boilerplate|vendored}. For found/needs_review set depth(0-3), jvm_fit(high/med/low), category(language/framework/tool/testing/build/data…), lines(int), notes. Follow the rules file (e.g. demo-repo is NOT itself a reason to reject; bare CLAUDE.md of run-commands = project-doc).\n`
  + `REASONING is REQUIRED on every verdict and must be specific (name what the skill does/teaches, the repo signal, why this bucket) — never a generic template.\n`
  + `WRITE the result to ${H}/${b.slug}_verdicts_${b.start}.json as {verdicts:[...]} and return the SAME object. Echo login/repo/path EXACTLY. If a peek fails, still return a verdict (reason="review").`,
  { label: `judge:${b.slug}[${b.start}-${b.end}]`, phase: 'Eval', schema: JUDGE_SCHEMA, model: JUDGE_MODEL })
  .then(r => ({ slug: b.slug, verdicts: (r && r.verdicts) || [] }))))).filter(Boolean)
const verdictsBySlug = {}
for (const j of judged) (verdictsBySlug[j.slug] ||= []).push(...j.verdicts)
const judgedCount = Object.values(verdictsBySlug).reduce((n, v) => n + v.length, 0)

// 4b-bundles) bundle-eval — one agent per conf evaluates its bundle candidates as UNITS (reads eval.md).
const bundleVerdictsBySlug = {}
await parallel(scanned.filter(c => (prepBySlug[c.slug] || {}).bundles).map(c => () => agent(
  `Evaluate SKILL BUNDLES for "${c.name}" — cohesive sets of dependent skills judged as ONE unit (a MORE extensive eval than per-file).\n`
  + `FIRST read the evaluation rules (esp. the bundle + workflow rules): ${EVAL_RULES}\n`
  + `Read the candidates: ${H}/${c.slug}_bundles.json — each has login, repo, root, members[].path (and copies in other repos).\n`
  + `For EACH candidate READ its members: HEAD=200 python3 ${H}/peek.py <login> "<repo>|<path>"  (batch the member paths; peek the repo README too if helpful).\n`
  + `Decide per candidate: cohesive (true if the members truly form ONE dependent suite/pipeline; false if they are unrelated skills merely sharing a dir), kind (jvm|workflow), status (found|needs_review|reject), a short bundle name (kebab slug), depth(0-3), and SPECIFIC reasoning naming what the suite does and why. A coherent, high-quality workflow suite CAN be status="found" with kind="workflow".\n`
  + `Return {verdicts:[{repo,root,cohesive,kind,status,name,depth,reasoning}…]} — echo repo & root EXACTLY for each candidate.`,
  { label: `bundle-eval:${c.slug}`, phase: 'Eval', schema: BUNDLE_EVAL_SCHEMA, model: 'sonnet' })
  .then(r => { const m = {}; for (const v of (r && r.verdicts) || []) m[`${v.repo}|${v.root}`] = v; bundleVerdictsBySlug[c.slug] = m })))

// 4c) adversarial recheck (RECHECK_MODEL, default Sonnet) — individual promotions only
const proms = []
for (const [slug, vs] of Object.entries(verdictsBySlug)) for (const v of vs) if (v.status === 'found' || v.status === 'needs_review') proms.push({ ...v, slug })
const bundleProm = Object.values(bundleVerdictsBySlug).reduce((n, m) => n + Object.values(m).filter(v => v.cohesive && (v.status === 'found' || v.status === 'needs_review')).length, 0)
log(`Judged ${judgedCount} files (+${bundleProm} bundle promotions); ${proms.length} individual promotions; ${RECHECK_MODEL} rechecking each.`)
// stable, short cache key per candidate (djb2 over login|repo|path) — lets a retry skip already-decided
// rechecks instead of re-hammering the recheck model (the batch-1 rate-limit storm left ~200 rechecks unresolved).
const djb2 = t => { let h = 5381; for (let i = 0; i < t.length; i++) h = ((h * 33) ^ t.charCodeAt(i)) >>> 0; return h.toString(36) }
const rcFile = s => `${H}/recheck_${s.slug}_${djb2(`${s.login}|${s.repo}|${s.path}`)}.json`
const rechecks = await parallel(proms.map(s => () => agent(
  `Adversarially verify ONE proposed skill-directory candidate. Default to keep=false unless it clearly passes.\n`
  + `RESILIENCE: if ${rcFile(s)} already exists and is valid JSON {keep,reason}, return its contents verbatim (do NOT re-verify).\n`
  + `Candidate: ${s.login}/${s.repo} :: ${s.path} — proposed status=${s.status}, category=${s.category || '?'}, claim: ${s.reasoning}\n`
  + `Read it: HEAD=400 python3 ${H}/peek.py ${s.login} "${s.repo}|${s.path}"\n`
  + `Keep ONLY a genuine, created, REUSABLE, JVM-specific skill in this person's OWN non-fork repo — not a bare project-doc, not vendored/forked, not boilerplate. `
  + `NOTE: living in a demo/workshop repo is NOT by itself a reason to drop a genuinely reusable skill. `
  + `WRITE your verdict to ${rcFile(s)} as {keep:boolean, reason:"<one line>"} and return the SAME object.`,
  { label: `recheck:${s.login}/${s.repo}`, phase: 'Eval', schema: RECHECK_SCHEMA, model: RECHECK_MODEL, effort: 'high' })
  .then(v => ({ key: `${s.slug}|${s.login}|${s.repo}|${s.path}`, keep: !v || v.keep !== false, reason: v && v.reason }))))
const dropReason = {}
for (const v of rechecks.filter(x => !x.keep)) { dropReason[v.key] = v.reason || ''; log(`  recheck dropped ${v.key.split('|').slice(1).join('/')}: ${v.reason || ''}`) }

// 4d) investigate — MED matches: deeper profile look vs the talk topic; record accept/reject for future runs.
await parallel(scanned.map(c => () => agent(
  `Investigate uncertain speaker→GitHub matches for "${c.name}" and record decisions for future runs.\n`
  + `FIRST read the matching rules: ${MATCH_RULES}\n`
  + `Read ${H}/${c.slug}_scout.json. For each resolution with confidence "MED", inspect its "cands" (login,name,company,bio,flw,orgs,jvm_repo) and judge whether the top candidate is really this conference speaker (a JVM-conference speaker with Java/Kotlin repos or a matching org/bio is almost certainly the right person).\n`
  + `For each MED you decide on, append ONE line to ${H}/${c.slug}_aliases_add.csv (create it; NO header) exactly: <norm_name>,<github_login>,<confirm|reject>,auto,"<short note>",${TODAY}\n`
  + `Return {decisions:[{norm_name,login,accept,reasoning}…]} (empty if there were no MEDs).`,
  { label: `investigate:${c.slug}`, phase: 'Eval', schema: INVESTIGATE_SCHEMA, model: 'sonnet' })
  .then(r => { for (const d of (r && r.decisions) || []) log(`  investigate ${c.slug}: ${d.accept ? '✓' : '✗'} ${d.norm_name} -> ${d.login}`) })))
// merge per-conf alias decisions into db/aliases.csv (serial, dedup-safe)
await agent(
  `Run: python3 ${H}/merge_aliases.py ${DBDIR}/aliases.csv ${scanned.map(c => `${H}/${c.slug}_aliases_add.csv`).join(' ')}\n`
  + `(missing add-files are skipped). It prints "aliases: +N new (M total)". Return {ok:true, note:"<that line>"}.`,
  { label: 'merge-aliases', phase: 'Eval', schema: STEP_SCHEMA, ...MECH })

// 4e) assemble per-conf overlays. The heavy skills[]/rejected[] arrays are reconstructed DETERMINISTICALLY
// from on-disk <slug>_verdicts_*.json by build_conf.py at apply time — here we only need the counts (for the
// run-note + final summary) and the SMALL deltas the verdicts can't carry: `drops` (adversarial recheck rejections)
// and bundle verdicts. This keeps the apply agent's payload tiny so large confs can't blow the 32k output cap.
const overlays = scanned.map(c => {
  const vs = verdictsBySlug[c.slug] || []
  const drops = {} // "login|repo|path" -> opus recheck reason; consumed by build_conf.py
  let nFound = 0, nNr = 0, nReject = 0
  for (const v of vs) {
    const key = `${c.slug}|${v.login}|${v.repo}|${v.path}`
    const isProm = v.status === 'found' || v.status === 'needs_review'
    if (isProm && !(key in dropReason)) {
      if (v.status === 'found') nFound++; else nNr++
    } else if (isProm) {
      drops[`${v.login}|${v.repo}|${v.path}`] = dropReason[key] || ''; nReject++
    } else {
      nReject++
    }
  }
  const bv = bundleVerdictsBySlug[c.slug] || {}
  const nb = Object.values(bv).filter(v => v.cohesive && (v.status === 'found' || v.status === 'needs_review')).length
  const run_notes = `${nFound} found, ${nNr} needs_review, ${nb} bundle(s), ${nReject} rejected. `
    + `LLM-judged every non-bundle hit; bundles evaluated as units.`
  return { slug: c.slug, drops, bundleVerdicts: bv, run_notes, nFound, nNr }
})

// ---------------- Phase 5: apply — SERIAL (shared CSV writes) ----------------
phase('Apply')
const applied = []
for (const o of overlays) {
  const c = bySlug[o.slug]
  // SMALL overlay only — build_conf.py reconstructs the heavy skills[]/rejected[] from on-disk verdicts.
  // (Previously the agent inline-wrote the full conf.json; for big confs that exceeded the 32k output cap
  //  and silently dropped them — jax/devoxxfrance/digitalcraftsday, batch 1.)
  const overlay = {
    conference: c.name, url: c.url, roster_fetched_at: TODAY, today: TODAY,
    drops: o.drops || {}, bundle_verdicts: o.bundleVerdicts || {}, run_notes: o.run_notes || '',
  }
  const r = await agent(
    `Apply conference "${c.name}" to the jvm-skills CSVs — three Bash steps, in order:\n`
    + `1. Write this SMALL JSON to ${H}/${o.slug}_overlay.json exactly:\n${JSON.stringify(overlay)}\n`
    + `2. python3 ${H}/build_conf.py ${o.slug} ${H}/${o.slug}_overlay.json ${H}/${o.slug}_conf.json\n`
    + `   (reconstructs the full conf.json from on-disk verdicts; prints a "skills=… rejected=…" summary line)\n`
    + `3. python3 ${H}/apply.py ${H}/${o.slug}_conf.json${DRY_APPLY ? ' --dry' : ''}\n`
    + (DRY_APPLY
      ? `(--dry renders the would-be CSVs without writing or self-validating.) Return {ok:true, validation:"DRY", note:"<the build_conf summary line>"}.`
      : `apply.py must print "VALIDATION PASS". Return {ok:true, validation:"PASS", note:"<the build_conf summary line>"} on PASS; `
        + `if it prints FAIL, return {ok:false, validation:"FAIL", note:"<the ragged/dup detail>"} and do NOT attempt to fix data.`),
    { label: `apply:${o.slug}`, phase: 'Apply', schema: APPLY_SCHEMA, ...MECH })
  applied.push({ slug: o.slug, ...(r || { ok: false, validation: '?' }) })
  if (!r || r.validation !== 'PASS') log(`  APPLY ISSUE ${o.slug}: ${r && r.validation} ${r && r.note}`)
}

// 5b) rule-refinement — let the eval LEARN: append general lessons to the rules files (git-tracked, auditable).
if (!DRY_APPLY) await parallel(overlays.map(o => () => agent(
  `Refine the skill-scout rule files from conference "${bySlug[o.slug].name}" results.\n`
  + `Read ${EVAL_RULES}. Inspect this run's outcomes in ${DBDIR}/skill_files.csv, ${DBDIR}/rejected.csv, ${DBDIR}/bundles.csv and note any judge↔recheck disagreements or surprising calls.\n`
  + `ONLY if you find a GENERAL, reusable lesson not already captured, prepend one or two concise dated bullets to the "Learnings changelog" of ${EVAL_RULES} (and/or ${MATCH_RULES} for matching lessons). Do NOT bulk-rewrite or delete existing rules; keep additions minimal and general.\n`
  + `Return {ok:true, added:<#bullets added>, note:"<what you added, or 'nothing new'>"}.`,
  { label: `refine:${o.slug}`, phase: 'Apply', schema: REFINE_SCHEMA, model: 'sonnet' })
  .then(r => { if (r && r.added) log(`  rules refined (${o.slug}): ${r.note || ''}`) })))

await agent(
  `Run: python3 ${H}/gen_candidates.py && python3 ${H}/gen_review_html.py — regenerate the human views. Return {ok:true}.`,
  { label: 'regen-views', phase: 'Apply', schema: STEP_SCHEMA, ...MECH })

const foundTotal = overlays.reduce((n, o) => n + (o.nFound || 0), 0)
const nrTotal = overlays.reduce((n, o) => n + (o.nNr || 0), 0)
const bundleTotal = overlays.reduce((n, o) => n + Object.values(o.bundleVerdicts || {}).filter(v => v.cohesive && (v.status === 'found' || v.status === 'needs_review')).length, 0)
log(`DONE. Conferences applied: ${applied.filter(a => a.validation === 'PASS').length}/${overlays.length}. `
  + `found=${foundTotal} needs_review=${nrTotal} bundles=${bundleTotal}. Validation issues: ${applied.filter(a => a.validation !== 'PASS').map(a => a.slug).join(', ') || 'none'}.`)

// ---------------- Phase 6: commit — opt-in, SCOPED to skill-scout outputs only ----------------
// Stages ONLY the files this workflow writes, aborts if anything else is staged (never sweeps up
// unrelated working-tree changes), and no-ops cleanly when there is nothing to commit.
const okSlugs = applied.filter(a => a.validation === 'PASS').map(a => a.slug)
if (AUTO_COMMIT && !DRY_APPLY && okSlugs.length) {
  phase('Commit')
  const msg = `skill-scout: batch — ${okSlugs.length} confs applied (found=${foundTotal} needs_review=${nrTotal} bundles=${bundleTotal})\n\n`
    + `Confs: ${okSlugs.join(', ')}.\n\n`
    + `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>\n`
    + `Claude-Session: https://claude.ai/code/session_01GCHca34hTGdUPtERGTuq6Z`
  const commitCmd =
    `git -C ${REPO} add skill-scout/db skill-scout/candidates.md skill-scout/review.html ${EVAL_RULES} ${MATCH_RULES} && `
    + `EXTRA=$(git -C ${REPO} diff --cached --name-only | grep -v '^skill-scout/' || true); `
    + `if [ -n "$EXTRA" ]; then git -C ${REPO} reset -q; echo "ABORT unexpected staged: $EXTRA"; exit 0; fi; `
    + `if git -C ${REPO} diff --cached --quiet; then echo "NOTHING_TO_COMMIT"; else `
    + `git -C ${REPO} commit -q -F - <<'MSGEOF'\n${msg}\nMSGEOF\n`
    + `echo "COMMITTED $(git -C ${REPO} rev-parse --short HEAD)"; fi`
  const r = await agent(
    `Run EXACTLY this one Bash command verbatim (it is a single command with a heredoc — run it as-is, do not modify, do not split):\n\n${commitCmd}\n\n`
    + `Then report what it printed. Return {ok:true, note:"<the COMMITTED.../NOTHING_TO_COMMIT line>"} on success, `
    + `or {ok:false, note:"<the ABORT... line>"} if it printed an ABORT line.`,
    { label: 'commit', phase: 'Commit', schema: STEP_SCHEMA, ...MECH })
  log(`  auto-commit: ${r ? r.note || (r.ok ? 'done' : 'failed') : 'no result'}`)
}

return {
  queued, harvested: harvestedCount, scanned: scanned.length,
  found: foundTotal, needs_review: nrTotal, bundles: bundleTotal,
  applied: applied.map(a => ({ slug: a.slug, validation: a.validation })),
  browserNeeded: browserNeededSlugs,
}
