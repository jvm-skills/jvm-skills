# Speaker-Scout Loop — runnable procedure (v2)

Find AI skills **created by conference speakers**. Resolve each speaker → GitHub via user search,
scan all their repos for skill files, evaluate, record. **Only existing created skills — no distilling.**
Design + trial rationale: `loop-design.md`. Output/state: `candidates.md`.

Run **one conference per invocation**; fan speakers out in batches. Stop when the conference queue is empty.

## 0. Load state (from `db/*.csv` — see `db/README.md`)
- `EXCLUDE` = repos already in `skills/**/*.yaml` (`grep -hE '^repo:' skills/**/*.yaml`). **`scout.py`
  auto-loads this** and flags re-found hits as `already-listed` so they are never re-promoted.
- `seen` speakers = `norm_name` column of `speakers.csv`; `seen` repos = `(login,name)` of `repos.csv`.
  The CSVs are the dedupe authority — never re-resolve a `norm_name` already present, never re-walk an
  unchanged repo (see §3 re-fetch). `candidates.md` is a generated view, not state.
- Pick the next conference: a `conferences.csv` row with empty `roster_fetched_at`, or one whose speakers
  are due (`resolutions.csv` `recheck_after <= today`).

> **Runnable harness** (in `skill-scout/harness/`): `scout.py` (resolve + tree-scan
> + EXCLUDE → JSON), `apply.py` (idempotent CSV upsert + auto-classify rejects + self-validate),
> `classify.py` (reject taxonomy), `gen_candidates.py` (regenerate the view). Feed `scout.py` a
> `[[name,aff],…]` JSON, eval the hits, then `apply.py <conf.json>`.

## 1. Harvest speakers
`WebFetch` the roster page → `[ {name, affiliation} ]`. Keep affiliation — it's the key disambiguator.
- **If `WebFetch` fails** (JS-rendered roster, 403/bot-block, wrong-but-guessed URL) **do not fall back to
  an easier conference** — that biases the corpus toward simple sites. Render it with **`agent-browser`**:
  `agent-browser open <url>` → `wait --load networkidle` → `snapshot -i -c`, then extract the speaker
  headings/cards. (This is how GeeCON — a hard 403 for WebFetch — was harvested.)

## 2. Resolve GitHub — v2 cascade (per speaker, skip if in `seen`)
```bash
# 1) exact fullname  → 2) accent-stripped  → 3) broad
gh api -X GET search/users -f q="$NAME in:fullname" -f per_page=5 --jq '.items[].login'
#   if empty: q="$(echo "$NAME" | iconv -f utf-8 -t ascii//TRANSLIT) in:fullname"
#   if empty: gh search users "$NAME" --json login --limit 5 --jq '.[].login'
# enrich each candidate:
gh api "users/$LOGIN" --jq '[.login,(.name//"-"),(.company//"-"),(.bio//"-"),(.followers|tostring)]|@tsv'
```
**Affiliation signal = the candidate's own GitHub `company`/`bio`** (no external lookup — decided).
First require a **name match**: GitHub `name` contains the speaker's **first AND last** token. Then classify:
- **HIGH (auto-accept):** a name match where **either** (a) the roster affiliation (when present) appears
  in the candidate's `company`/`bio`, **or** (b) there is **one clearly dominant** name-match — its
  `company` is non-empty *and* its `followers` exceed the runner-up name-match by a wide margin
  (≈3×, min ~50). Pick that candidate.
- **MED (manual-confirm, NOT auto-scanned):** name match but no affiliation match and **no dominant
  winner** (no `company`, low followers, or several comparable same-name profiles). *(Trial: the only
  FP — `jean-developer` ← Arnaud Jean — and the correct-but-downgraded `danvega` (employer not on
  GitHub) both land here. Safe: a human confirms.)*
- **UNRESOLVED (park):** no name match, or no hits (fully-anonymous profile). *(Pseudonymous **handles**
  like `HanSolo` still resolve — they have the real name in the profile.)*
- **Never auto-accept an unvalidated top result** (blocks `Josh Rickard`←`Josh Long`, `jean-developer`←`Arnaud Jean`, wrong `prwebbuk`←`Phil Webb`).
  *(Optional rare recovery for a high-value name: read the speaker page for a GitHub/X/blog link.)*

