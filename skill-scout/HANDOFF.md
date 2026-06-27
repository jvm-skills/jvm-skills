# skill-scout — Handoff (2026-06-27)

Self-contained handoff for the next session. **Assume no prior context.** Covers what batch 1
produced, what failed, the fixes now in place, and exactly how to continue + retry.

> Supersedes the original trial→execute handoff (the manual `speaker-scout-loop.md` validation plan);
> that loop is built and running as the Workflow below. Old version is in git history.

---

## TL;DR

- **Batch 1 done:** 24 of 75 queued JVM conferences scanned → judged → applied. DB now holds
  **451 skill files, 3 bundles, ~2.8k rejected, 1931 speakers** (24 runs). Committed in
  `c6b0b00` (fixes) + `0b6058c` (data) on branch `skill-scout-loop`.
- **Two known gaps from batch 1**, both rate-limit-driven — see [What failed](#what-failed).
- **Fixes are committed** so a rerun won't repeat them — see [Fixes in place](#fixes-in-place).
- **Next:** [Continue](#1-continue-batch-2--51-remaining-confs) (51 confs) and optionally
  [Reevaluate/retry](#2-reevaluate--retry-batch-1-rechecks) the rate-limited rechecks.

---

## How the pipeline works (1-paragraph primer)

`harness/overnight.workflow.js` is a Workflow script. Per conference it: **Harvest** roster
(WebFetch) → **Scan** GitHub for skill files (serial `scout.py`, throttled — GitHub core API is a
global mutex) → **Eval** (Haiku judges each file → Opus adversarially rechecks each promotion) →
**Apply** (serial upsert into `db/*.csv`, self-validating). All heavy intermediates are cached on
disk in `harness/` (gitignored) and agents self-skip when their cache file exists, so a relaunch
resumes cheaply. Run it with:
`Workflow({scriptPath: "<repo>/skill-scout/harness/overnight.workflow.js", args: {limit: 25, today: "<YYYY-MM-DD>"}})`

---

## What failed

1. **3 large confs failed to apply (RECOVERED).** `jax`, `devoxxfrance`, `digitalcraftsday` were
   fully scanned + judged, but the old Apply step asked the agent to inline-write a huge `conf.json`,
   which exceeded the 32k agent-output cap → the agent failed → those confs were silently dropped.
   **Already recovered** this session (re-applied deterministically from on-disk verdicts, all
   `VALIDATION PASS`) and the root cause is fixed. No action needed unless you re-derive them.

2. **~200 Opus rechecks failed on server-side rate-limiting (NOT recovered).** During the Eval tail
   the account hit sustained 429/"temporarily limiting requests". Rechecks that exhaust retries
   return `null`, which **fail-safes to `keep=true`** — so those promotions are in `skill_files.csv`
   **without** adversarial verification. Nothing was lost, but those rows are less-filtered than
   intended (some may be false positives Opus would have dropped). This is the main thing to
   **reevaluate** — see step 2 below. Affected candidates clustered around speakers such as
   `JohannesRabauer/*`, `jabrena/cursor-rules-*`, `marcoemrich/*`, `Grinseteddy/*`, `dyor/*`,
   `agoncal/*`, `brunoborges/gh-appmod`, `anishi1222/*`, `sshaaf/*`.

---

## Fixes in place (committed `c6b0b00`)

- **`harness/build_conf.py`** — reconstructs the heavy `skills[]`/`rejected[]` arrays
  deterministically from on-disk `<slug>_verdicts_*.json`. The Apply agent now writes only a tiny
  `<slug>_overlay.json` (Opus drops + bundle verdicts + meta) then runs `build_conf.py` + `apply.py`.
  **Per-conf size can no longer blow the output cap** (failure #1 cannot recur).
- **Opus recheck is now disk-cached** at `harness/recheck_<slug>_<hash>.json`. A rerun skips
  already-decided candidates instead of re-hammering Opus — so retrying failure #2 is cheap and
  won't re-trigger the storm.
- `.gitignore` updated for the new `*_overlay.json` / `recheck_*.json` / scratch artifacts.

> Note: batch 1 ran on the OLD code, so **no `recheck_*.json` files exist for batch 1 yet** — the
> first reevaluation pass (step 2) will create them.

---

## What to do next

### 1. Continue: batch 2 — 51 remaining confs

`queue.py` already excludes the 24 done confs; it returns **51 unscanned** (next up: `jalba`,
`javaone`, `voxxeddayszurich`, `confoo`, `fosdem`, …). Run in batches of ~25 to bound wall-clock and
rate-limit exposure:

```
Workflow({scriptPath: "<repo>/skill-scout/harness/overnight.workflow.js",
          args: {limit: 25, today: "<today>"}})
```

Run it twice more (limit 25, then the remainder) to clear all 51. The large-conf fix means no conf
will be dropped at apply time now.

**Monitoring** (learned the hard way): liveness = a running `scout.py` OR advancing
`harness/*_scout*.json` mtimes OR new `*_ckpt.json` during Scan; during Eval/Apply use the workflow
agent-transcript mtimes + growing `db/skill_files.csv`. Completion arrives as a task-notification.
Your monitoring checks run on the **same account** the workflow uses — if rate-limited, **back off to
~60-min checks** so you don't starve the run of token budget. Serial phases (Scan, Apply) tolerate
throttling and self-recover via retry; don't relaunch unless the transcript is stale >15-20 min AND
the runtime process is gone AND it's absent from `/workflows`.

### 2. Reevaluate / retry: batch-1 rechecks

Re-run **eval-only** over the 24 batch-1 confs. This reuses cached scout + judge verdicts (instant),
re-runs the Opus recheck (now cached as it goes) + apply (now deterministic + idempotent upsert), so
the ~200 unverified promotions finally get their adversarial pass and any false positives move to
`rejected.csv`.

```
# regenerate the evalOnly arg (24 confs) from the on-disk checkpoints:
python3 - <<'PY'
import json, glob, os
arr=[]
for f in sorted(glob.glob("skill-scout/harness/*_ckpt.json")):
    slug=os.path.basename(f).replace("_ckpt.json","")
    d=json.load(open(f)); arr.append({"slug":slug,"name":d.get("conference",slug),"url":d.get("url","")})
print(json.dumps(arr))
PY
# then:
Workflow({scriptPath: "<repo>/skill-scout/harness/overnight.workflow.js",
          args: {today: "<today>", evalOnly: <the array above>}})
```

This is an **Opus-heavy** pass (~451 rechecks). Do it when rate limits are healthy, or scope
`evalOnly` to the clustered confs above if cost is a concern. Because rechecks now cache, a second
pass after any further rate-limiting is cheap (only the still-uncached ones rerun).

---

## Deferred optimizations (NOT done — evaluate before batch 2 if desired)

- **Pipeline Scan→Eval→Apply per-conf** instead of three strict phases. Real but bounded win: it only
  overlaps eval's LLM *thinking* time under scan's rate-limit sleeps. **Caveat:** eval's `peek.py`
  (`gh api .../contents`) shares the **same GitHub core rate-limit bucket** as `scout.py`, so naive
  overlap splits the budget and can slow the long-pole scan. Worth doing carefully (keep scan serial
  via the existing mutex, kick a conf's eval on its checkpoint, keep apply serial), but it's a
  structural rewrite — don't bundle it with an unattended run.
- **Batch the Opus recheck** (one agent rechecks N candidates) to cut agent count / rate-limit
  pressure. Tradeoff: less per-candidate attention. Disk-caching (already added) covers most of the
  retry pain without this.

---

## Quick reference

| Thing | Where |
|---|---|
| Workflow script | `skill-scout/harness/overnight.workflow.js` |
| Deterministic conf builder | `skill-scout/harness/build_conf.py` |
| Apply / validation | `skill-scout/harness/apply.py` (`VALIDATION PASS` on success) |
| Queue of unscanned confs | `python3 skill-scout/harness/queue.py` |
| Eval rules (self-refining) | `skill-scout/harness/rules/eval.md`, `rules/matching.md` |
| DB (source of truth) | `skill-scout/db/*.csv` |
| Human views | `skill-scout/candidates.md`, `skill-scout/review.html` (regen: `gen_candidates.py`, `gen_review_html.py`) |
| Per-conf caches (gitignored) | `skill-scout/harness/<slug>_{speakers,scout,verdicts,bundles,ckpt,conf,overlay}*.json`, `recheck_*.json` |
