# jvm-skills Approval Rulebook

Standalone review guide for deciding whether a skill is **jvm-skills approved** — i.e. worth a
listing in `skills/<category>/<name>.yaml` on jvmskills.com. A new reviewer should be able to apply
this document cold, without having read `skill-scout/harness/rules/eval.md` (this rulebook
consolidates it) or any prior review history.

> **Status note.** This rulebook is *derived* from the repo's actual practice: the 31 approved
> listings, `CONTRIBUTING.md`, and ~75 conferences of field-tested judge/recheck decisions in
> `skill-scout` (eval.md + `db/rejected.csv`). Where current practice is internally inconsistent
> (it is — see the Appendix), the rules below state the recommended bar and the inconsistencies are
> flagged rather than papered over.

---

## 1. Purpose & philosophy

jvm-skills only lists skills that **teach the AI something it wouldn't know on its own** (README.md).
The named anti-pattern: the most-installed Spring Boot skill on a general directory has 9.8K installs
and just says "use Spring Boot best practices" — that is not a skill, because Claude already does
that unprompted. Every rule below serves one governing test: **does this skill deliver concrete,
opinionated, reusable JVM expertise an AI wouldn't otherwise have — and is it the best available
version of that skill?** A skill earns a listing by being *load-bearing context*: version-specific
knowledge, non-obvious pitfalls, opinionated defaults, and verified APIs — not restated common sense.

### The unit of evaluation: the skill-unit

A skill is evaluated as its **skill directory as a unit**: the `SKILL.md` plus any companion files
that ship *inside the same skill directory* (`references/`, `knowledge/`, scripts). The approved
gold standard works this way: `jooq-best-practices/SKILL.md` is a 71-line index whose substance
lives in 30+ co-located `knowledge/*.md` files — that is a deep skill, not a thin one. Conversely,
a 700-line SKILL.md that depends on files *outside* its directory (numbered sibling pipeline steps,
repo-level docs, orchestration state) is not self-contained no matter how long it is.

---

## 2. Hard minimum requirements (objective gates — must pass ALL)

