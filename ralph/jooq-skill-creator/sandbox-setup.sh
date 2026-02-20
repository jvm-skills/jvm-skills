#!/bin/bash
# Setup Docker sandbox for jOOQ skill creator with MCP access
set -e

cd "$(dirname "$0")"
SANDBOX_NAME="claude-ralph-jooq"
PROJECT_DIR="$(cd ../.. && pwd)"

echo "=== Setting up sandbox: $SANDBOX_NAME ==="
echo "Project dir: $PROJECT_DIR"

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
echo "Run Ralph:"
echo "  ./ralph-jooq-once.sh"
echo "  ./afk-ralph-jooq.sh 50"
echo ""
echo "Manage:"
echo "  docker sandbox ls"
echo "  docker sandbox rm $SANDBOX_NAME"
