---
title: "jvm-skills Now Has an Interface for Coding Agents"
slug: agent-readable-skill-guides
date: 2026-07-22
draft: false
author: Thomas Schilling
description: "Every jvm-skills listing now explains what the skill does, when it fits, and how an agent can install it. The website also gets a new look ahead of Big Sky Dev Conference."
skills:
  - testing/tdd-task
  - database/jooq-best-practices
  - framework/spring-boot
tags:
  - announcement
  - agent-skills
  - installation
  - big-sky
---

jvm-skills had a directory for developers, but coding agents still had to scrape the HTML cards or follow GitHub links one by one. The install button made this worse: it told every agent to copy the skill into `.claude/skills/`, even when the user was working with Codex, Cursor, or another client.

The directory now has an agent-readable interface:

```text
Inspect this codebase, then read https://jvmskills.com/skills.md and recommend
the smallest useful set of matching skills. Open the linked detail page for
every recommendation and explain it using evidence from the repository.
Do not install anything yet.
```

That one prompt gives the agent a compact catalog, then lets it open the relevant skill guides only when needed.

## A reference file instead of one large prompt

`/skills.md` contains the name and invocation description for every visible listing. `/llms.txt` exposes the same catalog through the emerging documentation convention used by sites such as the Claude Code guide.

The catalog stays deliberately small. It does not load the complete instructions for 59 skills into one context window. Each entry links to its own Markdown page:

```text
/skills/testing/tdd-task.md
/skills/database/jooq-best-practices.md
/skills/framework/spring-boot.md
```

In detail:

- The catalog entry -> tells the agent what the skill does and when it may apply
- The detail page -> adds matching signals, provenance, compatibility, evaluation evidence, and installation instructions
- The installed `SKILL.md` -> remains authoritative for the workflow the agent actually follows

This follows the progressive-disclosure model used by the [Agent Skills specification](https://agentskills.io/specification): discover from name and description, load the instructions when the task matches, then read supporting files only when the skill references them.

## Review project fit before installation

My first implementation generated a Markdown page for every skill and taught the agent where to copy it. That fixed discovery, but did not check whether the skill fit the project.

A generic skill does not know the project-specific details that usually decide whether its advice works:

- Build and test facts: exact commands plus the Spring Boot, Kotlin, Java, and library versions
- Project conventions: architecture boundaries, fixtures, base classes, domain terminology, and existing agent instructions

Every detail page now asks for a project-context review before installation. The agent must inspect the repository, explain why the skill fits, check for overlapping instructions, and identify the context the skill is missing.

It then recommends the smallest maintainable addition. I prefer a project-local reference, overlay, or companion instruction over editing the upstream skill directly, because upstream changes become harder to merge into an edited copy.

The [TDD Task skill](https://github.com/jvm-skills/jvm-skills/blob/main/.claude/skills/tdd-task/SKILL.md) already uses this pattern. Its reusable workflow lives in `SKILL.md`; a local `references/project.md` can supply the project's test base classes, focused test command, and E2E setup. The upstream workflow stays updateable while the repository provides the facts only it can know.

## Two installation paths on the website

Every skill card now opens an installation dialog with two options.

The CLI option produces a source-specific command:

```bash
npx skills add https://github.com/owner/repository/tree/main/path/to/skill
```

The open-source [skills CLI](https://github.com/vercel-labs/skills) detects supported agents and asks where to install the skill. I do not add `--yes`, `--global`, or a fixed client to the generated command, so the user still chooses the installation scope and target agent. The dialog also states that the CLI requires Node.js and may collect anonymous installation telemetry.

The Agent review option copies the longer evaluation prompt. It does not install anything. The agent first checks fit and missing context, then waits for approval.

For a collection, the agent selects individual skills instead of copying the repository into one large skill directory. Its guide tells the agent to preserve each selected directory with its scripts, references, templates, and assets.

## A new website ahead of Big Sky

I also refreshed the website ahead of Big Sky Dev Conference in Bozeman on July 25, 2026. The directory, blog, evaluation pages, conference archive, and new Big Sky landing page now share the visual language of the talk.

The talk is called **Agentic Engineering for JVM Developers**. It focuses on the part that gets harder once agents can produce code quickly: aligning on the right change, proving the implementation, and keeping human review focused on risk instead of reading every generated line with equal attention.

The guides support that review workflow by requiring repository evidence before installation. Inspecting the repository, challenging the recommendation, and adding the missing local context gives the agent a better chance of applying the skill correctly.

The implementation is available in the [jvm-skills repository](https://github.com/jvm-skills/jvm-skills). On the website, open **For agents** to browse the generated reference and detail pages.

If an agent recommends the wrong skill for your repository, report the evidence it missed. I can use that feedback to improve the matching guidance.
