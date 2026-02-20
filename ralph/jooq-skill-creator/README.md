# jOOQ Skill Creator (Ralph)

Processes jOOQ blog articles into a knowledge base at `.claude/skills/jooq-best-practices/`.

## Setup

### 1. Scrape articles (one-time)

```bash
kotlin scripts/ralph/jooq-skill-creator/scrape-jooq-blog.main.kts
```

Creates `jooq_blog_articles.json`. The first run of any script auto-converts it to JSONL.

### 2. Run in Docker Sandbox (recommended)

```bash
# One-time: create sandbox with MCP + network access
./scripts/ralph/jooq-skill-creator/sandbox-setup.sh

# Then inside the sandbox:
./scripts/ralph/jooq-skill-creator/ralph-jooq-once.sh      # single article
./scripts/ralph/jooq-skill-creator/afk-ralph-jooq.sh 50    # AFK loop
```

The sandbox allows access to:
- `blog.jooq.org` — article fetching (WebFetch)
- `jooq-mcp.martinelli.ch` — jOOQ MCP server (conflict resolution)
- `registry.npmjs.org` — context7 MCP install via npx
- `api.anthropic.com` — Claude API

### 3. Run locally (no sandbox)

```bash
./scripts/ralph/jooq-skill-creator/ralph-jooq-once.sh      # single article
./scripts/ralph/jooq-skill-creator/afk-ralph-jooq.sh 50    # AFK loop
```

Uses `--dangerously-skip-permissions` — safe since the script only reads articles and writes markdown.

## Scripts

| Script | Purpose |
|--------|---------|
| `sandbox-setup.sh` | Create Docker sandbox with MCP + network access |
| `ralph-jooq-once.sh` | Process one article, stream thinking + text to stdout |
| `afk-ralph-jooq.sh <N>` | Loop N articles, auto-commit after each |
| `scrape-jooq-blog.main.kts` | Scrape article list from blog.jooq.org |
| `process-jooq-article.md` | Prompt template for Claude |

## Output

| Path | Content |
|------|---------|
| `blog/jooq_blog_articles.jsonl` | Article list with `processed` flags |
| `blog/processing-log.md` | Table of all processed articles |
| `blog/highlights.md` | Notable events (conflicts, new topics, MCP lookups) |
| `~/.claude/skills/jooq-best-practices/` | Knowledge base + SKILL.md index |
| `~/.claude/skills/jooq-best-practices/UNCERTAINTIES.md` | Unresolved questions |