## 3. Scan resolved (HIGH) handles for skill files — REST tree-scan (PRIMARY)
Code-search `--owner` is **not** reliable here (trial: it returned 0 for speakers who actually had 13★/14★
skill repos — it skips forks, subdir files, and unindexed repos). **Use the tree-scan:**
```bash
# list owned, non-fork repos (top ~30 by pushed), then walk each tree — THROTTLED
gh api "users/$H/repos?per_page=100&sort=pushed&type=owner" \
  --jq '.[]|select(.fork==false)|[.name,(.stargazers_count|tostring)]|@tsv'        # take first 30
# per repo (sleep ~0.7s between calls to dodge the secondary rate limit):
gh api "repos/$H/$R/git/trees/HEAD?recursive=1" \
  --jq '.tree[].path|select(test("(^|/)(SKILL\\.md|AGENTS\\.md|CLAUDE\\.md|\\.cursorrules)$";"i"))'
```
- **Throttle** ~0.7s between tree calls. A burst of empties usually means the **secondary rate limit**
  tripped (false "0 repos") — back off and re-scan, don't trust the empty.
- Exclude **forks** (skills copied from upstream aren't "created by them").
- Primary rate limits: `core` bucket = 5000/hr (plenty); poll `gh api rate_limit` if unsure.
- **Incremental re-fetch:** for a repo already in the DB, compare its current HEAD `sha`/`pushed_at`
  (`gh api repos/$H/$R --jq .pushed_at` or `.../commits/HEAD --jq .sha`) to the stored `head_sha`/
  `last_scanned_at`. **Skip the tree walk if unchanged.** Only walk new or changed repos; bump
  `skipped_repos` in the run ledger for the rest.

## 4. Evaluate each skill file found
**First filter out non-skills** (trial showed these dominate the raw hits):
- **Demo/talk/workshop** repos (name or path contains `demo`, `workshop`, `sample`, `playground`, a
  conf+year like `voxxeddays2026`, or example skills like `ai-tutor`/`pdf`/`travel-planner`) → Reject.
- **Boilerplate templates** duplicated across repos (e.g. the `01-spec`…`06-execute` SDD set) → list the
  canonical repo once, reject the copies.
- Bare `CLAUDE.md`/`AGENTS.md` that is just project instructions, not a reusable skill → Reject.

Then fetch content (`gh api repos/$R/contents/$PATH --jq '.content' | base64 -d`) and score:
- **Depth** 0–3: lines of concrete, opinionated, JVM-specific guidance (≈100+ lines is a good sign;
  trial Found ranged 107–423 lines). Reject "use best practices" stubs.
- **JVM-fit:** java / kotlin / spring / jooq / jpa / testcontainers / quarkus / micronaut / ktor / gradle…
- **Authority:** stars + speaker's followers + org-verified.

## 5. Record into the CSVs (no silent drops) — upsert by natural key (`apply.py`)
For each row, check the key (`speakers.norm_name`, `repos.(login,name)`, `skill_files.(login,repo,path)`):
update in place if present, else append. Write to:
- `speakers.csv` (+ `speaker_conferences.csv` link), `resolutions.csv` (login, confidence, followers,
  `recheck_after` for UNRESOLVED/MED), `repos.csv` (stars, `pushed_at`, `head_sha`, `last_scanned_at`),
  `skill_files.csv`.
- **`skill_files.csv` = promoted only** — `found` (Depth ≥ 2, JVM-relevant) · `needs_review` (borderline).
  Fill `depth`, `jvm_fit`, `category`, `lines`, `notes`. Quote any comma field (RFC-4180), e.g. `"Code Monkey, LLC"`.
- **`rejected.csv` = every other scanned hit**, auto-classified by `classify.py` (`apply.py` does this — no
  manual rejects). `reason` ∈ `jvm-collection｜off-topic-workflow｜off-topic-service｜off-topic-tech｜demo｜
  boilerplate｜vendored｜project-doc｜test-fixture｜already-listed｜review`. The `off-topic-*` rows are the
  reviewable "real but non-JVM" skills; `jvm-collection` are promote-worthy members of a found collection.
- Resolved-but-no-skill and UNRESOLVED stay in `resolutions.csv` (parked).
Then:
- Set `roster_fetched_at` in `conferences.csv`; append a **`runs.csv` ledger** row.
- `apply.py` **self-validates** after writing (re-parses every CSV: column counts + duplicate natural keys
  → `VALIDATION PASS/FAIL`).
- **Regenerate `candidates.md`** from the CSVs (`gen_candidates.py`).
- Stop.

## Re-fetch mode (run periodically)
Same procedure, but stage 0 selects speakers whose `recheck_after` has passed and repos already in the DB.
Stage 2 re-resolves only UNRESOLVED/MED-due speakers; stage 3 skips repos whose HEAD is unchanged. Cheap:
a quiet speaker costs one repo-list call and zero tree walks. New skills surface as new `skill_file` rows.

## Stop / loop control
- One conference per run. Stop when `Arm A` queue has no `[ ]` left.
- Within a run, if a speaker batch is large, process in chunks of ~20 and checkpoint the artifact between chunks.
