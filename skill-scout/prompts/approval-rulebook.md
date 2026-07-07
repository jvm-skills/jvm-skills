# Prompt — jvm-skills Approval Rulebook + Strict Candidate Review

Paste everything below into a **fresh** Claude Code session opened at the repo root
(`/Users/tschuehly/IdeaProjects/jvm-skills`). Run it with the **strongest available model
(Opus) at high/max reasoning effort** — the judging step depends on it. It is self-contained; it
assumes no prior context.

---

You have two jobs, done in order:

1. **Derive the Approval Rulebook** — the minimum requirements and judgment criteria that decide
   whether a skill is "jvm-skills approved."
2. **Apply it to every candidate** — group, label, and strictly judge each surfaced candidate with a
   smarter model, then **deduplicate overlapping skills and choose the single best of each group.**

jvm-skills (jvmskills.com) is a curated directory of AI coding skills for JVM developers. This is a
**synthesis + review task**, not a promotion task: produce the two deliverable documents, but do
**not** add/edit/promote/reject anything in `skills/` or the databases. Read-only everywhere except
the two deliverable files.

## The core philosophy (north star — every rule and verdict serves it)

From `README.md`: *"jvm-skills only lists skills that teach the AI something it wouldn't know on its
own."* Named anti-pattern: the most-installed Spring Boot skill elsewhere has 9.8K installs and just
says "use Spring Boot best practices" — that is **not** a skill, because Claude already does that.
Governing test for everything below: **does this skill deliver concrete, opinionated, reusable JVM
expertise an AI wouldn't otherwise have — and is it the best available version of that skill?**

## Read these first, in this order (know what each is and how much to trust it)

1. **`README.md`** — mission, the philosophy above, the 8 categories (framework, language, database,
   testing, fullstack, web, workflow, tool) and their scopes.
2. **`CONTRIBUTING.md`** — the listing YAML schema (required vs optional), and the three **trust
   levels**: `official` (library/tool maker), `curated` (vetted expert), `community` (PR).
3. **`skills/**/*.yaml`** — the **31 currently-approved listings** = today's bar. NOTE: these are
   *listings* (metadata), each pointing to a `repo` + often a `skill_path`. The metadata is NOT the
   bar — the referenced **SKILL.md content is.** Open and read a representative sample across every
   category (~8–12 real SKILL.md files, incl. the `curated`/`official` ones — jOOQ, kotest, jspecify —
   as gold-standard PASS exemplars).
4. **`skill-scout/harness/rules/eval.md`** — the richest source: a dated, field-tested taxonomy of
   `found`/`needs_review`/`reject` decisions with concrete named examples and a reject-reason
   vocabulary, distilled from ~75 conferences. **Consolidate it — do not copy it.** Most entries are
   variations on a few deep principles (extractability, "JVM fit must be the subject not an accident",
   structural disqualifiers). Critically, its changelog shows the cheap scanner judge **over-promotes**
   and the Opus recheck rejects a large fraction — your Phase-2 judge must be that strict Opus recheck.
5. **The candidate set** (your review input):
   - `skill-scout/db/skill_files.csv` — the promotable pile: rows with `status=found` (and
     `needs_review`). Columns include owner, repo, path, depth, jvm_fit, category, line count, reasoning.
   - `skill-scout/review.html` — the human-review view of the same.
   - `skill-scout/db/rejected.csv` — the reject taxonomy in practice (reason + reasoning); mine it for
     real FAIL examples.

Use the **Explore** subagent and parallel reads to cover the 31 listings and candidate repos
efficiently. Fetch external GitHub content with `gh api` / `gh` or WebFetch — `skill_files.csv` gives
`owner/repo/path`. **Always read the actual SKILL.md body before judging — never judge from the CSV
reasoning field alone** (eval.md documents that field being wrong repeatedly).

---

## PHASE 1 — Derive the Approval Rulebook

Write **`docs/skill-approval-rulebook.md`** (create `docs/` if needed): a standalone document a new
reviewer can apply cold, without having read `eval.md`. Sections:

1. **Purpose & philosophy** — one tight paragraph; state the "teaches the AI something it wouldn't
   know" test as governing.
2. **Hard minimum requirements** — objective, checkable gates a skill must pass *all* of. Derive from
   what every approved skill shares and what eval.md's structural rejects forbid. At minimum pin down:
   authored by the submitter in their own non-fork repo; concrete + opinionated (not a stub, manifesto,
   or "use best practices"); a real depth/substance floor (define by *content*, not just line count —
   eval.md's rough line is Depth ≥ 2 / ~100+ lines); **self-contained / extractable** (droppable into a
   *different* project without transplanting numbered sibling files, framework state, companion
   reference docs, or machine-local paths); APIs that actually exist (no hallucinated
   classes/methods/packages); correct, complete listing metadata per CONTRIBUTING.
3. **Quality judgment criteria** — the softer bar separating strong from borderline, plus tie-breakers.
   Include the decisive eval.md tests: **"JVM fit must be the subject, not an accident"** (could this be
   lifted verbatim into a Python/JS project unchanged? → off-topic) and the extractability test. Define
   when `needs_review` is right vs a direct reject.
