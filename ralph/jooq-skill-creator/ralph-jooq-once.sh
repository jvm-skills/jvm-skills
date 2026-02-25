#!/bin/bash
# Human-in-the-loop: process one article, watch what it does
# Run from project root or via: docker sandbox run claude

cd "$(dirname "$0")"

ARTICLES=blog/jooq_blog_articles.jsonl
if [ ! -f "$ARTICLES" ]; then
  echo "ERROR: $ARTICLES not found. Creating from source..."
  jq -c '.[]' jooq_blog_articles.json > "$ARTICLES" 2>/dev/null \
    || { echo "Source JSON not found either. Run the scraper first."; exit 1; }
fi

unset CLAUDECODE
docker sandbox run claude-ralph-jooq -- --dangerously-skip-permissions --model claude-sonnet-4-6 --add-dir ~/.claude/skills -p \
  "@ralph/jooq-skill-creator/process-jooq-article.md"
