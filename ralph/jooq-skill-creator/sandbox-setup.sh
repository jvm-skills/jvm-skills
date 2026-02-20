#!/bin/bash
# Setup Docker sandbox for jOOQ skill creator with MCP access
set -e

SANDBOX_NAME="claude-ralph-jooq"
PROJECT_DIR=~/IdeaProjects/PhotoQuest

echo "=== Setting up sandbox: $SANDBOX_NAME ==="
if docker sandbox ls 2>/dev/null | grep -q "$SANDBOX_NAME"; then
  echo "Sandbox '$SANDBOX_NAME' already exists, reusing it."
else
  echo "Creating sandbox..."
  docker sandbox create --name "$SANDBOX_NAME" claude "$PROJECT_DIR"
fi

echo "=== Configuring network: allow MCP + blog access ==="
docker sandbox network proxy "$SANDBOX_NAME" \
  --allow-host blog.jooq.org \
  --allow-host jooq-mcp.martinelli.ch \
  --allow-host registry.npmjs.org \
  --allow-host api.anthropic.com \
  --allow-host statsig.anthropic.com \
  --bypass-host localhost \
  --bypass-cidr 127.0.0.0/8

echo ""
echo "=== Sandbox ready ==="
echo "Run:"
echo "  docker sandbox run $SANDBOX_NAME -- ./scripts/ralph/jooq-skill-creator/ralph-jooq-once.sh"
echo "  docker sandbox run $SANDBOX_NAME -- ./scripts/ralph/jooq-skill-creator/afk-ralph-jooq.sh 50"
echo ""
echo "Manage:"
echo "  docker sandbox ls"
echo "  docker sandbox rm $SANDBOX_NAME"
