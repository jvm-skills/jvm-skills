# Contributing Guidelines

Welcome to **jvm-skills** — a curated collection of best-practice skills for AI coding tools in the JVM ecosystem.

This document outlines how to contribute effectively to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Ways to Contribute](#ways-to-contribute)
- [Skill Structure](#skill-structure)
- [Writing Guidelines](#writing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)

## Code of Conduct

Be respectful, constructive, and inclusive. We welcome contributors of all experience levels.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch** for your contribution
4. **Make your changes** following the guidelines below
5. **Submit a pull request**

## Ways to Contribute

### 1. Write New Skill Content (Highest Impact)

Pick a JVM technology you know deeply and create a skill for it:

| Category     | Planned Skills                           |
|--------------|------------------------------------------|
| Database     | jOOQ, JPA, Flyway, Liquibase, PostgreSQL |
| Spring       | Core, Security                           |
| Frontend     | JTE, DaisyUI, Thymeleaf                  |
| Architecture | Patterns, Testing                        |

### 2. Improve Existing Skills

- Review and refine knowledge files
- Add examples and code snippets
- Fix inaccuracies
- Expand topic coverage

### 3. Build a Ralph Pipeline

Adapt the [Ralph pipeline](ralph/jooq-skill-creator/) to extract skills from other technology blogs or documentation sources.

### 4. Tool Maker Adoption

If you maintain a JVM library, host skill content in your repo and add a `skill.yaml` pointer:

```yaml
name: your-skill-name
repo: your-org/your-repo
path: skills/your-skill
ref: v1.0.0
activatesOn:
  - "your.group:your-artifact"
```

## Skill Structure

Each skill must follow this structure:

```
.claude/skills/<skill-name>/
├── SKILL.md              # Main entry point with knowledge index and core rules
├── knowledge/            # Subdirectory for topic files
│   ├── topic-one.md
│   ├── topic-two.md
│   └── ...
└── UNCERTAINTIES.md      # (Optional) Unresolved questions
```

### SKILL.md Requirements

Use the [jOOQ SKILL.md](.claude/skills/jooq-best-practices/SKILL.md) as a template. Your `SKILL.md` should include:

1. **Header** — Skill name, version, and brief description
2. **Knowledge Index** — Table of contents linking to all knowledge files
3. **Core Rules** — Essential best practices that apply broadly
4. **When to Use** — Context for when this skill applies

### Knowledge File Requirements

Each knowledge file should:

- Focus on **one specific topic**
- Provide **concrete, actionable guidance**
- Include **code examples** (preferably in both Java and Kotlin where applicable)
- Cite **sources** (official docs, blog posts, etc.)
- Be **opinionated** — recommend the best approach, not all approaches

## Writing Guidelines

### Be Opinionated

❌ "You can use either `EXISTS()` or `COUNT(*) > 0`"

✅ "Use `EXISTS()` not `COUNT(*) > 0` for existence checks — it's more efficient and expresses intent"

### Provide Context

Explain **why** a pattern is preferred, not just **what** to do.

### Use Practical Examples

```kotlin
// ❌ Don't: Check existence with COUNT
val exists = dsl.selectCount()
    .from(USERS)
    .where(USERS.EMAIL.eq(email))
    .fetchOne(0, Int::class.java)!! > 0

// ✅ Do: Check existence with EXISTS
val exists = dsl.fetchExists(
    dsl.selectOne()
        .from(USERS)
        .where(USERS.EMAIL.eq(email))
)
```

### Target Audience

Write for AI coding assistants. Be explicit and unambiguous — AI tools perform better with clear, direct instructions.

## Pull Request Process

1. **Create a descriptive PR title** summarizing your contribution
2. **Fill out the PR template** (if available)
3. **Link related issues** if applicable
4. **Ensure your skill follows the structure** outlined above
5. **Request review** from maintainers

### PR Checklist

- [ ] Skill follows the required directory structure
- [ ] `SKILL.md` includes knowledge index and core rules
- [ ] Knowledge files focus on single topics
- [ ] Code examples are correct and tested
- [ ] Sources are cited where applicable
- [ ] Writing is clear and opinionated

## Style Guide

### Markdown

- Use ATX-style headers (`#`, `##`, `###`)
- Use fenced code blocks with language identifiers
- Use tables for structured data
- Keep lines under 120 characters where practical

### Code Examples

- Prefer Kotlin examples with Java alternatives where relevant
- Use meaningful variable names
- Include comments explaining key points
- Show both "don't do this" and "do this" patterns

### Naming Conventions

- Skill directories: `kebab-case` (e.g., `jooq-best-practices`)
- Knowledge files: `kebab-case.md` (e.g., `existence-checks.md`)
- Use descriptive, specific names

## Questions?

- Check the [technical spec](docs/dev/spec.md) for architecture details
- Review the [jOOQ skill](.claude/skills/jooq-best-practices/) as a reference implementation
- Open an issue for questions or discussions

---

Thank you for contributing to jvm-skills! Your expertise helps AI coding tools write better JVM code.
