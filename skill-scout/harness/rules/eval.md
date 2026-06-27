# Skill-Scout evaluation rules

Plain-English guidance the judge + bundle-eval agents read **before** judging. The rule-refinement
agent appends concise, general learnings here after each conference (newest changelog entry on top).
Keep rules general and non-redundant. Git-tracked — every change is auditable and revertable.

## What we are looking for

A directory of **created, reusable, opinionated skills** authored by the speaker in their OWN
(non-fork) repo. Prefer recall on genuinely good skills; reject noise with a specific reason.

- **found** — a real skill with concrete, opinionated guidance (Depth >= 2, ~100+ lines), authored
  by this person, not a demo/talk fixture. JVM skills are the primary target.
- **needs_review** — real but borderline (thin, demo-ish, niche, blog-coupled). When genuinely
  unsure whether something real is promotable, prefer needs_review over reject — never silently drop.
- **reject** — everything else, with a reason from the taxonomy.

## Core principles (seeded from review)

1. **Demo/workshop repo is NOT a reason to reject.** Judge the skill *content's* reusability, not the
   repo's purpose. Several strong authors (e.g. Anton Arhipov) ship genuinely reusable skills *via*
   demo/workshop/conference repos. A 200-line Spring Batch skill in `sdd-demo` is still a real skill.
2. **A copied skill is promoted ONCE, at its canonical repo.** When the same skill appears in several
   of an author's repos, the canonical = the dedicated collection repo, else most stars, else non-demo.
   Don't let the same skill land in both the found and rejected piles.
