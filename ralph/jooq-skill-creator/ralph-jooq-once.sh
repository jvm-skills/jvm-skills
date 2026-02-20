#!/bin/bash
# Human-in-the-loop: process one article, watch what it does
# Run from project root or via: docker sandbox run claude

cd "$(dirname "$0")/../../.."

ARTICLES=scripts/ralph/jooq-skill-creator/blog/jooq_blog_articles.jsonl
if [ ! -f "$ARTICLES" ]; then
  echo "ERROR: $ARTICLES not found. Creating from source..."
  jq -c '.[]' scripts/ralph/jooq-skill-creator/jooq_blog_articles.json > "$ARTICLES" 2>/dev/null \
    || { echo "Source JSON not found either. Run the scraper first."; exit 1; }
fi

claude --dangerously-skip-permissions --add-dir ~/.claude/skills --output-format stream-json -p \
  "@scripts/ralph/jooq-skill-creator/process-jooq-article.md" \
  | jq -rj '.message?.content[]? | if .type == "thinking" then .thinking elif .type == "text" then .text else empty end // empty'
