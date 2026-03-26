# jvm-skills — Technical Specification

## Overview

**jvm-skills** is a curated directory of the best AI coding skills for JVM projects, hosted at **jvmskills.com**.

Skills are opinionated best-practice guides that AI coding tools (Claude Code, Cursor, Copilot, etc.) use as context
when writing code. The directory helps JVM developers discover, evaluate, and adopt high-quality skills for their stack.

The project follows a **phased approach**:

1. **Phase 1 — Directory.** A curated website listing the best JVM skills. Ship fast, validate demand.
2. **Phase 2 — Evaluation.** Automated quality scoring of skills using an autoresearch eval loop.
3. **Phase 3 — Tooling.** A CLI that auto-detects a project's stack and assembles skills. (See `spec-tool-v2.md`.)

---

## Core Principles

1. **Directory first.** Prove the catalog is valuable before building tooling around it.
2. **Decentralized content.** Skills live in their own repos. The directory links to them, it doesn't host them.
3. **Curated quality.** Expert authors are hand-picked. Community submissions go through PR review.
4. **JVM-focused, not JVM-exclusive.** Core focus is JVM libraries/frameworks. Adjacent tech that JVM developers commonly use (PostgreSQL, Docker, Testcontainers, Flyway) is in scope.
5. **Strongly opinionated skills.** Listed skills state "do X, don't do Y." If you disagree, edit your local copy.
6. **Transparent evaluation.** Phase 2 adds public quality scores so developers can make informed choices.

---

## Phase 1: Curated Directory

### Architecture

```
jvm-skills/                          # GitHub repo (github.com/jvm-skills/jvm-skills)
├── skills/                          # Skill listing YAML files (one per skill)
│   ├── database/
│   │   ├── jooq.yaml
│   │   ├── jpa.yaml
│   │   └── flyway.yaml
│   ├── web/
│   │   ├── spring-core.yaml
│   │   └── jte.yaml
│   ├── infrastructure/
│   │   └── testcontainers.yaml
│   ├── testing/
│   │   └── spring-boot-testing.yaml
│   ├── architecture/
│   │   └── hexagonal.yaml
│   └── workflow/
│       ├── grill-me.yaml
│       └── prd-to-plan.yaml
│
├── experts.yaml                     # Curated list of trusted expert authors
├── build-site.sh                    # Shell script: reads YAML → outputs index.html
├── template.html                    # HTML template with embedded CSS/JS
│
├── dist/                            # Generated output (git-ignored, built by CI)
│   └── index.html
│
├── .github/
│   └── workflows/
│       ├── build.yml                # CI: validate YAML + build site
│       └── deploy.yml               # CD: deploy to GitHub Pages
│
├── docs/
│   └── dev/
│       ├── spec.md                  # This file
│       └── spec-tool-v2.md          # Future tooling spec (archived)
│
├── CONTRIBUTING.md
├── README.md
└── LICENSE
```

### Content Model

Skills live in their own repositories, maintained by whoever wrote them. The directory repo contains only
**listing metadata** (YAML files) that point to those repos — no skill content.

This is analogous to awesome-lists but structured as YAML for machine-readability, with a generated website on top.

### Skill Listing Schema

Each skill is a YAML file in the `skills/<category>/` directory:

```yaml
# skills/database/jooq.yaml
name: jOOQ Best Practices
description: >-
  Comprehensive jOOQ DSL best practices for queries, result mapping,
  transactions, and repository layer design.
repo: jvm-skills/jooq-skill
category: database
tools:
  - claude
  - cursor
languages:
  - kotlin
  - java
trust: expert                         # expert | community
author: Lukas Eder
maintainer: jvm-skills
version: "1.2.0"
last_updated: "2026-03-15"
min_spring_boot: "3.0"
tags:
  - sql
  - dsl
  - type-safe
  - database
```

#### Field Reference

| Field              | Required | Description                                                                |
|--------------------|----------|----------------------------------------------------------------------------|
| `name`             | yes      | Display name of the skill                                                  |
| `description`      | yes      | One-paragraph description shown on the card                                |
| `repo`             | yes      | GitHub `owner/repo` where the skill content lives                          |
| `category`         | yes      | One of: `database`, `web`, `infrastructure`, `testing`, `architecture`, `workflow` |
| `tools`            | yes      | AI tools supported: `claude`, `cursor`, `copilot`, `windsurf`, `aider`     |
| `languages`        | yes      | Languages supported: `kotlin`, `java`, or both                             |
| `trust`            | yes      | `expert` (author is in experts.yaml) or `community`                        |
| `author`           | yes      | Person or organization who created the skill                               |
| `maintainer`       | no       | Person or org currently maintaining (if different from author)              |
| `version`          | no       | Latest version/tag of the skill                                            |
| `last_updated`     | no       | Date of last significant update (YYYY-MM-DD)                               |
| `min_spring_boot`  | no       | Minimum Spring Boot version (if applicable)                                |
| `tags`             | no       | Freeform tags for filtering                                                |
| `screenshots`      | no       | List of screenshot URLs (future use)                                       |

