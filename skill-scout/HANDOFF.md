# Handoff — Speaker-Scout Loop: trial → execute

**What this is:** a validated loop that finds AI skills *created by conference speakers* (resolve speaker
→ GitHub via user search → scan repos for skill files → evaluate). Run the **TRIAL** first; only proceed to
**EXECUTE** if the gates pass.

## Files
| File | Role |
|---|---|
| `loop-design.md` | Design, Mermaid diagrams, trial results, **v3** decisions, DB + re-fetch |
| `speaker-scout-loop.md` | **The runnable procedure** (v3). Feed this to the agent |
| `db/*.csv` + `db/README.md` | System of record (git-tracked CSV; `candidates.md` is generated from it) |
| `candidates.md` | **Generated** human view (Found / Needs-review / Parked / Rejected) |
| `candidates.trial.md` | Phase-1 (Spring I/O) trial results |
| `HANDOFF.md` | This plan |

## Status (validated 2026-06-26)
- **v3 passes the critical gates on fresh data.** Phase-1 (Spring I/O, 15) failed gates #2/#3 and exposed
  two bugs (code-search recall; name-only false positives) → fixed in v3 (tree-scan primary + throttle;
  auto-accept HIGH only). Re-trial on 8 **fresh Devnexus** speakers: **0 false-positive auto-accepts**
  (a wrong "Phil Webb" was correctly routed to MANUAL, not accepted); throttled tree-scan clean.
- **Known residual gaps (safely handled):** affiliation false-negatives downgrade correct people to MANUAL;
  name variants (Kenneth/Ken) → UNRESOLVED; **rosters without affiliations** (Devnexus) need an
  affiliation-enrichment step before the HIGH gate can fire. None cause bad auto-accepts.
- **State is git-tracked CSV** (`db/*.csv`); the loop upserts by natural key and supports cheap re-fetch.

---

## Phase 1 — TRIAL (do this first)

**Scope:** Spring I/O 2026, **first 15 speakers only** (alphabetical from the roster).

**Steps:** run `speaker-scout-loop.md` stages 1–5 on those 15. Write results to a scratch copy
(`candidates.trial.md`), **not** the real artifact yet.

**Acceptance gates (ALL must pass):**
1. **Resolution recall ≥ 70%** — ≥ 11/15 resolved to a handle (rest legitimately UNRESOLVED, not wrong).
2. **Zero false-positive resolutions** — spot-check 5 resolved handles by hand; none may be the wrong person.
   *(This is the critical gate — a wrong handle silently poisons the scan.)*
3. **Scan correctness** — re-run the batched code-search and confirm it agrees with a REST tree-scan on
   1 resolved handle (no false "0 skills").
4. **Artifact hygiene** — every speaker lands in exactly one bucket (Found/Needs-review/Parked/Rejected);
   no dupes vs `skills/**/*.yaml`; run-log row written.

**If a gate fails:** stop, report which gate + sample failures, adjust `speaker-scout-loop.md`, re-trial.
Do **not** proceed to EXECUTE on a failed trial.

---

## Phase 2 — EXECUTE (only after TRIAL passes)

1. Run the loop on **all ~85 Spring I/O 2026 speakers** (batches of ~20 for the scan; checkpoint
   `candidates.md` between batches; respect rate-limit polling).
2. Mark Spring I/O `[x]`; write the run-log row.
3. Pop the **next conference** from the Arm-A queue (Devoxx Belgium, JavaLand, …) and repeat.
4. Stop when the queue is empty, or on user request.

**Expected yield (set expectations):** based on the trial + earlier scans, *individual speakers rarely
ship skills* — most will Park. Value = exhaustive, deduped coverage + the occasional high-authority hit.
If after 2 full conferences the Found count is ~0, surface that and reconsider whether Arm B (topic
skill-file search) deserves priority over more rosters.

## How to run
- **Inline (recommended for control):** execute `speaker-scout-loop.md` stage by stage in this session.
- **Delegated:** spawn one agent per conference with `speaker-scout-loop.md` as the prompt; fan speakers
  into sub-batches. (Larger fan-outs = a Workflow; opt-in/cost-gated.)

## Guardrails
- **Never accept an unvalidated top search result** — require name- or affiliation-match (stage 2 gate).
- **Verify skills by reading** — never list on a search hit alone.
- **Park, don't guess** — unresolved/pseudonymous/no-skill → watchlist, never a fabricated candidate.
- **Watch rate limits** — poll `gh api rate_limit` before each code-search batch.
