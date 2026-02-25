# jvm-skills

Curated, opinionated best-practice skills for AI coding tools in the JVM ecosystem.

> **This project is in active development.** The first skill (jOOQ) is in progress.
> The CLI tooling, additional skills, and multi-tool support are being built. 
> The full vision is documented in the [technical spec](docs/dev/spec.md). 
> Contributions are welcome at every stage — 
> from writing skill content to building the CLI infrastructure.

**jvm-skills** is a growing collection of expert knowledge bases that teach AI coding assistants (Claude Code, Cursor,
Copilot, etc.) how to write idiomatic, production-quality code for JVM technologies like jOOQ, Spring Boot, JPA, Flyway,
and more.

## Why?

AI coding tools are only as good as their context. Without guidance, they generate code that *works* but doesn't follow
the patterns a senior engineer would use. jvm-skills fills that gap with strongly opinionated best practices extracted
from official docs, expert blog posts, and real-world experience.

Install a skill, and your AI assistant knows:

- Use `EXISTS()` not `COUNT(*) > 0` for existence checks
- Use `FILTER (WHERE ...)` not `CASE` in aggregates
- Test against real databases via Testcontainers, not H2 compatibility modes
- Map jOOQ results to Kotlin data classes, not Java beans

## Current State

### jOOQ Best Practices (mature)

The first skill is a comprehensive jOOQ 3.20 knowledge base.

Built from 79 processed articles out of 747 scraped from `blog.jooq.org`, with more being added continuously by [Ralph](#ralph-the-skill-builder).

## Vision

A CLI tool (`jvm-skills`) that auto-detects your project's tech stack from `build.gradle.kts` / `pom.xml` and assembles
composed skills (base + language/database overlays) into your AI tool's config directory. See
the [full spec](docs/dev/spec.md) for architecture details.

```
$ jvm-skills init

Detected: Kotlin, Spring Boot 3.3.0, PostgreSQL, jOOQ, Flyway

  [x] jooq          base + kotlin + postgres overlays
  [x] spring-core   base + kotlin overlay
  [x] flyway         standalone
  [x] postgres       standalone

Done. 4 skills installed to .claude/skills/
```

### Planned skills

| Category     | Skills                                   |
|--------------|------------------------------------------|
| Database     | jOOQ, JPA, Flyway, Liquibase, PostgreSQL |
| Spring       | Core, Security                           |
| Frontend     | JTE, DaisyUI, Thymeleaf                  |
| Architecture | Patterns, Testing                        |

## Repository Structure

```
.claude/skills/jooq-best-practices/   # The jOOQ skill (SKILL.md + 23 knowledge files)
ralph/jooq-skill-creator/             # Tooling to build skills from blog articles
docs/dev/spec.md                      # jvm-skills CLI technical specification
```

## Ralph: The Skill Builder

Ralph is a semi-autonomous pipeline that reads blog articles, classifies them, and extracts best-practice patterns into
structured knowledge files. It runs Claude in a Docker sandbox with MCP access to the jOOQ blog, a jOOQ MCP server for
conflict resolution, and context7 for docs.

```bash
# Process one article
./ralph/jooq-skill-creator/ralph-jooq-once.sh

# Process 50 articles in AFK mode
./ralph/jooq-skill-creator/afk-ralph-jooq.sh 50
```

See [ralph/jooq-skill-creator/README.md](ralph/jooq-skill-creator/README.md) for details.

## Contributing

We're looking for collaborators across several areas:

### Write skill content

The highest-impact contribution. Pick a JVM technology you know deeply and write a skill for it:

1. Create a directory under `.claude/skills/<skill-name>/`
2. Write a `SKILL.md` with a knowledge index and core rules (
   use [jOOQ's SKILL.md](.claude/skills/jooq-best-practices/SKILL.md) as a template)
3. Add knowledge files in a `knowledge/` subdirectory, one per topic
4. Submit a PR

### Improve existing skills

- Review and refine existing knowledge files and skills.
- Add examples, fix inaccuracies, expand topics

### Build a Ralph for your technology

The Ralph pipeline can be adapted to build skills from any technology's blog or documentation. Fork the approach for
Spring, JPA, or any other JVM library with a rich content source.

### Tool maker adoption

If you maintain a JVM library, you can host skill content in your own repo. Add a `skill.yaml` pointer in this repo and
the CLI will fetch content from your repository directly.

```yaml
# Example: external skill pointer
name: timescale-design-tables
repo: timescale/pg-aiguide
path: skills/design-postgres-tables
ref: v2.0.1
activatesOn:
  - "org.postgresql:postgresql"
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
