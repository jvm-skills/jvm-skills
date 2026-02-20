# Session Capture: Building a jOOQ Expert Skill with Ralph

## The Problem

We use jOOQ 3.20 with Kotlin + PostgreSQL in a Spring Boot 4 project. Claude Code has a jOOQ MCP server for API docs, but it lacks real-world patterns — the kind you learn from 14 years of Lukas Eder's blog posts. We wanted to turn 783 blog articles into a structured, version-aware Claude Code skill.

The challenge: jOOQ has evolved significantly since 2011. Old blog posts teach patterns that are now deprecated or superseded. We needed a system that handles this gracefully.

## Step 1: Scraping the Blog

Kotlin script (`scrape-jooq-blog.main.kts`) using OkHttp + Jackson + Jsoup. The jOOQ blog uses WordPress infinite scroll — POST to `?infinity=scrolling` returns JSON with `{type, html, lastbatch, currentday}`. Jsoup extracts title, description, date, and tags from each `<article>` element in the HTML.

Rate limiting (429 responses) handled with 1.5s base delay + exponential backoff. Result: 783 articles across 79 pages.

Each article stored as:
```json
{
  "url": "https://blog.jooq.org/...",
  "title": "Consider using JSON arrays instead of JSON objects for serialisation",
  "description": "When implementing the awesome MULTISET operator in jOOQ...",
  "date": "2025-08-11T14:43:10+02:00",
  "tags": ["java", "json", "json-array", "performance"],
  "processed": false
}
```

Sorted newest-first (2025 → 2011). The `processed` field doubles as the Ralph progress tracker — no separate progress file needed.

## Step 2: Designing the Skill Structure

```
.claude/skills/jooq-best-practices/
├── SKILL.md                  # Index + core rules (auto-updated each iteration)
├── UNCERTAINTIES.md           # Questions the loop couldn't resolve
└── knowledge/
    ├── anti-patterns.md       # Seeded from official docs
    ├── multiset.md            # Seeded from official docs
    ├── fetching-mapping.md    # Seeded from official docs
    └── ...                    # Progressively built by Ralph loop
```

Key design decisions:
- **Skill file is an index**, not the knowledge itself — stays under 100 lines
- **Topic-based files**, not per-article — related patterns merge into one file
- **Knowledge entries have source links + dates** — traceability back to the original post
- **UNCERTAINTIES.md** — things the loop couldn't resolve, queued for human review

## Step 3: Handling Outdated Information

Newest-first processing is the key insight. Since articles are processed from 2025 → 2011:

1. First entry in any topic file is always from the newest article
2. When an older article hits the same topic, the loop reads existing entries first
3. If the older article contradicts a newer entry → skip it, note it was superseded
4. If the older article adds a new pattern → add it, but verify syntax if suspicious
5. jOOQ MCP server only consulted on conflicts/uncertainty, not routinely
6. Unresolvable questions → logged to UNCERTAINTIES.md for later human review

Authority chain: **existing newer entries > jOOQ MCP docs (on conflict) > older blog posts**

## Step 4: Seeding from Official Docs

Before the blog loop, we seeded baseline knowledge from the jOOQ 3.20 manual:

- **anti-patterns.md**: 15 "don't do this" rules from the official reference (EXISTS vs COUNT, NOT EXISTS vs NOT IN, UNION ALL, schema anti-patterns)
- **multiset.md**: MULTISET value constructor for nested collections
- **fetching-mapping.md**: RecordMapper, fetchMap, fetchGroups, ad-hoc converters

Entries marked `(docs)` in their source field so the loop knows they came from official documentation and won't override them with blog opinions.

## Step 5: The Ralph Loop

```
scripts/ralph/jooq-skill-creator/
├── process-jooq-article.md   # The prompt — one article per invocation
├── ralph-jooq-once.sh         # Human-in-the-loop: process one, watch
├── afk-ralph-jooq.sh          # AFK: ./afk-ralph-jooq.sh 100
└── blog/
    ├── session-capture.md      # This file
    ├── processing-log.md       # Table row per article (auto-appended)
    └── highlights.md           # Noteworthy moments (auto-appended)
```

Each iteration:
1. Pick next `processed: false` article from JSON
2. Fetch full article via WebFetch
3. Classify: `jooq-api` / `sql-pattern` / `skip`
4. If not skip: extract patterns → topic file, update SKILL.md index + core rules
5. Mark `processed: true` in JSON
6. Log to processing-log.md and highlights.md

The `<promise>COMPLETE</promise>` sigil stops the loop when all articles are done.

## Step 6: Keeping the Skill Updated

The scraper and Ralph loop are rerunnable. When new blog posts appear:

1. **Re-run the scraper** — it outputs newest-first; new articles get `processed: false`
2. **Run the Ralph loop** — picks up only unprocessed articles
3. Since new articles are newer than everything in the knowledge base, they naturally take precedence

For jOOQ version upgrades (e.g., 3.20 → 3.21):
1. Update the version pin in the prompt and SKILL.md
2. Re-run the scraper to pick up release announcement + new feature posts
3. The loop processes them first (newest-first) and they supersede older patterns
4. Review UNCERTAINTIES.md for items that may now be resolved

The skill is also self-correcting during normal use: if a knowledge entry causes a compile error, the SKILL.md instructs Claude to check the jOOQ MCP server and the developer can update the entry.

## Stats (pre-loop)

- Total articles: 783
- Date range: 2011-07-20 → 2025-08-11
- Baseline knowledge files: 3 (from official docs)
- Baseline patterns: ~20

## Tools Used

- **Kotlin script**: OkHttp + Jackson + Jsoup for scraping
- **Claude Code**: Interactive session for system design
- **Ralph loop**: Claude Code CLI (`-p` mode) for unattended processing
- **jOOQ MCP server**: Conflict resolution (not every article)
- **WebFetch**: Full article retrieval during processing
