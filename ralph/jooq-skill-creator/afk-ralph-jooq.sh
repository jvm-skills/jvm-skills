#!/bin/bash
# AFK Ralph loop: process N jOOQ blog articles unattended
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <iterations>"
  exit 1
fi

cd "$(dirname "$0")"
unset CLAUDECODE

START_TIME=$(date +%s)

for ((i=1; i<=$1; i++)); do
  echo "=== Iteration $i/$1 ==="

  result=$(docker sandbox run claude-ralph-jooq -- --dangerously-skip-permissions --add-dir ~/.claude/skills -p \
    "@ralph/jooq-skill-creator/process-jooq-article.md")

  echo "$result"

  # Extract article title + action from last table row (ignore summary lines)
  last_row=$(grep '^|' blog/processing-log.md | grep -v '^|[-#]' | tail -1)
  article_title=$(echo "$last_row" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/, "", $3); print $3}')
  action=$(echo "$last_row" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/, "", $7); print $7}' | sed 's/pped$/p/; s/ed$//')
  commit_msg="jooq-${action:-process}: ${article_title:-iteration $i}"

  # Commit skill changes after each iteration
  git add ../../.claude/skills/jooq-best-practices/ blog/
  if git commit -m "$commit_msg" --no-verify 2>/dev/null; then
    COMMIT_HASH=$(git rev-parse --short HEAD)
    # Append commit hash to last table row in processing log
    last_row_num=$(grep -n '^|' blog/processing-log.md | grep -v '^[0-9]*:|[-#]' | tail -1 | cut -d: -f1)
    if [ -n "$last_row_num" ]; then
      sed -i '' "${last_row_num} s/|[[:space:]]*$/| ${COMMIT_HASH} |/" blog/processing-log.md
    fi
    # Stage updated log with hash
    git add blog/processing-log.md
    git commit --amend --no-edit --no-verify 2>/dev/null
  fi

  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "All articles processed after $i iterations."
    break
  fi

  echo "---"
done

END_TIME=$(date +%s)
ELAPSED=$(( END_TIME - START_TIME ))
MINUTES=$(( ELAPSED / 60 ))

# Capture summary stats for blog post
ARTICLES_FILE=blog/jooq_blog_articles.jsonl
PROCESSED=$(grep -c '"processed":true' "$ARTICLES_FILE" || echo 0)
REMAINING=$(grep -c '"processed":false' "$ARTICLES_FILE" || echo 0)
TOPIC_FILES=$(ls ../../.claude/skills/jooq-best-practices/knowledge/*.md 2>/dev/null | wc -l | tr -d ' ')
UNCERTAINTIES=$(grep -c "^## " ../../.claude/skills/jooq-best-practices/UNCERTAINTIES.md 2>/dev/null || echo 0)

cat >> blog/processing-log.md << EOF

---
**Run summary** ($(date '+%Y-%m-%d %H:%M')):
- Iterations this run: $i
- Duration: ${MINUTES}m ${ELAPSED}s total
- Articles processed so far: $PROCESSED / $(( PROCESSED + REMAINING ))
- Topic files: $TOPIC_FILES
- Open uncertainties: $UNCERTAINTIES
EOF

echo ""
echo "=== Summary ==="
echo "Iterations: $i | Duration: ${MINUTES}m | Processed: $PROCESSED | Remaining: $REMAINING | Topics: $TOPIC_FILES | Uncertainties: $UNCERTAINTIES"
