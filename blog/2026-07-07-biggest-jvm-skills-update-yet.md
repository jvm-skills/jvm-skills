---
title: "The Biggest jvm-skills Update Yet"
slug: biggest-jvm-skills-update-yet
date: 2026-07-07
draft: false
author: Thomas Schilling
description: "Today I'm publishing the largest set of additions jvm-skills has ever had: 25 new listings from the engineers who build Camel, Quarkus, Kotlin, and the JVM itself, and how a skill-scout loop did the curation work I never had time for."
skills:
  - framework/camel-route-developer
  - framework/gemini-java-sdk
  - tool/jstall
  - tool/qs-kotlin
  - framework/spring-batch-6
  - language/java-best-practices-stephanj
  - language/kotlin-language-features
  - framework/microprofile-server
tags:
  - announcement
  - skill-scout
  - curation
---

Today I'm publishing the biggest update in the history of jvm-skills: **25 new listings** across framework, language, tool, testing, database, and workflow. Previous releases added a skill or two at a time; this one adds twenty-five at once.

And I didn't write any of them.

## The work I never had time for

The premise of jvm-skills has always been that the best JVM skills come from the people who actually build the ecosystem: the maintainers of Camel, Quarkus, Kotlin tooling, the JVM diagnostics folks. Not generic "write good Java" prompts, but skills that teach an agent something it wouldn't otherwise know.

The problem is that finding those skills is real work. The people who write them are conference speakers, library authors, and Java Champions who quietly drop a `SKILL.md` into a workshop repo or a `.claude/skills/` folder and never announce it. To find them you have to go speaker by speaker, repo by repo, read what they published, and judge whether it clears the bar.

That doesn't scale by hand, and I never had the time to do it properly. The catalog grew whenever I tripped over something good, and most of it I never found.

## The skill-scout loop

I stopped doing it by hand and built a pipeline instead. I call it **skill-scout**.

The loop starts from the one list I already trust: conference speaker rosters. If you spoke at Devoxx, JavaZone, KotlinConf, or Spring I/O, you're worth listening to. From there:

1. **Harvest the roster.** Pull the speaker list off each conference site: a plain fetch, or a headless browser for the JavaScript-heavy ones that don't give it up easily.
2. **Follow every speaker to their code.** Resolve each one to GitHub and tree-scan their non-fork repositories for skill files: `SKILL.md`, `AGENTS.md`, `.cursorrules`, `.claude/skills/`.
3. **Judge each candidate, then judge the judgment.** A fast model gives a first verdict: real skill, needs a look, or reject. A stronger model then re-checks every proposed acceptance *adversarially*, actively trying to knock it down.
4. **Record everything.** Survivors, rejections, and the reason for each land in a CSV store, so nothing is ever re-judged.

It's deliberately slow: GitHub's API is effectively a global rate limit, so it scans one conference at a time, roughly fifteen minutes each, and runs overnight. Over several nights it worked through about **75 conferences** and surfaced **483 candidate skills**.

## The rulebook wrote itself

I didn't write the approval rulebook. The loop did.

The bar for what gets listed already existed in the repo, just not in one place: 31 approved listings, the contributing guide, and about 75 conferences of accept/reject decisions the loop had already made and recorded, each with a reason. Instead of writing the rules by hand, I gave all of that to Claude Fable 5 at max reasoning and had it consolidate the history into one standalone rulebook a cold reviewer could apply.

It came back with eight hard gates, an eleven-reason taxonomy of disqualifiers, a deduplication policy, and worked pass/fail examples, every rule citing a real repo. It also corrected one of its own rules mid-run: it had flagged a set of skills as suspicious for sharing an identical line count, then worked out that the uniform length was an artifact of the scanner's read cap, not evidence of anything, and revised the rule.

Then the rulebook went to work on all 483 candidates: eighteen Opus 4.8 judge subagents, one per cluster, reading around 140 actual skill files and verifying roughly 70 API claims against the libraries they described. It killed 87 rows from a marketplace skill-farm, 30 that leaned on APIs which don't exist (checked against the real library), and 8 that were byte-identical copies of someone else's skill set.

