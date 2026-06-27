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
Jakarta EE, JUnit, Reactor / Project Reactor, Vert.x. Kafka counts as JVM only when the guidance is
about JVM clients/Streams, not generic ops.

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
- 2026-06-27 (Devnexus 2026) — **Rule 2's single-promotion principle extends to bundles.** When a speaker has both a canonical multi-step pipeline (in their dedicated skills repo, more steps, richer content) and a teaching/workshop variant of the same pipeline (demo repo, fewer steps, thinner content), promote only the canonical as `found`; the workshop variant is `needs_review` at best — not a second `found` listing. (e.g., agentskills/spec-driven-development found at 13 stars; sdd-workshop 5-step variant needs_review at 2 stars.)
- 2026-06-27 (jPrime 2026) — **Rule 5's `workflow` escape requires a bundle, not just a deep skill.** A single well-developed non-JVM skill (e.g., 47-line code-review workflow, 130-line PR-defense guide, LLM communication-style) is `off-topic-workflow` / `off-topic-tech` regardless of its depth or quality — "single thin step" in rule 5 means individual step, not quality judgment. Skill depth does not override the bundle requirement. The `tool` category label likewise does not rescue individual non-JVM utilities (knowledge-base schema, interaction style).
- 2026-06-27 (J-Spring 2026) — **Zero found AND zero rejected is a valid run outcome.** Speakers who publish primarily as educators (authors, advocates, presenters) may have no in-repo skill files regardless of follower count or JVM prominence (e.g. nipafx/Nicolai Parlog, 918 followers, 0 skill files across 70 repos). Do not re-investigate confident HIGH resolutions or flag the scan as broken when the result is simply zero.
- 2026-06-27 (Devoxx Poland 2026) — **JVM fit must be the subject, not an accident.** A skill that crawls an Angular UI with one incidental actuator curl, or a code-review workflow that happens to live in a Java repo, is not JVM-fit. Ask: could this skill be lifted verbatim into a Python or JS project without change? If yes, classify `off-topic-workflow` / `off-topic-tech` directly — not `needs_review`.
- 2026-06-27 (Devoxx Poland 2026) — **Hybrid project-docs with embedded skill content stay `project-doc`.** A CLAUDE.md/AGENTS.md that mixes project-specific scaffolding (build commands, endpoint lists, branch strategy) with some reusable patterns is still `project-doc` unless the transferable guidance is self-contained and primary. Test: can the skill content be extracted unchanged into a different project without referencing this project's layout, endpoints, or file paths? If not, project-doc wins.
- 2026-06-27 — seeded from the 3-conference trial review.
