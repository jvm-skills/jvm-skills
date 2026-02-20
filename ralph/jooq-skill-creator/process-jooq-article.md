# Process next jOOQ blog article

You are building a jOOQ expert knowledge base by processing blog articles one at a time.
Articles are sorted **newest-first** — this is critical for handling outdated info.
Target version: **jOOQ 3.20** on **PostgreSQL**.

## Input

- Articles list: `scripts/ralph/jooq-skill-creator/blog/jooq_blog_articles.jsonl` — one JSON object per line: `{url, title, description, date, tags, processed}`
- Knowledge base: `.claude/skills/jooq-best-practices/knowledge/`
- Skill file: `.claude/skills/jooq-best-practices/SKILL.md`
- Uncertainties log: `.claude/skills/jooq-best-practices/UNCERTAINTIES.md`

## Your task

1. **Find the first unprocessed article** using Bash: `grep -n '"processed":false' scripts/ralph/jooq-skill-creator/blog/jooq_blog_articles.jsonl | head -1` — this returns the line number and article JSON. Use the line number as the article index.
2. **If no unprocessed articles remain**, output `<promise>COMPLETE</promise>` and stop
3. **Fetch the full article** using WebFetch on the article's URL
4. **Classify** the article into one of:
   - **jooq-api**: jOOQ-specific API patterns, DSL usage, features, configuration
   - **sql-pattern**: General SQL best practices, window functions, CTEs, anti-patterns (timeless, applicable through jOOQ)
   - **skip**: Not relevant (Java opinion pieces, hiring, conferences, non-SQL topics, release announcements without actionable patterns, posts about jOOQ internals/development process)
5. **If skip**: mark processed and stop (step 8)
6. **Check for outdated info** (see Outdated Info Strategy below)
7. **Extract knowledge** and write to the appropriate topic file in the knowledge directory:
   - Determine the topic (e.g., `multiset.md`, `cte-patterns.md`, `window-functions.md`, `anti-patterns.md`, `type-safe-mapping.md`, `implicit-joins.md`, etc.)
   - If the topic file exists, read it first before writing
   - Write concise best-practice nuggets following the Topic File Format below
   - Do NOT dump the entire article — extract only actionable patterns
8. **Mark processed**: use Bash with `sed` to update the line in-place: `sed -i '' 'LINEs/\"processed\":false/\"processed\":true/' scripts/ralph/jooq-skill-creator/blog/jooq_blog_articles.jsonl` (replace LINE with the line number from step 1)
9. **Update the skill**: read and update `.claude/skills/jooq-best-practices/SKILL.md` (see Skill Update below)
10. **Log for blog post**: append a row to `scripts/ralph/jooq-skill-creator/blog/processing-log.md` (see Blog Log below)
11. **Report** what you did: article title, classification, which topic file was updated (or "skipped")

## Outdated Info Strategy

Articles are processed newest-first, so **existing entries in topic files are always from newer articles**.

When processing an older article and the topic file already has entries:

1. **Read the existing topic file first**
2. **If the older article teaches the same pattern** already covered by a newer entry → skip it, don't add a duplicate
3. **If the older article has a pattern NOT yet covered** → add it normally
4. **If the older article contradicts a newer entry** (different API, deprecated approach) → **don't add it**. Instead:
   - Add a `> **Supersedes**: older approach X from [article](url)` note to the existing newer entry
   - Use jOOQ MCP tools (`searchDocumentation`, `getQueryDslReference`) to verify which approach is current
5. **If you're unsure whether syntax is still valid** (old article, no newer entry to compare against):
   - Use jOOQ MCP tools to check — only in this case, not routinely
   - If confirmed outdated, skip. If confirmed current or can't determine, add with date context
   - **If still uncertain after MCP check**: log it to `UNCERTAINTIES.md` (see below) and add the pattern with a warning
6. **Version-specific patterns**: if a pattern requires jOOQ 3.x+, note it as `**Since**: jOOQ 3.x`

**Key rule**: Only contact the jOOQ MCP server when there's a conflict or uncertainty. Not on every article.

## Uncertainties log

When you encounter something you can't resolve, append to `.claude/skills/jooq-best-practices/UNCERTAINTIES.md`:

```markdown
## [topic-file] Question or uncertainty
**From**: [Article title](url) (YYYY-MM-DD)
**Status**: open
**Context**: Brief description of what's uncertain and why
```

Log uncertainties for:
- Syntax you can't confirm is still valid in jOOQ 3.20
- Conflicting advice between two articles where neither is clearly newer
- Patterns that may only apply to specific databases (not PostgreSQL)
- API features that might have been removed or renamed

## Topic file format

```markdown
# Topic Title

## Pattern: Short name
**Source**: [Article title](url) (YYYY-MM-DD)
**Since**: jOOQ 3.x (only if version-specific)

Description of the pattern/best practice.

\```kotlin
// Code example using jOOQ DSL
\```

---
```

## Skill update (after each article)

After writing to a topic file, update `.claude/skills/jooq-best-practices/SKILL.md`:

1. **Read the current SKILL.md**
2. Update the `## Knowledge base` section to list all topic files with a one-line description:
   ```
   - [multiset.md](knowledge/multiset.md) — Nested collections with MULTISET and JSON aggregation
   - [window-functions.md](knowledge/window-functions.md) — ROW_NUMBER, RANK, LEAD/LAG patterns
   ```
3. If the article revealed a new **core rule** (a universally applicable best practice), add it to the `## Core rules` section
4. Keep SKILL.md under 100 lines — it's an index, not the knowledge itself

## Blog log

After each article (including skips), append one row to `scripts/ralph/jooq-skill-creator/blog/processing-log.md`:

```
| {iteration#} | {article title (truncated to 50 chars)} | {date} | {classification} | {topic file or "-"} | {added/merged/skipped/superseded} | {brief note if interesting} | |
```

Count the iteration number by counting existing rows in the table.

Also capture noteworthy events in a separate `scripts/ralph/jooq-skill-creator/blog/highlights.md` file (create if missing, append):
- First time a topic file is created (new topic discovered)
- When an older article contradicts a newer one (evolution example)
- When MCP was consulted to resolve a conflict
- When an uncertainty was logged
- Interesting stats (e.g., "5 articles in a row skipped — all Java opinion pieces from 2013")
- When a pattern was added with a version note (shows API evolution across jOOQ versions)
- When a doc-seeded entry (source marked `(docs)`) got enriched by a blog post

These highlights make good anecdotes for the blog post.

## Rules

- ONE article per invocation
- Keep extractions concise — this is a reference, not a blog mirror
- Target: jOOQ 3.20 on PostgreSQL — skip patterns that only apply to other dialects unless they're educational
- Always read existing topic files before writing to avoid duplicates
- Only use jOOQ MCP tools when there's a conflict between articles or you suspect outdated syntax — not on every article
- If an article is purely about SQL (no jOOQ-specific content), still extract it — SQL patterns are valuable when using jOOQ
- Log uncertainties rather than guessing — the UNCERTAINTIES.md file exists for this purpose
