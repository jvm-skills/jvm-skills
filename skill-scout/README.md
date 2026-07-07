# Skill-Scout

Find AI skills **created by JVM/Spring conference speakers** — a real `SKILL.md` / `AGENTS.md` /
`CLAUDE.md` / `.cursorrules` file in the speaker's own **non-fork** repo — and maintain a reviewable
candidate list for the [jvm-skills](https://jvmskills.com) directory.

**Scope:** only *existing, created* skills. Never distill a skill from a blog/docs; never list forks or
vendored third-party skills. A speaker with no published skill file is not a candidate (they stay parked
in `resolutions.csv` and get re-checked later).

The pipeline resolves each speaker → GitHub, tree-scans their repos for skill files, LLM-judges every
hit, adversarially rechecks each promotion, and upserts the result into the `db/*.csv` store.

---

## How to run (canonical)

The loop is a single **Workflow** script — `harness/overnight.workflow.js`. It orchestrates every stage
per conference across many subagents and checkpoints to disk, so a relaunch resumes cheaply.

```
Workflow({
  scriptPath: "/Users/tschuehly/IdeaProjects/jvm-skills/skill-scout/harness/overnight.workflow.js",
  args: { limit: 25, today: "YYYY-MM-DD" }
})
```

> Running a Workflow spawns dozens–hundreds of agents and hits the GitHub API hard. It is **opt-in**:
> only launch it when the user has asked to run/continue the loop.

**Args** (all optional):

| Arg | Default | Meaning |
|---|---|---|
| `today` | `2026-06-26` | run date, stamped into the CSVs — **always pass the real date** |
| `limit` | `999` | max conferences to scan this run (batches of ~25 are the tested size) |
| `slugs` | — | explicit slug allowlist, e.g. `["javazone"]`, to run/resume specific confs |
| `recheckModel` | `sonnet` | adversarial-recheck model; pass `"opus"` for a high-stakes pass |
| `judgeModel` | `haiku` | bulk per-file judge model |
| `evalOnly` | — | `[{slug,name,url}]` to re-judge from cached `*_scout.json` (no re-scan) |
| `dryApply` | `false` | `apply.py --dry` — render without mutating the CSVs |
| `autoCommit` | `false` | opt-in: final step commits ONLY skill-scout outputs |
| `maxSpeakers` | `0` | per-conference speaker cap (small trials); 0 = full roster |

**The queue** is `db/conferences.csv` itself: rows with an empty `roster_fetched_at` are unscanned.
`python3 harness/queue.py` emits the unscanned set with deterministic slugs. When the queue empties,
append fresh JVM/Kotlin conferences (2024–26) to `conferences.csv` and rerun, or stop.

---

## Pipeline (what the Workflow does per conference)

1. **Load queue** — `queue.py` → unscanned confs + deterministic slugs.
2. **Harvest** — `WebFetch` the roster → `<slug>_speakers.json` (`[[name,affiliation],…]`). If the page
   is JS-rendered / 403s, fall back to **agent-browser** (`open` → `wait --load networkidle` →
   `snapshot -i -c`) — never skip to an easier conference (it biases the corpus).
3. **Scan** — `split_speakers.py` chunks the roster (≤22/chunk); `scout.py` resolves each speaker and
   tree-scans their non-fork repos for skill files. **Serial** — the GitHub core API is a global mutex.
   `merge_scout.py` recombines chunks → `<slug>_scout.json`.
4. **Eval** —
   - `bundle_detect.py` clusters numbered pipelines (e.g. `01-spec…06-execute`) into **bundles** judged
     as one unit; `prefilter.py` splits hits into cheap-skip vs judge.
   - **Judge** (Haiku): one verdict per skill file → `found` / `needs_review` / `reject` (+ taxonomy
     reason), reading content via `peek.py`.
   - **Recheck** (Sonnet, adversarial): every promotion is re-verified; drops are recorded.
   - **Investigate** MED matches; **bundle-eval** each canonical bundle.
5. **Apply** — a small overlay + on-disk verdicts → `build_conf.py` assembles the full `conf.json`
   (keeps large-conf payloads under the 32k output cap) → `apply.py` upserts every CSV by natural key
   and **self-validates** (`VALIDATION PASS`/`FAIL`). Stamps `roster_fetched_at`, appends a `runs.csv`
   ledger row, regenerates the views.
6. **Commit** (opt-in) — commits only skill-scout outputs.

Heavy intermediates (`<slug>_{speakers,scout,verdicts,bundles,ckpt,conf,overlay}*.json`,
`recheck_*.json`) are cached in `harness/` (gitignored); agents self-skip when their cache exists.

---

## Layout

| Path | What |
|---|---|
| `harness/overnight.workflow.js` | **the loop** (v3 Workflow orchestration) |
| `harness/*.py` | stage tools: `queue`, `split_speakers`, `scout`, `merge_scout`, `bundle_detect`, `prefilter`, `peek`, `build_conf`, `apply`, `classify`, `merge_aliases`, `gen_candidates`, `gen_review_html`, `reset_run` |
| `harness/rules/eval.md` | self-refining judge rules (agents read before judging; refinement agent appends learnings) |
| `harness/rules/matching.md` | self-refining speaker→GitHub matching rules |
| `db/*.csv` | **system of record** (see `db/README.md` for schema + reject taxonomy) |
| `db/aliases.csv` | confirmed/rejected speaker→login decisions (human + learned memory) |
| `candidates.md`, `review.html` | generated human views (regenerated each run; do not edit by hand) |
| `trials/` | archived supervised-trial snapshots (historical record) |

---

## Design decisions (why it works this way)

- **Tree-scan is authoritative, not code-search.** `gh search code --owner` has unacceptable recall — it
  returned 0 for speakers who actually shipped 13★/14★ skill repos (it skips forks, subdir files, and
  unindexed repos). Scan = `users/<h>/repos` (non-fork, top ~30 by pushed) → `git/trees?recursive=1`.
- **Throttle the tree-scan (~0.7s/call).** Bursts trip GitHub's *secondary* rate limit → false "0 repos".
  A suppressed 403 reads as "no results" — sanity-check against a known-positive before trusting empties.
- **Resolution auto-accepts HIGH only.** HIGH = name match AND (roster affiliation appears in the
  candidate's GitHub `company`/`bio`, **or** one dominant name-match: non-empty company + followers ≫
  runner-up ≈3×). MED → investigate/manual; UNRESOLVED → parked. Never auto-accept an unvalidated top
  result (blocks e.g. `Josh Rickard`←`Josh Long`, `jean-developer`←`Arnaud Jean`). Matching signal is
  the candidate's own GitHub profile — no external lookup.
- **Verify by reading.** A search hit alone is never enough (spike precision ≈ 15%); every promotion is
  read and then adversarially rechecked.
- **Bundles are one unit.** A numbered pipeline copied across an author's repos is listed once
  (most-complete non-demo copy = canonical), not per step.
- **CSV, not a DB.** The dataset is small (hundreds of rows) and the repo values reviewable, diffable
  text; upsert-by-natural-key is a few lines of Python. Query ad-hoc with DuckDB-over-CSV or awk.
- **Re-fetch is cheap.** `repos.csv` stores `head_sha`/`last_scanned_at` (skip unchanged repos);
  `resolutions.csv` `recheck_after` retries UNRESOLVED/MED later. Most speakers have no skill *today* but
  may publish later — the store exists so re-scans avoid rework.

---

## Continue / resume / monitor

- **Continue:** `python3 harness/queue.py` shows what's unscanned; launch the Workflow with
  `limit` + the real `today`. Rerun in batches until the queue empties.
- **Resume an interrupted conference:** relaunch with `slugs:["<slug>"]` — cached
  `*_speakers.json`/`*_scout.json` are reused, so it picks up mid-pipeline.
- **Monitor:** liveness = a running `scout.py`, advancing `harness/*_scout*.json` mtimes, or new
  `*_ckpt.json` during Scan; during Eval/Apply, growing `db/skill_files.csv`. Completion = the
  task-notification. Serial phases self-recover from throttling — don't relaunch unless the transcript is
  stale >15–20 min AND the process is gone AND it's absent from `/workflows`.
- **Recheck cache is model-blind:** `recheck_*.json` keys on candidate identity, not model. To force an
  Opus recheck to actually re-decide, delete the relevant `recheck_*.json` first.

## Hard rules

- Only real, created skills in the speaker's own non-fork repo. No distilling, forks, or vendored skills.
- Auto-accept HIGH resolutions only; tree-scan is authoritative; verify by reading.
- Don't auto-promote CSV rows into `skills/*.yaml` — that's the human review step (see the top-level
  `CONTRIBUTING.md`). The human reviews `review.html` and promotes rows they like.
- One conference is the unit of checkpointing; the CSVs are the state.