### Categories

Skills are organized by technology layer:

| Category           | Scope                                                                  |
|--------------------|------------------------------------------------------------------------|
| `database`         | Data access (jOOQ, JPA/Hibernate), databases (PostgreSQL, MySQL), migrations (Flyway, Liquibase) |
| `web`              | Web frameworks (Spring Boot, Quarkus), template engines (JTE, Thymeleaf), security |
| `infrastructure`   | Docker, CI/CD, deployment, observability                               |
| `testing`          | Testing strategies, Testcontainers, integration testing patterns       |
| `architecture`     | Design patterns, hexagonal architecture, modularity                    |
| `workflow`         | Process and meta skills: planning (prd-to-plan), interview (grill-me), code review, compound engineering. These are language-agnostic but curated for JVM developers. |

### Trust Model

#### Expert Authors

You maintain a curated `experts.yaml` file listing trusted experts:

```yaml
# experts.yaml
experts:
  - name: Lukas Eder
    github: lukaseder
    expertise: jOOQ, SQL
  - name: Bruno Borges
    github: brunoborges
    expertise: Java, Azure, Spring
  - name: Thomas Schuehly
    github: tschuehly
    expertise: Spring Boot, JTE, jOOQ
```

Skills where the `author` matches an expert get the **Expert** badge automatically. All other skills get the
**Community** badge.

The expert list is curated by you (Thomas). Adding someone requires a commit to `experts.yaml`.

#### Badge Display

- **[Expert]** — Author is a recognized expert. High confidence in quality.
- **[Community]** — Submitted by the community via PR. Passed basic review.

### Website

#### Generation

A shell script (`build-site.sh`) reads all YAML files in `skills/` and `experts.yaml`, then generates a single
`dist/index.html` using an HTML template.

- **Input:** `skills/**/*.yaml` + `experts.yaml` + `template.html`
- **Output:** `dist/index.html` (single self-contained HTML file with embedded CSS and JS)
- **No dependencies** beyond standard shell tools (`yq` or similar for YAML parsing)

#### Design

- Skills grouped by category (Database, Web, Infrastructure, Testing, Architecture)
- Each skill rendered as a card showing: name, description, author, trust badge, supported tools, languages, tags
- Client-side JavaScript for filtering by: search text, AI tool, language, trust level
- Cards link directly to the skill's GitHub repo — no detail pages
- Responsive design (mobile-friendly)

#### Hosting

- **GitHub Pages** with custom domain **jvmskills.com**
- GitHub Actions CI/CD: push to main → validate YAML → build site → deploy

### Contribution Workflow

#### Adding a new skill listing

1. Fork the repo
2. Create a YAML file in the appropriate category: `skills/<category>/<name>.yaml`
3. Fill in all required fields per the schema
4. Open a PR
5. CI validates the YAML schema automatically
6. Maintainer (Thomas) reviews and merges
7. Site auto-rebuilds and deploys

#### Becoming an expert

Expert status is by invitation only. If a tool maker (e.g., Lukas Eder for jOOQ) or recognized community expert
wants to be listed, Thomas adds them to `experts.yaml`.

### Seed Content

Launch with ~5-10 skill listings:

- **Our own:** jOOQ best practices skill
- **Known external:** Timescale pg-aiguide, other known high-quality JVM AI skills
- **Expert network:** Skills from Bruno Borges, other contacts

---

## Phase 2: Skill Evaluation

### Autoresearch Eval Loop