Twenty-five cleared it.

## What made it in

The additions fall into three trust tiers.

**From the library authors themselves** (official trust: the person who wrote the skill also maintains the thing it's about):

- [Camel Route Developer](https://github.com/zbendhiba/camel-route-developer) and [Quarkus Extension Development](https://github.com/zbendhiba/my-open-skills), by Zineb Bendhiba (Apache Camel, Red Hat)
- [Gemini Java SDK](https://github.com/glaforge/gemini-interactions-api-sdk), by Guillaume Laforge (Google, Apache Groovy)
- [jstall: JVM live diagnostics](https://github.com/parttimenerd/jstall), by Johannes Bechberger (SapMachine, JVM profiling)
- [qs-kotlin](https://github.com/techouse/qs-kotlin), by Techouse

**Curated from acknowledged experts:**

- [Java 21 Best Practices](https://github.com/stephanj/claude-code-collections), by Stephan Janssen (Devoxx)
- [Kotlin 2.2/2.3 Language Features](https://github.com/antonarhipov/kotlinconf-sdd) and [Spring Batch 6 Migration](https://github.com/antonarhipov/agentskills), by Anton Arhipov (JetBrains)
- [Java 25 Conventions, MicroProfile Server, and Single-File Scripting](https://github.com/AdamBien/airails), by Adam Bien (Java Champion)
- [Java LTS Upgrade Guides 8→25](https://github.com/brunoborges/gh-appmod) and [macOS Notarization for JavaFX](https://github.com/brunoborges/fx2048), by Bruno Borges (Microsoft)
- [JFR Recording Analysis](https://github.com/victorrentea/performance-profiling), by Victor Rentea (Java Champion)
- [Kotlin API Design Review and POJO→Data-Class Refactoring](https://github.com/jbaruch/kotlin-tutor), by Baruch Sadogursky
- [Quarkus + LangChain4j Scaffolding](https://github.com/eldermoraes/quarkus-agentic-scaffolding), by Elder Moraes (Red Hat)
- [Kotlin REPL Prototyping](https://github.com/nomisRev/koog-workshop), by Simon Vergauwen (Arrow)
- [The jabrena JVM collection](https://github.com/jabrena/cursor-rules-java), by Juan Antonio Breña Moral
- [Oracle OKafka Java Clients](https://github.com/anders-swanson/oracle-database-code-samples), by Anders Swanson (Oracle)
- [Compose Desktop UI Testing](https://github.com/Mr3zee/Release-Wizard), by Mr3zee

**Community-trust utilities** that teach something specific:

- [Konveyor MTA Migration Analysis](https://github.com/sshaaf/mta-skill), by Syed M. Shaaf
- [Malicious-PDF Validation with PDFBox](https://github.com/righettod/code-assistant-skills-security-utils), by Dominique Righetto (OWASP)
- [Native Firebase in Kotlin Multiplatform](https://github.com/dyor/skills), by dyor

## Curation cuts both ways

An honest catalog also has to remove what no longer earns its spot.

Two older Java-quality listings I was carrying (a generic code-quality skill and a design-patterns one) are now superseded by the new best-practices and convention skills above. So they're gone. That's the less glamorous half of curation: the same bar that lets new skills in also retires the ones a better skill has replaced.

What matters is whether every entry still earns its place.

## What I actually learned

Automation didn't just add skills; it brought the judgment with it. The experts wrote the skills. The loop found them, judged them, and wrote the rulebook it judged them against, all from decisions the repo had already accumulated. What was left for me: setting the north star (list only skills that teach the AI something it doesn't already know), building the pipeline, and making the final calls.

Those final calls still matter, because the loop isn't always right. Applying its own consistency rule, it moved to delist four of my own workflow skills: the commit, spec, interview, and rebase skills I rely on and reference in other posts here. I put them back. Deciding when a consistent rule is still the wrong call is the part I don't want to automate.

More conferences are in the queue, and the loop keeps running.