| # | Gate | Test |
|---|------|------|
| H1 | **Authorship** | The submitter wrote the skill, in their own **non-fork** repo. Fails on: in-file attribution to someone else ("Original source: …", "Adapted from …" — e.g. lordofthejars/test-codeassistants-workshop carried a 428-line Playwright-Java skill with "Original source: sickn33/antigravity-awesome-skills" in its footer); an `import_url:` frontmatter field (machine-imported copy — e.g. dyor/Factory-13's 501-line KMP skill pointed at dyor/skills as canonical); a path segment encoding a different login (e.g. asm0dey/conference-notifier-bot vendored jbaruch's skills under `.tessl/plugins/jbaruch/…`); `vendor/` paths; "a collection of SKILL.md files I've found" repos (tedneward/AgentSkills). |
| H2 | **Concrete + opinionated substance** | The skill-unit prescribes a specific, reproducible method with code/commands/decision rules — not a stub, a manifesto, or "use best practices". Fails on: ≤~25-line placeholder SKILL.md files (template variables, bare checklists); personal philosophy files ("zen-of-X", guiding principles — e.g. jamesward/skills `zen-of-james` restated generic FP beliefs with no actionable method); "run `mvn test`, read output, fix, re-run" wrappers that invoke commands any agent already knows (jkordick/ghcp-java-intellij `build-and-compile`/`run-tests`). |
| H3 | **Depth floor** | Depth ≥ 2 as *content*, not just length: named APIs with version-specific behavior, anti-patterns with rationale, worked code, decision tables. Rough proxy: ~100+ lines of substance across the skill-unit. Calibration from the approved set: line counts run 64–400 (median ~245), and the 80-line `java-optionals` clears comfortably because every line is load-bearing (version-gated API rules, lazy-fallback semantics) — while the 64-line sivalabs spring-boot hub is the set's one genuine weakness (pure index). Length never rescues content that fails other gates; a bare SKILL.md under ~25 lines is effectively always a placeholder. |
| H4 | **Self-contained / extractable** | Can a practitioner drop the skill-unit into a *different* project and follow it unchanged? Fails on: references to numbered sibling pipeline files (`01-spec.md`, "Phase 3", `harness.sh` — loiane/specs-driven-development-spring-angular had real Spring/JaCoCo content in 12 skills that were all integration nodes of a 9-phase proprietary framework); agent-framework orchestration state (`executionState.returnAssignee`, stage participants — alvarosanchez/micronaut-agent-company); companion reference docs *outside* the skill directory (jabrena/cursor-rules-java's 2026-era dispatch shells deferred to unreachable `references/NNN-topic.md`; note the repo has since co-located them — re-verify reachability, don't reuse old verdicts); machine-local absolute paths (`C:\VoxxedDays\…` — WBurggraaf/VoxxedDays `green-java-pr-report`); open injection sections ("Code to be Refactored:" left blank for a pipeline to fill — anishi1222 `java-refactoring-extract-method`); `scope: repository` / `maturity: starter` frontmatter (Junie starters — JohannesRabauer/junie-midi-javafx-app). |
| H5 | **JVM fit is the subject, not an accident** | The concrete code and core method are Java/Kotlin/JVM-native. Test: could this file be lifted verbatim into a Python or JS project unchanged? If yes → off-topic. (Sole exception: a coherent high-quality **workflow bundle** — see §5.) Details in H5a–H5d below. |
| H6 | **APIs actually exist** | Spot-check claimed classes/methods/config keys against the library's real public surface, and template `import` package prefixes against the declared artifact's runtime namespace. jbaruch/koog-tessl taught a fabricated Koog `install(Sql)` API; anishi1222's 756-line MCP-server generator imported `io.mcp.server.*` while the real SDK namespace is `io.modelcontextprotocol.*` — every generated class failed to compile. Uniform line counts across a collection signal template-filled content — but verify against real byte sizes first (a scanner read-cap once made 19 of jbaruch/koog-tessl's 30 skills *appear* to be exactly 140 lines; the real kill there was the generator-fabricated APIs). Verify ≥3 members before promoting any generator-emitted collection. |
| H7 | **Reusable beyond one project/event/machine** | Fails on: event-expiring purpose (a Devoxx France schedule navigator); fictional-company branding ("Contoso Java Standards" — agoncal/contoso-plugin-marketplace, 123–184-line skills, all rejected); workshop exercise fixtures (`step-2/SKILL.md` = the exercise's own expected output — lordofthejars/java-migration-modernization-bob); classpath resources (`src/main/resources/**/skills/` — habuma/spring-ai-recipes); timestamped experiment archives (`experiments/runs/2026-05-17_…/` — marcoemrich/agentic_coding_lab, 342 fixtures); the author's own `archive/` folder (dyor/skills). |
| H8 | **Complete listing metadata** | The `skills/<category>/<name>.yaml` has all required fields per CONTRIBUTING.md (`name`, `description`, `repo`, `category`, `tools`, `languages`, `trust`, `author`), the category is one of the 8, `repo`+`skill_path` resolve to the actual SKILL.md, and `trust` follows §5 (community for PR submissions; official/curated assigned by maintainers). |

### H5 refinements (all field-tested)

- **H5a — Where the code lives decides, not what the text claims.** "This also applies to Java"
  doesn't rescue a skill whose examples are C#/Python/Go (tpierrain/the-hive-pattern: 319 lines of
  C# with one throwaway Java mention). Symmetrically, a skill scaffolding a non-JVM language as a
  co-equal first-class track throughout ("Java/jqwik OR TypeScript/fast-check" in every step —
  gtrefs/tdd-pbt-plugin) is polyglot, not JVM.
- **H5b — Java-runtime services don't count.** Operating Elasticsearch/Neo4j/Kafka/ZooKeeper via
  REST/CLI is language-agnostic (dadoonet/fscrawler's `check-elasticsearch` = pure `curl`). JVM fit
  requires Java/Kotlin SDK code, typed config, or JVM-specific patterns. Kafka counts only when the
  guidance is about JVM clients/Streams.
- **H5c — Generic OS analysis of JVM processes doesn't count.** vmstat/mpstat/perf pointed at a JVM
  is Linux analysis (franz1981 `use-analysis`). JVM-native diagnostics do: JFR, jstack, jcmd,
  async-profiler, GC logs, heap dumps.
- **H5d — Android/Compose/KMP are JVM.** Jetpack Compose, Compose Multiplatform, and Kotlin
  Multiplatform are strong JVM signals; never reject solely as "not server-side JVM".
- **Brand names are not proof.** Testcontainers ships official .NET/Node/Go/Python ports under the
  identical brand — a `testcontainers` SKILL.md can be entirely .NET (tedneward/AgentSkills). Read
  the concrete code, not the keyword list.

---

## 3. Quality judgment criteria (strong vs borderline)

Passing the hard gates earns consideration, not a listing. Separators, in rough order of weight:

1. **Non-obvious density.** Count the things a strong model would *not* do by default: version
   deltas ("Spring Batch 6 removed X, use Y"), API-level pitfalls (`.eq()` vs `.equals()` in jOOQ;
   "always call `.execute()`"), performance facts with numbers (`COUNT(*)` ~10% faster than
   `COUNT(1)` on PostgreSQL), tool-specific config that is hard to find. A skill restating framework
   documentation headlines has low density regardless of length.
2. **Opinionation.** The best skills take positions (avoid Mockito, prefer `UNION ALL`, never H2
   compatibility mode) and say *why*. Neutral surveys of options are weaker.
3. **Verification built in.** Approved skills tell the agent how to check its work (run this
   focused test command, compile before/after, `@CheckReturnValue` inspection).
4. **Author authority + maintenance.** Library maker > recognized expert > unknown. Recent commits,
   real stars, active issue flow all raise trust; a repo whose primary language contradicts the
   skill topic lowers it (check `gh api repos/<o>/<r>` → `language` before trusting a description).
5. **Anatomy.** The de-facto shape of the approved set (12 external bodies audited): 12/12 have a
   trigger-rich frontmatter `description`; 11/12 have fenced code examples; 8–9/12 have explicit
   anti-pattern guidance (BAD/GOOD pairs, DO-NOT lists); 8/12 have decision/symptom→fix tables;
   8/12 use progressive disclosure to co-located companion files. A candidate missing *all* of
   code examples, anti-patterns, and tables is very unlikely to clear §1.

**When is `needs_review` right vs a direct reject?** `needs_review` is reserved for
**JVM-plausible skills with genuine quality/depth uncertainty** — a real Spring skill that might be
too thin, a bundle whose coherence needs a deeper read. It is *never* a hedge for off-topic content
(a Rust CLI skill is `off-topic-tech` no matter how well-written — asierzapata/saku), for
structural disqualifiers (a `step-N/` fixture stays `demo` regardless of doubt), or for unread
files (check the repo's primary language first; only hedge when that signal is JVM-plausible or
unavailable). One more textual shortcut: **when the reviewer's own notes contain hedge phrases like
"language-agnostic", "context-free", or "transferable methodology but X-focused"**, the verdict is
already decided — reject, regardless of what score sits next to it (9 of 12 self-contradicting
"found" verdicts in one JCConf Taiwan run were overturned this way).

---

## 4. Automatic disqualifiers (rejection taxonomy)

Consolidated from ~75 conferences of decisions (6,247 rejected rows). Each: one-line test + one real
example.

| Reason | Test | Real example |
|--------|------|--------------|
| `demo` | Value is tied to a one-time event, workshop exercise, fictional company, or the author's machine — the purpose expires outside that context. | philippart-s/ai-learn `devoxx-companion` (Devoxx 2026 schedule navigator); agoncal/contoso-plugin-marketplace ("Contoso Java Standards", 4 skills, 123–184L each); WBurggraaf/VoxxedDays (`C:\VoxxedDays\…` paths); lordofthejars `step-2/SKILL.md` (the workshop's own expected output). Content-free ≤15-line delegating stubs are also `demo` (fcroiseaux/flui, 52 BMAD persona wrappers). |
| `project-doc` | The document serves *this* repo — build/run commands, layout, milestones, phase trackers, orchestration state — rather than teaching a transferable method. Hybrid files with some reusable patterns stay `project-doc` unless the transferable part is self-contained and primary. | koreainvestment/kis-ai-extensions `kis-setup` (env setup via project scripts); bryanfriedman/rewrite-jboss-to-jetty ("Phase N ✓" progress tracker); kdubois/kubernetes-aiops-agent agents.md (206 lines of real Quarkus/LangChain4j content embedded in project setup — still project-doc); anishi1222 `java-refactoring-extract-method` (real heuristics ending in an open "Code to be Refactored" injection slot); jamesward `zen-of-james` (manifesto). |
| `vendored` | Someone else wrote it — in-file attribution, foreign-login path segment, `import_url:`, `vendor/` dirs, curated-copies collections. Chase the real author instead. | dcermak/skiff `vendor/go.opentelemetry.io/otel/AGENTS.md`; tedneward/AgentSkills (self-described found-files collection); asm0dey `.tessl/plugins/jbaruch/…`; anishi1222/multi-agent-code-reviewer, where 8 of 10 `skills/java-*` files were byte-identical copies from github/awesome-copilot (36K★ aggregation repo) — check any `skills/java-*` path against the awesome-copilot skill list on sight. |
| `test-fixture` | Lives under a test/build/experiment path: `src/test/**`, `src/main/resources/**` (classpath-loaded demo resources), `experiments/runs/<timestamp>/**`. Path alone decides; content quality is irrelevant. | habuma/spring-ai-recipes `skills/src/main/resources/.agent/skills/weather/SKILL.md`; marcoemrich/agentic_coding_lab (342 timestamped-run copies). |
| `boilerplate` | Auto-generated or template-family content: byte-identical files in ≥3 directories (issue ONE bulk verdict — wjglerum's workshop had 12 identical Quarkus AGENTS.md each individually re-judged before this rule), tool-emitted docs (Quarkus Dev MCP AGENTS.md, Spectra CLI, OpenSpec/Tessl iikit families), uniform line counts across a collection. | cashwu/ThreeLittlePigs `spectra-*` (generatedBy=Spectra); jbaruch/koog-tessl (0-star generator-emitted Tessl tile for a library the author didn't write, with 2 verified hallucinated APIs among its 30 skills). |
| `off-topic-tech` | Real skill, wrong technology: concrete code is non-JVM, polyglot co-equal tracks, generic OS tooling aimed at JVM processes, or REST/CLI ops of a Java-runtime service. | tedneward `scientific-slides` (Python stack); gtrefs/tdd-pbt-plugin (Java/TS parallel tracks); franz1981 `use-analysis` (vmstat/mpstat); dadoonet `check-elasticsearch` (curl-only). |
| `off-topic-workflow` | Real, even good, *generic* dev/agent workflow as a single skill: code review orchestration, PR flow, commit style, spec-step. The `workflow` category escape requires a coherent multi-skill **bundle** (§5) — depth does not override the bundle requirement (a 130-line PR-defense guide is still off-topic). | hondaya14/skills `gh-pr`; MrLesk/agents-council `backlog-technical-project-manager`. |
| `off-topic-service` | Real skill for operating an external SaaS/service (Stripe, HubSpot, Zoom, trading APIs), not for JVM development. | koreainvestment `kis-strategy-builder` (251 lines, 83 indicators — substantial and still off-topic). |
| `hallucinated-api` | Teaches classes/methods/packages that verifiably don't exist in the named library, or templates whose imports don't match the artifact's runtime namespace. | jbaruch/koog-tessl `query-sql-from-agent` (fabricated `install(Sql)`); anishi1222 `java-mcp-server-generator` (`io.mcp.server.*` vs real `io.modelcontextprotocol.*`). |
| `jvm-collection` | A genuine JVM skill that duplicates an already-promoted sibling (same author, other repo/registry). Reserved for *JVM* duplicates — a non-JVM duplicate keeps the canonical's own reject reason. | antonarhipov/sdd-demo `spring-batch-6` (canonical promoted at antonarhipov/agentskills); the `.junie/skills/` copy of a promoted `.claude/skills/` skill (Java Day Istanbul rule: promote once via `.claude/`, widest reach). |
| `already-listed` | The repo or skill is already in `skills/**/*.yaml` — including copies of listed skills showing up in *other* people's repos. | martinfrancois/java-streams-skill re-surfaced by the scanner; jvm-skills' own `jooq-best-practices/SKILL.md` (71L) found verbatim in tschuehly/lexware and JohannesRabauer/java-project-analyser. |

**Bundle handling.** Numbered SKILL.md files in one skills dir (`01-spec` … `06-execute`) are steps
of ONE pipeline — never judge steps individually as "generic workflow"; evaluate the suite as a
unit. But unit-evaluation does not waive JVM fit: a Tekton pipeline where Maven appears in 1 of 4
steps is `off-topic-tech` as a bundle too (lordofthejars/hello-world-tekton-bob). And structural
hard-stops (step-N fixture, classpath resource, fictional company, ≥3 identical copies) bind every
review pass, including recheck — a file correctly rejected on structure must not be re-promoted
later on content (lordofthejars `step-2` was, wrongly, at Spring I/O 2026).

**Precedence when several reasons apply:** structural signals first (`test-fixture`/`vendored`/
`already-listed` by path or attribution, `demo` for stubs and fixtures, `boilerplate` for template
families), then `project-doc` (coupling/scoping), then `off-topic-*` (which presuppose real
standalone content), then `hallucinated-api` (presupposes otherwise-promotable JVM content).

---

## 5. Category & trust-level guidance

**Categories** (pick exactly one; scope from README):

| Category | Pick when the skill's *primary surface* is… |
|----------|---------------------------------------------|
| framework | a framework as a whole: comprehensive guides, scaffolding (Spring Boot, Quarkus, Micronaut, Ktor) |
| language | Java/Kotlin language technique (Streams, Optional, design patterns, logging idioms) |
| database | data access & DBs: jOOQ, JPA/Hibernate, PostgreSQL, migrations |
| testing | test authoring/infra: Testcontainers, Kotest, coverage, mutation testing, debuggers |
| fullstack | end-to-end workflows spanning backend + frontend + tests |
| web | web UI, templates, frontend, browser-facing performance |
| workflow | process skills: planning, review, commit — **bundles only** for non-JVM content (below) |
| tool | agent-facing utilities and supporting integrations |

**The workflow carve-out (only exception to H5).** A coherent, high-quality *bundle* of
agentic/dev-workflow skills (spec-driven pipeline, review suite) may list under `workflow` even
though its content is not JVM-specific — evaluate the members, coherence, and reusability
extensively first (antonarhipov/agentskills' 6-step SDD pipeline, 79–228 lines per step with EARS
templates and RFC-2119 language, is the exemplar). A single thin workflow step is
`off-topic-workflow` no matter its quality. The `tool` category likewise does not rescue individual
non-JVM utilities.

**Trust levels** (who assigns: maintainers, except community):

- `official` — the library/tool maker wrote the skill for their own library (e.g. Lukas Eder for
  jOOQ; a TamboUI skill by TamboUI's author qualifies). Assigned by maintainers.
- `curated` — recognized expert, vetted by maintainers.
- `community` — submitted via PR; the default for anything a maintainer hasn't vetted.

A skill about someone *else's* library is never `official` regardless of author fame.

---

## 6. Deduplication & "best in class" policy

**Policy: when multiple skills teach substantially the same thing, only the best one is listed.**

*"Substantially the same"* = same technique/topic on the same framework surface at comparable
scope: two "JPA pitfalls" skills; two Spring Boot scaffolding skills; a candidate vs an existing
listing covering the same ground. Different layers of one stack (jOOQ DSL vs PostgreSQL table
design) are NOT the same thing.

**Ranking criteria for picking the winner, in order:**

1. Clears more hard gates / higher trust standing (official > curated > community; the library's
   author beats a third party writing about that library).
2. Deeper, more concrete, more *correct* content (verified APIs beat breadth).
3. Canonical source over a copy or workshop variant — the **single-promotion principle**: a copied
   skill is listed once, at its canonical repo (canonical = dedicated collection repo, else most
   stars, else non-demo; for intra-repo registry copies, `.claude/skills/` wins). The canonical
   multi-step pipeline beats its own teaching variant (antonarhipov/agentskills over sdd-workshop).
4. More maintained: recent commits, stars, release cadence.
5. Better extractability (fewer external couplings).

Losers are marked `duplicate` (superseded-by recorded) — that is not a quality reject and should be
reversible if the winner is delisted.

---

## 7. Reviewer decision procedure (run in this order, stop at first kill)

1. **Already listed?** Repo/skill in `skills/**/*.yaml`, or a verbatim copy of a listed skill →
   `already-listed`. (Cheapest check.)
2. **Structural path scan** (no content read needed): fork? `src/test/**` or
   `src/main/resources/**`? `experiments/runs/<ts>/`? `step-N/`? `archive/`? foreign login in
   path? `vendor/`? → `test-fixture` / `demo` / `vendored`.
3. **Frontmatter scan:** `import_url:` → vendored/jvm-collection at canonical only.
   `scope: repository` / `maturity: starter` → `project-doc`. Identical file in ≥3 dirs → one bulk
   `boilerplate`.
4. **Authorship:** in-file attribution lines; repo self-described as a found-collection →
   `vendored`.
5. **Substance floor (H2/H3):** stub/manifesto/command-wrapper → `demo`/`project-doc`; skill-unit
   depth < 2 → reject or, if JVM-plausible and genuinely uncertain, `needs_review`.
6. **Extractability (H4):** numbered-sibling/framework-state/external-references/machine-paths/
   injection-slots → `project-doc` (or `demo` for machine-local). Companion files count only if
   inside the skill directory and shipped with it.
7. **JVM fit (H5, with H5a–d):** read where the concrete code lives. Off-topic → `off-topic-tech`
   / `off-topic-workflow` / `off-topic-service` directly (never `needs_review`). Non-JVM but a
   coherent workflow *bundle* → evaluate under §5 carve-out.
8. **API verification (H6):** spot-check ≥3 claimed APIs (more if line counts are uniform or the
   collection is large); templates' import namespaces vs declared artifacts → `hallucinated-api`.
9. **Dedup (§6):** against the candidate set AND the 31 existing listings. Same-thing cluster →
   rank, keep one winner, mark the rest `duplicate`/`jvm-collection`.
10. **Metadata (H8):** required YAML fields, correct category, honest trust level.
11. **Verdict** with the specific gate/reason that decided it, in 1–2 substantive sentences naming
    what the skill actually teaches and the author/repo signal. Never a generic template.

---

## 8. Worked examples

### PASS (real approved listings, and why)

1. **jOOQ Best Practices** (jvm-skills, curated; database). 71-line SKILL.md index + 30+ co-located
   `knowledge/*.md` files distilled from official docs + 783 blog articles. Passes because the
   skill-unit is dense with non-obvious, version-pinned facts: "always call `.execute()` — the
   fluent API builds silently"; `NOT EXISTS` over `NOT IN` with nullable columns; MERGE-as-RIGHT-
   JOIN mental model; ORA-38104 workarounds. Opinionated (never H2 compat mode; Testcontainers) and
   verifiable (`@CheckReturnValue`).
2. **Design PostgreSQL Tables** (timescale/pg-aiguide, curated; database). Comprehensive,
   PostgreSQL-specific table-design guidance (types, JSONB, partitioning, index strategy) from a
   database vendor's team — authority + depth + extractable single directory.
3. **Java Streams Skill** (martinfrancois/java-streams-skill, community; language). The community-PR
   exemplar: dedicated single-skill repo, concrete API-level semantics (terminal-op choice,
   collector null behavior, duplicate-key pitfalls, version-gated Gatherers) that a model won't
   reliably volunteer; clean metadata.
4. **JSpecify Nullability** (sivaprasadreddy/sivalabs-agent-skills, curated; tool). Narrow scope
   done deeply: dependency + ErrorProne/NullAway build wiring for Maven and Gradle with
   version-correct configuration — exactly the "hard-to-find config" density §3 rewards.
5. **Spec-Driven Development bundle** (antonarhipov/agentskills — accepted as `found` by the scout
   pipeline under the §5 workflow carve-out). 6 numbered steps, 79–228 lines each, EARS
   acceptance-criteria templates, RFC-2119 constraint language, severity-graded review protocol —
   a coherent bundle evaluated as a unit, listed once at its canonical repo.

### FAIL (real rejected rows, and the rule that kills each)

1. **lordofthejars/java-migration-modernization-bob `step-2/SKILL.md`** — H7/`demo` (step-N
   fixture): 107 lines of real Java content, but literally the workshop exercise's expected output,
   copy-pasted from the workshop adoc. Structure kills it before content is weighed.
2. **agoncal/contoso-plugin-marketplace (4 skills, 123–184L)** — H7/`demo` (fictional company):
   depth-3 Spring/JPA/Maven content branded as "Contoso Java Standards" for a company that doesn't
   exist; showcase artifact, unusable in a real project.
3. **jbaruch/koog-tessl `query-sql-from-agent`** — H6/`hallucinated-api`: teaches a fabricated Koog
   `install(Sql)` query tool absent from `ai.koog`; misinformation, not guidance.
4. **WBurggraaf/VoxxedDays `green-java-pr-report`** — H4/`demo` (machine-local): genuine 113-line
   JVM performance-audit skill made non-portable by hardcoded `C:\VoxxedDays\…` paths.
5. **jamesward/skills `zen-of-james`** — H2/`project-doc` (manifesto): personal FP philosophy in a
   skills dir; declares beliefs, teaches no reproducible method.
6. **dadoonet/fscrawler `check-elasticsearch`** — H5b/`off-topic-tech`: pure `curl` ops of a
   Java-written service; usable unchanged from any language.
7. **gtrefs/tdd-pbt-plugin (10-step bundle)** — H5a/`off-topic-tech` (polyglot): every step offers
   "Java/jqwik OR TypeScript/fast-check" as co-equal tracks; Java coverage depth doesn't make JVM
   the subject.
8. **habuma/spring-ai-recipes `…/src/main/resources/.agent/skills/weather/SKILL.md`** —
   H7/`test-fixture` (classpath resource): a Spring AI demo's loadable resource, not authored
   standalone guidance; path alone decides.

---

## Appendix — Currently-listed skills to revisit

Applying this rulebook to the 31 existing listings themselves (read against the same bar candidates
face) flags the following. These are recommendations to the maintainers, not delistings.

**A. Would fail the JVM-fit gate (H5) that rejects outside candidates daily:**

- `workflow/commit.yaml` (20-line SKILL.md), `workflow/rebase-commit.yaml` (26L),
  `workflow/spec.yaml` (55L), `workflow/interview.yaml` (51L) — generic git/planning workflow,
  liftable verbatim into a Python repo; each is a *single* workflow skill, and §5's carve-out
  requires a bundle. `commit` and `rebase-commit` also sit at/below the H3 placeholder threshold.
  6,247 rejected rows include hundreds of `off-topic-workflow` skills of comparable or better depth
  (e.g. hondaya14's 26-line `gh-pr` was rejected for exactly this). Options: bundle them as one
  coherent "jvm-skills dev workflow" listing, or acknowledge an explicit first-party exception in
  policy.
- `tool/agent-browser.yaml` (vercel-labs, JS/TS), `web/frontend-design.yaml` (Anthropic, html),
  `web/performance-web.yaml` (Addy Osmani, html) — zero JVM content; `off-topic-tech` under the
  scout rules (`languages:` fields even say html/javascript). If the directory intends a "general
  skills useful to JVM devs" section, that policy should be written down; today it contradicts the
  README's JVM mission and the reject taxonomy.
- `testing/ui-review.yaml` (64L) and `fullstack/fix-fullstack.yaml` (68L) — borderline: thin,
  mostly framework-agnostic process; closest to `off-topic-workflow` singles.

**B. Metadata defects (H8):**

- `skills/framework/spring-boot-skill.yaml` declares `category: web` while living in
  `skills/framework/` — one of the two is wrong (content says framework).
- `testing/mutation-testing.yaml` carries `trust: official` with `author: jvm-skills` — jvm-skills
  is not the maker of pitest; per §5 this is `curated` at most.
- `testing/kotest.yaml`: `author: Urs Peter`, but `repo: jvm-skills/jvm-skills` — the listing
  points at jvm-skills' own copy rather than the author's canonical repo, the exact
  single-promotion/canonical-source violation the scout rejects as `vendored` elsewhere. Either
  document the "maintainer-adopted skill" arrangement (there is a `maintainer: jvm-skills` field —
  good start) or move the canonical to the author.
- `framework/restart-spring-boot.yaml` — depends on an IntelliJ run-configuration MCP setup;
  borderline H4 (environment-coupled) and thin (50L).
- `framework/spring-boot-skill.yaml` (sivaprasadreddy) — the SKILL.md body is a 64-line pure
  hub/index: every substantive point delegates to ~13 `references/*.md` files. The references are
  co-located (so H4 passes at the skill-unit level), but the listing's quality rests entirely on
  files the original review may not have read — audit them.
- `framework/dr-jskill.yaml` — body embeds `metadata.recommended_model: gpt-5.5` (competitor-model
  branding inside a directory aimed at Claude/Cursor/Copilot users) and machine-local steps
  (`brew install jdtls`); version-pinned scaffolding assumptions (Java 25/Angular 22/React 19)
  will age fast.
- `tool/jspecify.yaml` — hardcodes dependency versions (jspecify 1.0.0, errorprone 2.42.0,
  nullaway 0.12.12, `release 25`); fine today, needs a `last_updated` refresh cadence.

**C. Superseded-risk / dedup watch (§6):**

- `framework/spring-boot-piomin.yaml` (community) vs `framework/spring-boot-skill.yaml` (curated)
  vs `framework/dr-jskill.yaml` (curated) — three Spring Boot guides already coexist; any new
  Spring Boot candidate must beat all three, and the maintainers should decide whether
  "comprehensive Spring Boot" needs more than one listing per style (piomin's 3.x enterprise vs
  siva's 4.x Modulith vs dubois' scaffolding are arguably distinct scopes — document that
  distinction).
- `language/code-quality-java.yaml`, `language/design-patterns-java.yaml` (piomin) — checklist-style
  breadth skills whose content is closest to "what Claude already does"; weakest of the approved
  set against the §1 governing test. Candidates in the pipeline (e.g. 400+-line Java
  best-practices collections) may supersede them — re-judge on §6 when that happens.

**D. Process debt visible in the data (for the maintainers, not a listing defect):**

- 189 of 483 current candidate rows (`status=found`/`needs_review` in `db/skill_files.csv`) *also*
  appear in `db/rejected.csv` — for 185 of them the rejection is dated at-or-after the found
  verdict (i.e. an Opus recheck overrode the scanner and the found row was never retired). Any
  consumer of `skill_files.csv` must treat "found" as "scanner-promoted", not "approved".
- 9 `rejected.csv` rows carry the bare unfilled template "real SKILL.md — classify JVM vs
  off-topic" as their reasoning — never actually judged; re-run before trusting.
