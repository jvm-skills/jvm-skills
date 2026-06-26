# Skill-Scout — full AFK run prompt

Paste everything below the line into a fresh Claude Code session (in the `jvm-skills` repo). It runs the
scout loop unattended across many JVM conferences. Trial data is archived under `skill-scout/trials/`;
the live `db/` starts empty except `conferences.csv`, which is pre-seeded with ~75 conferences (the
queue). The prompt below is ≤4000 chars — detail lives in the referenced docs.

---

You are running **skill-scout** unattended: find AI skills *created by* JVM-conference speakers (already in their own GitHub repos) for the jvm-skills directory. Work autonomously — do not ask questions. Checkpoint after each conference (the CSVs are the state). Stop when the queue is empty or budget runs low.

Read first, then follow them (don't rewrite): `skill-scout/speaker-scout-loop.md` (procedure, stages 0–5) and `skill-scout/db/README.md` (CSV store + reject taxonomy). Harness in `skill-scout/harness/`: `scout.py` (resolve + tree-scan + EXCLUDE), `apply.py` (upsert + auto-classify rejects + self-validate), `classify.py`, `peek.py` (read a skill's content), `gen_candidates.py` / `gen_review_html.py` (views). The queue is `db/conferences.csv` itself — rows with an empty `roster_fetched_at` are unscanned (pre-seeded; `apply.py` stamps the date when done).

Hard rules: only real, created skills (SKILL.md/AGENTS.md/CLAUDE.md/.cursorrules) in the speaker's own **non-fork** repo — no distilling, forks, or vendored skills. Resolution: auto-accept **HIGH only**; never accept an unvalidated top result; scan HIGH handles only (MED→manual queue, UNRESOLVED→parked). Tree-scan is authoritative (not code-search). Don't auto-promote to `skills/*.yaml` (human step). Don't commit.

Per conference (one per loop, full roster):
1. Pick the next `db/conferences.csv` row with empty `roster_fetched_at`; harvest its roster from its `url` → `[[name,affiliation],…]` JSON (aff="" if absent). Try WebFetch; **if it fails (JS / 403 / bad URL) use agent-browser** (`open` → `wait --load networkidle` → `snapshot -i -c`, extract names) — never skip to an easier conference. Save to `skill-scout/harness/<conf>_speakers.json`. (When no unscanned rows remain, append more JVM/Kotlin conferences 2024–26 to conferences.csv, else stop.)
2. `python3 skill-scout/harness/scout.py <conf>_speakers.json <conf>_scout.json` (throttles + dedupes + applies EXCLUDE; re-run a handle if a burst of empties = secondary rate limit).
3. Evaluate the residual real SKILL.md hits (the classifier auto-handles junk): `peek.py <login> "repo|path"`, then mark **found** (Depth≥2, ≈100+ lines of concrete, opinionated, JVM-specific guidance; not a demo/fork) or **needs_review** (borderline). Build `skill-scout/harness/<conf>_conf.json`: `{conference,url,roster_fetched_at,today,scout:"<abs path to scout json>",skills:[{login,repo,path,status,depth,jvm_fit,category,lines,notes,reasoning}],run_notes}`. `today` = real date; put `reasoning` on every promoted skill; `skills` = only found/needs_review (the rest auto-classify).
4. `python3 skill-scout/harness/apply.py <conf>_conf.json` — must print `VALIDATION PASS` (fix data + re-run if FAIL).
5. `python3 skill-scout/harness/gen_candidates.py && python3 skill-scout/harness/gen_review_html.py`. Loop.

Rate limits: search 30/min, code_search 10/min, core 5000/hr (separate buckets) — scout.py handles throttling. A suppressed 403 reads as "no results"; if a handle is unexpectedly empty, check `gh api rate_limit` and re-run it.

When done: regenerate the views and summarize — conferences covered, cumulative HIGH/MED/UNRESOLVED, new found + needs_review (with repos), the size of the needs-classification queue (`rejected.csv` reason=`review`), and any rate-limit/harvest issues. The human reviews `review.html` and promotes to `skills/*.yaml`.
