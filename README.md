# jvm-skills

[![Build](https://github.com/jvm-skills/jvm-skills/actions/workflows/build.yml/badge.svg)](https://github.com/jvm-skills/jvm-skills/actions/workflows/build.yml)

**[jvmskills.com](https://jvmskills.com)** — AI coding skills from the engineers who build the JVM ecosystem.

![jvmskills.com preview](site/preview.webp)

Skills are opinionated best-practice guides that AI coding tools (Claude Code, Cursor, Copilot, etc.) use as context when writing code. The directory helps JVM developers discover, evaluate, and adopt high-quality skills for their stack.

## Why?

AI coding tools are only as good as their context. Without guidance, they generate code that *works* but doesn't follow the patterns a senior engineer would use. jvm-skills fills that gap with strongly opinionated best practices.

General skill directories exist (playbooks.com, skills.sh, skillsdirectory.com), but they're not focused on a specific ecosystem — and many of the top-installed skills are surprisingly shallow. The most popular Spring Boot skill on skills.sh has 9.8K installs and just tells the AI to "use Spring Boot best practices." That's not a skill — Claude already does that without one. jvm-skills only lists skills that teach the AI something it wouldn't know on its own.

## Browse Skills

Visit **[jvmskills.com](https://jvmskills.com)** to browse all skills, filter by AI tool, language, and category.

### Categories

| Category | Scope |
|----------|-------|
| Framework | Comprehensive framework guides, scaffolding, and framework-level best practices |
| Language | Java, Kotlin, and JVM language best practices |
| Database | jOOQ, JPA/Hibernate, PostgreSQL, Flyway, Liquibase |
| Testing | Testcontainers, integration testing patterns |
| Fullstack | End-to-end application workflows spanning backend, frontend, and tests |
| Web | Web UI, frontend, templates, and browser-facing performance |
| Workflow | Planning, interview, code review, process skills |
| Tool | Agent-facing tools, automation utilities, and supporting integrations |

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
  framework/               #   spring-boot.yaml, scaffolding.yaml
  language/                #   java-code-quality.yaml, design-patterns.yaml
  database/                #   jooq.yaml, jpa.yaml, postgresql.yaml
  testing/                 #   testcontainers.yaml, tdd.yaml
  fullstack/               #   fullstack fix and end-to-end workflows
  web/                     #   frontend design and web performance
  workflow/                #   planning, commit, interview workflows
  tool/                    #   browser automation and supporting tools
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