Automated quality scoring of listed skills using a methodology inspired by
[MindStudio's autoresearch eval loop](https://www.mindstudio.ai/blog/autoresearch-eval-loop-binary-tests-claude-code-skills).

#### How it works

1. **Define test inputs.** For each skill, create 20-30 representative coding tasks that the skill should help with.
2. **Generate outputs.** Have an AI coding tool use the skill to solve each task.
3. **Apply binary tests.** Evaluate each output against pass/fail criteria:
   - Does the output follow the skill's stated best practices?
   - Does the output avoid the skill's stated anti-patterns?
   - Is the generated code correct and idiomatic?
   - Does the skill improve output quality vs. no skill?
4. **Score.** Calculate pass rate as a quality percentage.
5. **Iterate.** Re-run when skills are updated or new library versions release.

#### Display

Quality scores are shown publicly on skill cards:

```
[Expert] jOOQ Best Practices        92% quality score
by Lukas Eder
Claude, Cursor | Kotlin, Java | Database
```

#### Implementation (TBD)

- Eval runner (likely a Claude Code agent or script)
- Test input corpus per skill category
- Binary test definitions
- Score storage and display pipeline
- Re-evaluation triggers (skill update, schedule)

---

## Phase 3: Tooling

A CLI tool that auto-detects a project's technology stack and assembles composed skills from the directory into the
user's AI tool format. See `spec-tool-v2.md` for the full architectural specification.

### Transition: Directory YAML Graduates into CLI Registry

The same `skills/<category>/<name>.yaml` files that power the directory website grow to serve the CLI tool. New
optional fields are added; existing fields remain unchanged. The website ignores fields it doesn't use, the CLI
reads the full schema.

**Phase 1 schema (directory only):**

```yaml
# skills/database/jooq.yaml
name: jOOQ Best Practices
description: >-
  Comprehensive jOOQ DSL best practices
repo: jvm-skills/jooq-skill
category: database
tools: [claude, cursor]
languages: [kotlin, java]
trust: expert
author: Lukas Eder
version: "1.2.0"
last_updated: "2026-03-15"
tags: [sql, dsl, type-safe]
```

**Phase 3 schema (directory + CLI):**

```yaml
# skills/database/jooq.yaml — same file, new optional fields
name: jOOQ Best Practices
description: >-
  Comprehensive jOOQ DSL best practices
repo: jvm-skills/jooq-skill
category: database
tools: [claude, cursor]
languages: [kotlin, java]
trust: expert
author: Lukas Eder
version: "1.2.0"
last_updated: "2026-03-15"
tags: [sql, dsl, type-safe]

# --- Phase 3 fields (used by CLI, ignored by website) ---
activatesOn:                          # Dependencies that trigger this skill
  - "org.jooq:jooq"
overlays:                             # Overlay dimensions for composition
  language: [kotlin, java]
  database: [postgres, mysql]
path: skills/database/jooq            # Path within the skill repo
ref: v1.2.0                           # Git ref to pin content to
```

**Key design choice:** One YAML file per skill, one source of truth, two consumers. No migration needed — the
CLI fields are additive and optional. Skills without `activatesOn` are skipped by the CLI (workflow skills, or
skills not yet configured for auto-detection). The `registry.yml` from the v2 spec becomes unnecessary — dimension
config moves into the CLI itself, and skill discovery uses the same directory YAML files.

---

## Design Decisions Log

| Decision                | Chosen                                       | Rationale                                                                   |
|-------------------------|----------------------------------------------|-----------------------------------------------------------------------------|
| Phase 1 focus           | Curated directory website                    | Validate demand before building tooling. Ship fast.                         |
| Content hosting         | Decentralized (skills in their own repos)    | No content maintenance burden. Skill authors own their content.             |
| Listing format          | YAML files in a git repo                     | Machine-readable, PR-friendly, CI-validatable.                              |
| Website generation      | Shell script → single HTML file              | Zero dependencies, simplest possible build. No SSG framework to maintain.   |
| Hosting                 | GitHub Pages at jvmskills.com                | Free, automatic deployment, zero ops.                                       |
| Trust model             | Curated expert authors list                  | Quality signal without per-skill review overhead. You curate the experts.   |
| Categories              | By tech layer                                | Matches how developers think about their stack.                             |
| Card links              | Direct to skill repo                         | No detail pages to maintain. Users go straight to the source.               |
| Filtering               | Client-side JS on single page                | No backend needed. Works for 100+ skills.                                   |
| Contribution model      | PRs adding YAML files + CI validation        | Low barrier, automated checks, maintainer review.                           |
| Scope                   | JVM-focused, adjacent tech allowed           | Covers what JVM developers actually use without being too narrow.           |
| Skill evaluation        | Autoresearch eval loop (phase 2)             | Objective, automated quality scoring. Public transparency.                  |
| Rich metadata           | Yes (version, author, last_updated, etc.)    | Better filtering and trust signals for users.                               |
| Project name            | jvm-skills at jvmskills.com                  | Clear, memorable, matches the ecosystem scope.                              |
| Phase transition        | Directory YAML graduates (adds CLI fields)   | One file per skill, one source of truth, two consumers. No migration needed.|
| Workflow skills         | Included as a category                       | Universal process skills (grill-me, prd-to-plan) are useful for JVM devs too.|
