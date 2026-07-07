---
name: skill-scout
description: Run the skill-scout loop — scan the next batch of unscanned JVM-conference rosters for speaker-created AI skills and apply results to the CSV store via the overnight Workflow. Use when the user says "run skill-scout", "continue the skill-scout loop", "scan more conferences", or wants to grow the skill candidate list.
invocation: user
---

# Run skill-scout

Launch the skill-scout loop over the unscanned conference queue. Full design + pipeline:
`skill-scout/README.md`. Invoking this skill **is** the explicit opt-in to run the Workflow.

## Steps

1. **Today's date.** Use the real current date as `YYYY-MM-DD` (it stamps the CSVs — never hardcode).

2. **Check the queue.**
   ```bash
   python3 skill-scout/harness/queue.py | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['confs']),'unscanned'); [print(' ',c['slug']) for c in d['confs'][:30]]"
   ```
   If **0 unscanned**: the queue is empty — tell the user to append fresh JVM/Kotlin conferences
   (2024–26) to `skill-scout/db/conferences.csv`, or stop. Do not fabricate conferences.

3. **Launch the Workflow** (one batch, self-committing):
   ```
   Workflow({
     scriptPath: "/Users/tschuehly/IdeaProjects/jvm-skills/skill-scout/harness/overnight.workflow.js",
     args: { limit: 25, today: "<today>", autoCommit: true }
   })
   ```
   - `limit: 25` covers a full batch (the tested size); pass a smaller `limit` for a quick run.
   - `autoCommit: true` makes ONE scoped commit at the end (only `skill-scout/db`, `candidates.md`,
     `review.html`, `rules/*.md`; aborts if anything else is staged). Omit it if the user wants to
     review `review.html` before committing.
   - It runs in the background; a task-notification fires on completion.

4. **On completion, report the delta** from the result JSON: `found` / `needs_review` / `bundles`,
   the per-conf `validation` (must be `PASS`), and `browserNeeded` (confs whose roster needed the
   agent-browser fallback and may warrant a re-run). Then point the user at `skill-scout/review.html`
   — the human reviews it and promotes rows into `skills/*.yaml` (see top-level `CONTRIBUTING.md`).

## Options (pass in `args` when asked)

| Want | Arg |
|---|---|
| Higher-rigor adversarial recheck | `recheckModel: "opus"` (slower/pricier; delete stale `harness/recheck_*.json` first — the cache is model-blind) |
| Dry run (no CSV writes) | `dryApply: true` |
| Specific conference(s) only | `slugs: ["<slug>", …]` |
| Re-judge from cached scans (no re-scan) | `evalOnly: [{slug,name,url}, …]` |

## Notes

- One conference is the unit of work; the `db/*.csv` files are the state. A relaunch resumes cheaply
  from the per-conf caches in `harness/` (gitignored), so an interrupted run is safe to re-launch.
- A full-queue run is long (serial GitHub scan, ~15 min/conf) — it's meant to run AFK. Monitor with
  `/workflows`; serial phases self-recover from GitHub rate-limiting.
