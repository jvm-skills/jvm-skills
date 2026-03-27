# jvm-skills

[![Build](https://github.com/jvm-skills/jvm-skills/actions/workflows/build.yml/badge.svg)](https://github.com/jvm-skills/jvm-skills/actions/workflows/build.yml)

**[jvmskills.com](https://jvmskills.com)** — Curated directory of the best AI coding skills for JVM developers.

Skills are opinionated best-practice guides that AI coding tools (Claude Code, Cursor, Copilot, etc.) use as context when writing code. The directory helps JVM developers discover, evaluate, and adopt high-quality skills for their stack.

## Why?

AI coding tools are only as good as their context. Without guidance, they generate code that *works* but doesn't follow the patterns a senior engineer would use. jvm-skills fills that gap with strongly opinionated best practices.

General skill directories exist (playbooks.com, skills.sh, skillsdirectory.com), but they're not focused on a specific ecosystem — and many of the top-installed skills are surprisingly shallow. The most popular Spring Boot skill on skills.sh has 9.8K installs and just tells the AI to "use Spring Boot best practices." That's not a skill — Claude already does that without one. jvm-skills only lists skills that teach the AI something it wouldn't know on its own.

## Browse Skills

Visit **[jvmskills.com](https://jvmskills.com)** to browse all skills, filter by AI tool, language, and category.

### Categories

| Category | Scope |
|----------|-------|
| Database | jOOQ, JPA/Hibernate, PostgreSQL, Flyway, Liquibase |
| Web | Spring Boot, JTE, Thymeleaf, security |
| Infrastructure | Docker, CI/CD, deployment, observability |
| Testing | Testcontainers, integration testing patterns |
| Architecture | Hexagonal, design patterns, modularity |
| Workflow | Planning, interview, code review, process skills |

## Contributing

Want to add a skill to the directory? See [CONTRIBUTING.md](CONTRIBUTING.md) for the step-by-step guide.

**TL;DR:** Fork → create `skills/<category>/<name>.yaml` → open a PR.

## Local Development

```bash
# Requires Kotlin (https://kotlinlang.org/docs/command-line.html)
# Build once
kotlin site/build.main.kts
open dist/index.html

# Or use the live-reload dev server
./site/watch.sh
```

## Repository Structure

```
skills/                    # Skill listing YAML files (one per skill)
  database/                #   jooq.yaml, flyway.yaml, postgresql.yaml
  web/                     #   spring-core.yaml, jte.yaml
  infrastructure/          #   docker-spring.yaml
  testing/                 #   testcontainers.yaml
  architecture/            #   hexagonal.yaml
  workflow/                #   grill-me.yaml
site/                      # Website build tooling
  template.html            #   HTML template with embedded CSS/JS
  build.main.kts           #   Kotlin build script: reads YAML → outputs dist/index.html
  validate.main.kts        #   Kotlin validation script for CI
  build.sh                 #   Shell wrapper for build.main.kts
  watch.sh                 #   Live-reload dev server
ralph/                     # Skill builder tooling
dist/                      # Generated output (git-ignored)
.github/workflows/         # CI/CD pipelines
```

## Ralph: The Skill Builder

Ralph is a semi-autonomous pipeline that reads blog articles and extracts best-practice patterns into structured knowledge files. See [ralph/jooq-skill-creator/README.md](ralph/jooq-skill-creator/README.md) for details.

## License

Apache 2.0 — see [LICENSE](LICENSE).