4. **Automatic disqualifiers (rejection taxonomy)** — consolidate every reject reason into a clean
   list; for each give a one-line *test* + one *real* example (cite an actual repo/file from
   `rejected.csv` or `eval.md`). Cover at least: `demo`, `project-doc`, `vendored`, `test-fixture`,
   `boilerplate`, `off-topic-tech`, `off-topic-workflow`, `off-topic-service`, `hallucinated-api`,
   personal-manifesto/philosophy, event-specific, machine-local-paths, framework/pipeline-coupling,
   and bundle handling (numbered pipeline steps = evaluate as a unit).
5. **Category & trust-level guidance** — how to pick the category; what each trust level means and who
   assigns it; the `workflow`-category carve-out (a coherent high-quality agentic-workflow *bundle* may
   list; a single thin workflow step may not).
6. **Deduplication & "best in class" policy** — the rule Phase 2 will apply (see below), stated as
   policy: when multiple skills teach substantially the same thing, **only the best one is listed.**
   Define "substantially the same" (same technique/topic/framework surface) and the ranking criteria
   for picking the winner (see Phase 2 tie-breakers). Include the single-promotion / canonical-source
   principle from eval.md (a copied skill is listed once, at its canonical repo).
7. **Reviewer decision procedure** — a numbered, do-this-in-order checklist per candidate: cheapest
   structural disqualifier checks first → extractability → JVM-fit → depth/quality → dedup vs the
   candidate set and existing listings → metadata → verdict.
8. **Worked examples** — 3–5 **PASS** (real approved skills, with why) and 6–8 **FAIL** (real rejected
   rows, naming the rule that kills each).

Grounding rules: **every rule cites a real example from this repo** (approved skill or rejected row —
no invented cases); prefer objective/checkable phrasing; keep it self-contained.

---

## PHASE 2 — Group, label, judge, deduplicate, choose the best

Apply the Phase-1 rulebook to the candidate pile (`status=found`, then `needs_review`) and produce
**`docs/candidate-review.md`**. Judge **strictly** — this is the adversarial Opus-recheck gate, not
the lenient scanner judge. Default posture: a candidate must *prove* it deserves listing; when
genuinely uncertain, `needs_review`, not `approve`.

Do it in these steps:

1. **Group into clusters.** Cluster candidates by what they actually teach (topic + framework/tool
   surface), across all owners/repos — e.g. "Java best-practices", "Spring Boot", "JUnit/testing",
   "Clojure REPL tooling". A cluster may hold one candidate or many. Also check each cluster against
   the **already-approved** listings (Phase-0 reading) — an existing listing puts a candidate in that
   cluster too.
2. **Label each candidate.** Assign: category (one of the 8), a short topic label, the source
   (owner/repo/path, stars, fork?), and the trust level it would qualify for.
3. **Judge each candidate strictly** against the rulebook, reading the real SKILL.md body. Emit a
   verdict — `approve` / `needs_review` / `reject` — with the *specific* rule or disqualifier that
   drove it (name the hard gate passed/failed or the reject reason). Be adversarial: actively try to
   disqualify (extractability, "JVM fit is the subject", hallucinated APIs, project-doc/demo signals).
   Use maximum reasoning effort here; where helpful, fan out one strict judge subagent per cluster **on
   the Opus model** and have each independently try to refute promotion before you accept it.
4. **Deduplicate within each cluster and choose the best.** When ≥2 candidates (or a candidate vs an
   existing listing) teach substantially the same thing, select the single **best** and mark the rest
   `duplicate` (not a quality reject — record which winner supersedes them). Ranking criteria, in order:
   (a) clears more hard gates / higher trust (official > curated > community; library-author beats
   third-party); (b) deeper, more concrete, more correct content; (c) canonical source over a
   copy/workshop variant (eval.md single-promotion rule); (d) more maintained (recent commits, stars);
   (e) better extractability. State *why* the winner won and why each loser was dropped.
5. **Output — `docs/candidate-review.md`:**
   - A **summary table**: one row per candidate — cluster | topic | category | source | verdict |
     dedup status (winner / duplicate-of / n/a) | one-line reason.
   - A **per-cluster section**: the members, the chosen winner + justification, dropped duplicates +
     which winner supersedes them, and any standalone verdicts.
   - A **final promote list**: the exact set that should become new `skills/*.yaml` listings (winners
     that pass every hard gate), each with proposed category + trust level — ready for a human to action.

---

## Guardrails

- Read-only except writing `docs/skill-approval-rulebook.md` and `docs/candidate-review.md`. Do **not**
  modify `skills/`, any `skill-scout/db/*.csv`, `eval.md`, `review.html`, or promote/reject anything.
- Don't fabricate. If the current approved set is internally inconsistent (it will be — eval.md's
  changelog documents real judge/recheck disagreements), say so and label your recommendations as
  recommendations, not existing policy.
- **Appendix in the rulebook: "Currently-listed skills to revisit."** As you read the 31 approved
  listings against the bar you derive (and against Phase-2 dedup), flag any that wouldn't clear it —
  too thin, not extractable, metadata gaps, borderline JVM fit, or superseded by a better candidate —
  with the specific concern. Do not change them; just surface them.
- When done, print a short summary: the hard-gate list, the disqualifier list, the Phase-2 promote
  list (winners), the duplicates dropped, and any currently-listed skills flagged to revisit.