3. **Bare `CLAUDE.md` / `AGENTS.md` / `.cursorrules` = `project-doc`**, even when the topic is JVM.
   If the file is only build/run/test commands, project layout, or workshop flow — not transferable
   skill guidance — it is `project-doc`, not a skill. (e.g. a Kafka *training project's* CLAUDE.md.)
4. **Numbered SKILL.md in one skills dir = a BUNDLE.** `01-spec`, `02-criteria`, … `06-execute` are
   steps of one pipeline and are meaningless alone. Evaluate the suite as a unit (see bundles below);
   never reject the steps individually as "generic workflow."
5. **Workflow skills can be listed.** A general agentic/dev workflow (code review, spec-driven dev,
   PR defense) is not JVM, but a *coherent, high-quality* workflow bundle is directory-worthy under
   the `workflow` category. Evaluate these MORE extensively — read the members, judge coherence and
   reusability — before deciding. A single thin workflow step on its own is still `off-topic-workflow`.

## Strong JVM signals (high jvm_fit)

Spring (Batch / Boot / Data / Framework), JFR / Java Flight Recorder, Testcontainers, JPA / Hibernate,
jOOQ, Quarkus, Micronaut, Ktor, Kotlin language features, Gradle / Maven internals, GraalVM, JBang,
Jakarta EE, JUnit, Reactor / Project Reactor, Vert.x, Android / Jetpack Compose / Compose Multiplatform /
Kotlin Multiplatform (KMP). Kafka counts as JVM only when the guidance is about JVM clients/Streams, not
generic ops.

## Not JVM (reject reasons)

- `off-topic-workflow` — real reusable skill, generic agent/dev workflow, not JVM (review-orchestration,
  spec-driven-dev step, comms style, thread handoff).
- `off-topic-service` — real skill for an external service (Stripe, HubSpot, Zoom, Google, Tavily).
- `off-topic-tech` — real skill for non-JVM tech (CSS/Tailwind/daisyUI, React/Vue, Python/Rust/Go, robotics).
- `demo` — example/workshop/sample/newsletter skill with no reusable guidance.
- `vendored` — third-party skill copied into the repo, not authored by the speaker (chase the real author).
- `test-fixture` — a skill under `src/test/...`, a fixture not an authored skill.
- `boilerplate` — duplicated template family (OpenSpec, Tessl iikit).
- `jvm-collection` — a real JVM skill that is one member of a found collection (promote-worthy sibling).

## Reasoning requirement

Every verdict needs specific, substantive reasoning (1–2 sentences): name what the skill actually
does/teaches, the author + repo signal (stars, fork), and why it lands in this bucket. Never a generic
template like "demo repo" or "real SKILL.md".

## Learnings changelog

<!-- The rule-refinement agent prepends dated entries here. -->
- 2026-06-27 (Devnexus 2026) — **`step-N/` directory paths in workshop repos flag exercise artifacts, not standalone skills.** A SKILL.md nested inside a numbered workshop step directory (e.g., `step-2/SKILL.md`) is almost always the expected output of that training exercise, not independently-authored reusable guidance. Classify `demo` rather than evaluating on content alone — line count does not override this context signal. (e.g., `lordofthejars/java-migration-modernization-bob/step-2/SKILL.md`: 107 lines with Java content, but the skill was literally the exercise's "create a very simple Skill" expected output, copy-pasted verbatim from the workshop adoc; judge promoted it, Opus caught the fixture.)
- 2026-06-27 (Devoxx UK 2026) — **Stated JVM applicability does not rescue a skill whose concrete examples are in another language.** If all implementation details, class names, and code examples are in C#, Python, or Go, classify `off-topic-tech` even when the text says "this also applies to Java." Judge JVM fit by where the concrete code lives, not by claimed transferability. This complements the existing "JVM fit must be the subject" rule (which tests whether a skill in a JVM repo could be lifted to Python); this is the reverse: the skill is already in C# and only mentions Java in passing. (e.g. tpierrain/the-hive-pattern: 319-line skill with C#/.NET code throughout and a single throwaway Java mention — judge promoted on stated transferability; Opus rejected on concrete content language.)
- 2026-06-27 (KotlinConf 2026) — **Android / Jetpack Compose / Compose Multiplatform / KMP are strong JVM signals, not off-topic.** A KotlinConf 2026 run produced a hard inconsistency: nomisRev's 65-line Jetpack Compose skill was rejected as `off-topic-tech` ("Android is off-topic in JVM skills context") while dyor's Android/Compose/KMP skills of comparable scope were promoted as `found` with `jvm_fit=high` in the same run. Android runs on JVM-compatible ART, Jetpack Compose compiles to JVM bytecode, and KMP targets JVM. All are now listed as strong JVM signals; never reject Android/Compose/KMP skills solely on "not server-side JVM" grounds.
- 2026-06-27 (JCON EUROPE 2026) — **Uniform line counts across a skills collection signal template-filled or auto-generated content.** When ≥50% of promoted skills from one repo share an identical non-trivial line count (e.g., 19 of 30 skills in jbaruch/koog-tessl each at exactly 140 lines), treat the collection as potentially placeholder-extended — verify claimed API names for a sample (≥3 members) before promoting any. Two confirmed hallucinated APIs were found among those 140-line skills in this run; naturally authored collections show varied line lengths.
- 2026-06-27 (Devoxx France 2026) — **A service being written in Java does not make skills for it JVM-specific.** Elasticsearch, Neo4j, ZooKeeper, and similar tools run on the JVM but skills that operate them purely via REST/CLI (`curl`, admin scripts) are language-agnostic and belong to `off-topic-tech`. The existing Kafka carve-out ("Kafka counts as JVM only when guidance is about JVM clients/Streams, not generic ops") generalises to all Java-runtime services: judge JVM fit by whether the skill's *content* contains Java/Kotlin SDK code, typed config, or JVM-specific patterns — never by the runtime of the service being operated. (e.g. dadoonet/fscrawler's `check-elasticsearch` and `start-elasticsearch` skills were promoted as "high JVM fit (Elasticsearch, Java-native)" by the judge; Opus rejected both as pure `curl`/REST ops usable unchanged from any language.)
- 2026-06-27 (Devoxx Greece 2026) — **A path encoding a third-party login is a structural vendoring signal.** When skills appear under a directory that embeds a different GitHub user's login — e.g., `.tessl/plugins/<foreign-login>/<repo>/skills/` where `<foreign-login>` differs from the repo owner — classify as `vendored` without reading file content. The login segment in the installation path identifies the actual author. This is a faster complement to the in-file attribution rule (Devoxx Poland 2026); no file peek required. (e.g., asm0dey/conference-notifier-bot had jbaruch's kotlin-tutor skills installed under `.tessl/plugins/jbaruch/kotlin-tutor/skills/`; the path alone identified the real author.)
- 2026-06-27 (GeeCON 2026) — **Skills nested under a Java source tree are classpath-embedded demo fixtures, not authored standalone guidance.** AI/agent framework demos (Spring AI, LangChain4j, Koog) commonly load SKILL.md files from the JVM classpath; when a SKILL.md lives under a Maven/Gradle build path (`src/main/resources/…/skills/`, `src/test/skills/`, etc.) rather than at a standard location (repo root, `.claude/skills/`, `.agents/skills/`), treat it as a demo resource and apply `demo` or `test-fixture` directly — even if the content looks substantive. This extends the existing `test-fixture` rule (which covers only `src/test/`) to `src/main/resources/` Java build paths. (e.g. tzolov/voxxeddays2026-demo: real skills content in `src/main/resources/.claude/skills/` and `src/main/resources/skills/` — classpath resources for the demo app, not standalone guidance; ivargrimstad/augmented-duke: `src/main/resources/myskills/ducks/SKILL.md` duck-breed demo showing the skill-loader works.)
- 2026-06-27 (Code Remix Summit 2026) — **Progress-tracker document structure = project-doc.** A CLAUDE.md whose primary structure is milestone/phase-completion tracking ("Phase N ✓", accomplishment lists, success-metrics logs) is a project management document, not a transferable skill, even when individual phases contain JVM-specific patterns. The reusability test (hybrid-doc rule) asks if content is extractable; this structure test asks whether the document's *purpose* is tracking this project's completion state vs. teaching a repeatable recipe. (`bryanfriedman/rewrite-jboss-to-jetty`: judge rated "borderline" for JVM JBoss→Jetty migration content; Opus rejected it as a project status tracker for an OpenRewrite recipe project.)
- 2026-06-27 (Voxxed Days Luxembourg 2026) — **Apply `demo` before `off-topic-*` for content-free stubs.** A SKILL.md that is ≤~15 lines and merely delegates to an external file (e.g., BMAD agent persona wrappers) has no standalone guidance — classify `demo` directly, even if the topic is workflow-adjacent. `off-topic-workflow` / `off-topic-tech` presuppose substantive content with the wrong focus; use them only when the skill contains real guidance. (`fcroiseaux/flui` had 52 BMAD stub files inconsistently split between `off-topic-workflow` and `demo`; `demo` was the correct call for all of them.)
- 2026-06-27 (JJUG CCC 2026 Spring) — **Rule 3's stub-= project-doc principle extends to SKILL.md files.** A SKILL.md consisting solely of template placeholders (e.g., `{repository}` variable) and generic bullet checklists with no concrete transferable guidance is a `project-doc` stub regardless of its file extension or placement in a `skills/` directory. Reliable heuristic: a SKILL.md under ~25 lines is almost always placeholder-only. Do not classify these as `needs_review`; they contain no real skill content to review.
- 2026-06-27 (Devoxx Poland 2026) — **In-file source attribution overrides repo authorship for vendoring detection.** If the skill file's own content contains lines crediting a different original author or repo (e.g. "Original source: X", "Adapted from Y", "Adapted for @Z"), treat it as `vendored` regardless of where the file appears in the speaker's repo. Never promote a skill the speaker didn't write. (e.g. lordofthejars/test-codeassistants-workshop had a 428-line Playwright-Java skill with "Original source: sickn33/antigravity-awesome-skills" in its injected footer — judge promoted it; Opus caught the vendoring.)
- 2026-06-27 (Devoxx Poland 2026) — **A skill teaching a non-existent library API is misinformation, not reusable guidance.** When a skill file describes class names, method signatures, or config keys for a named JVM library that verifiably do not exist in that library, reject it (reason: `hallucinated-api`). When promoting framework-specific skills, spot-check claimed API names against the library's real public surface. (e.g. jbaruch/koog-tessl invented `install(Sql)` + `TraceSink.stdout()` APIs absent from ai.koog; judge promoted both; Opus verified and rejected.)
- 2026-06-27 (jPrime 2026) — **Framework tooling can auto-generate AGENTS.md boilerplate that looks like a JVM skill.** Quarkus Dev MCP, for example, emits a byte-identical AGENTS.md (referencing `quarkus_skills/searchDocs`, `quarkus_callTool`) into every project module. These files mention real JVM framework APIs and fool the judge into scoring them as "transferable Quarkus methodology." Classify `boilerplate` when the same file appears verbatim in ≥3 directories of the same repo, or when the content defers entirely to tooling-workflow commands rather than offering authored expertise.
- 2026-06-27 (Devnexus 2026) — **Rule 2's single-promotion principle extends to bundles.** When a speaker has both a canonical multi-step pipeline (in their dedicated skills repo, more steps, richer content) and a teaching/workshop variant of the same pipeline (demo repo, fewer steps, thinner content), promote only the canonical as `found`; the workshop variant is `needs_review` at best — not a second `found` listing. (e.g., agentskills/spec-driven-development found at 13 stars; sdd-workshop 5-step variant needs_review at 2 stars.)
- 2026-06-27 (jPrime 2026) — **Rule 5's `workflow` escape requires a bundle, not just a deep skill.** A single well-developed non-JVM skill (e.g., 47-line code-review workflow, 130-line PR-defense guide, LLM communication-style) is `off-topic-workflow` / `off-topic-tech` regardless of its depth or quality — "single thin step" in rule 5 means individual step, not quality judgment. Skill depth does not override the bundle requirement. The `tool` category label likewise does not rescue individual non-JVM utilities (knowledge-base schema, interaction style).
- 2026-06-27 (J-Spring 2026) — **Zero found AND zero rejected is a valid run outcome.** Speakers who publish primarily as educators (authors, advocates, presenters) may have no in-repo skill files regardless of follower count or JVM prominence (e.g. nipafx/Nicolai Parlog, 918 followers, 0 skill files across 70 repos). Do not re-investigate confident HIGH resolutions or flag the scan as broken when the result is simply zero.
- 2026-06-27 (Devoxx Poland 2026) — **JVM fit must be the subject, not an accident.** A skill that crawls an Angular UI with one incidental actuator curl, or a code-review workflow that happens to live in a Java repo, is not JVM-fit. Ask: could this skill be lifted verbatim into a Python or JS project without change? If yes, classify `off-topic-workflow` / `off-topic-tech` directly — not `needs_review`.
- 2026-06-27 (Devoxx Poland 2026) — **Hybrid project-docs with embedded skill content stay `project-doc`.** A CLAUDE.md/AGENTS.md that mixes project-specific scaffolding (build commands, endpoint lists, branch strategy) with some reusable patterns is still `project-doc` unless the transferable guidance is self-contained and primary. Test: can the skill content be extracted unchanged into a different project without referencing this project's layout, endpoints, or file paths? If not, project-doc wins.
- 2026-06-27 — seeded from the 3-conference trial review.
