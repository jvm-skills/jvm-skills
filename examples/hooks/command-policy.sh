#!/bin/bash
# command-policy.sh — PreToolUse hook that replaces the broken permission system
#
# Why: Claude Code's permission wildcards don't match compound commands (&&, ;, |).
#      "Always Allow" saves dead verbatim strings. 240+ allow rules, still prompted constantly.
#      See: https://github.com/anthropics/claude-code/issues/30519
#
# How: Splits compound commands, checks each sub-command against allow/block lists.
#      Exit 0 + JSON {permissionDecision:"allow"} = skip prompt
#      Exit 0 + JSON {permissionDecision:"deny"} = hard block
#      Any other exit = fall through to permission prompt
set -uo pipefail
trap 'echo "[command-policy] ERROR on line $LINENO (exit $?): $(sed -n "${LINENO}p" "$0" 2>/dev/null)" >&2' ERR

approve() {
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
}

deny() {
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"BLOCKED: $1\"}}"
  exit 0
}

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || true)

[ -z "$COMMAND" ] && approve

# --- BLOCK LIST ---
# These patterns are checked against the FULL command string first.
# Any match = hard block, no matter where it appears.
BLOCK_PATTERNS=(
  "push --force"
  "push -f "
  "push -f$"
  "git reset --hard"
  "git clean -fd"
  "git clean -f "
  "git clean -f$"
  "git branch -D"
  "git checkout \."
  "git restore \."
  "rm -rf /\*"
  "--no-verify"
)

TEST_PATTERNS=(
  "gradlew test "
  "gradlew test$"
  "gradlew.*--tests"
)

for pattern in "${TEST_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE -- "$pattern"; then
    deny "Use the /test skill instead of running gradlew test directly"
  fi
done

for pattern in "${BLOCK_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE -- "$pattern"; then
    deny "'$COMMAND' matches dangerous pattern '$pattern'"
  fi
done

# --- rm -rf GUARD ---
# Only allow rm -rf on paths where ALL contents are git-tracked (revertible).
# Extracts every rm -rf target path and checks git ls-files.
if echo "$COMMAND" | grep -qE 'rm -rf '; then
  PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || echo "")}"
  while IFS= read -r rmpath; do
    [ -z "$rmpath" ] && continue
    # Resolve to absolute path
    [[ "$rmpath" != /* ]] && rmpath="$PROJECT_DIR/$rmpath"
    # Block if outside project (check BEFORE existence so we catch all cases)
    if [[ "$rmpath" != "$PROJECT_DIR"* ]]; then
      deny "rm -rf target '$rmpath' is outside the project directory"
    fi
    # Skip if path doesn't exist (already gone, harmless)
    if [ ! -e "$rmpath" ]; then
      continue
    fi
    # Check if any file under the path is NOT tracked by git
    untracked=$(cd "$PROJECT_DIR" && find "$rmpath" -type f 2>/dev/null | while IFS= read -r f; do
      rel="${f#$PROJECT_DIR/}"
      if ! git ls-files --error-unmatch "$rel" >/dev/null 2>&1; then
        echo "$rel"
      fi
    done)
    if [ -n "$untracked" ]; then
      deny "rm -rf '$rmpath' contains untracked files that cannot be reverted via git: $(echo "$untracked" | head -3)"
    fi
  done < <(echo "$COMMAND" | grep -oE 'rm -rf [^ ;|&]+' | sed 's/^rm -rf //')
fi

# --- ALLOW LIST ---
# Prefixes of commands that are safe to auto-approve.
# We split on && ; | and check each sub-command.
ALLOW_PREFIXES=(
  # Build tools
  "./gradlew"
  "gradlew"
  "PIPELINE=true ./gradlew"
  "JAVA_HOME="
  # Git (dangerous patterns already blocked above)
  "git"
  "GIT_EDITOR="
  # Package managers
  "bun"
  "npm"
  "npx"
  "node"
  "kotlin"
  "kotlinc"
  # System utilities
  "ls"
  "find"
  "cat"
  "head"
  "tail"
  "echo"
  "chmod"
  "mkdir"
  "cp"
  "mv"
  "rm"
  "kill"
  "touch"
  "test"
  "wc"
  "du"
  "sort"
  "xargs"
  "sed"
  "tr"
  "grep"
  "awk"
  "cut"
  "uniq"
  "diff"
  "env"
  "which"
  "open"
  "cd"
  "pwd"
  "true"
  "false"
  "["
  "printf"
  "set"
  "export"
  "unset"
  "read"
  "basename"
  "dirname"
  "realpath"
  "mktemp"
  "date"
  "sleep"
  "tee"
  # Media tools
  "ffmpeg"
  "cwebp"
  "convert"
  "magick"
  "identify"
  "sips"
  "pdftoppm"
  "gzip"
  "xxd"
  "unzip"
  # Docker & infra
  "docker"
  "supabase"
  "psql"
  "PGPASSWORD="
  "dig"
  # Dev tools
  "idea"
  "lsof"
  "jar"
  "java"
  "cloc"
  "gtimeout"
  "sysctl"
  "curl"
  "wget"
  "python3"
  # Project scripts
  "./scripts/"
  "./build-"
  "scripts/"
  "./.claude/"
  "bash"
  # Claude / worktrunk
  "claude"
  "wt"
  "wtc"
  # GitHub CLI
  "gh"
  # Agent browser
  "agent-browser"
  # Shell control flow (for, if, do, done, etc.)
  "for"
  "if"
  "do"
  "done"
  "then"
  "else"
  "fi"
  "while"
  "case"
  "esac"
  # Brew
  "brew"
  # Performance
  "pmset"
)

# Split command on && ; | and newlines, check each sub-command
check_command() {
  local cmd="$1"

  # Split on && ; | (but not ||) and newlines
  # Use python for reliable splitting that handles quoted strings
  local subcmds
  subcmds=$(python3 -c "
import shlex, re, sys
cmd = sys.argv[1]
# Tokenize respecting quotes, then rejoin and split on operators
# Replace quoted strings with placeholders to avoid splitting inside them
tokens = []
i = 0
result = []
in_quote = None
buf = []
for ch in cmd:
    if in_quote:
        buf.append(ch)
        if ch == in_quote:
            in_quote = None
    elif ch in ('\"', \"'\"):
        in_quote = ch
        buf.append(ch)
    else:
        buf.append(ch)
joined = ''.join(buf)
# Split on && ; | (not ||) and newlines, but only outside quotes
parts = []
current = []
i = 0
in_q = None
depth = 0  # track $(...) nesting depth
while i < len(joined):
    ch = joined[i]
    if in_q:
        current.append(ch)
        if ch == in_q:
            in_q = None
    elif ch in ('\"', \"'\"):
        in_q = ch
        current.append(ch)
    elif ch == '\$' and i+1 < len(joined) and joined[i+1] == '(':
        depth += 1
        current.append('\$(')
        i += 2
        continue
    elif ch == '(' and depth > 0:
        depth += 1
        current.append(ch)
    elif ch == ')' and depth > 0:
        depth -= 1
        current.append(ch)
    elif depth > 0:
        current.append(ch)
    elif ch == '&' and i+1 < len(joined) and joined[i+1] == '&':
        parts.append(''.join(current))
        current = []
        i += 2
        continue
    elif ch == '|' and i+1 < len(joined) and joined[i+1] == '|':
        current.append('||')
        i += 2
        continue
    elif ch == '|':
        parts.append(''.join(current))
        current = []
    elif ch == ';':
        parts.append(''.join(current))
        current = []
    elif ch == '\n':
        parts.append(''.join(current))
        current = []
    else:
        current.append(ch)
    i += 1
if current:
    parts.append(''.join(current))
for p in parts:
    p = p.strip()
    if p:
        print(p)
" "$cmd" 2>/dev/null) || {
    # If python parsing fails, output no decision → Claude Code shows permission prompt
    echo '{}'
    exit 0
  }

  local all_allowed=true

  while IFS= read -r subcmd; do
    [ -z "$subcmd" ] && continue

    # Strip leading cd prefix: "cd /some/path && git status" → "git status"
    subcmd=$(echo "$subcmd" | sed -E 's/^cd [^ ]+ *//; s/^ +//')
    [ -z "$subcmd" ] && continue

    # Strip variable assignments at the start: "FOO=bar cmd" → check "cmd"
    # Use POSIX classes ([^ ] and [ ]) — macOS sed doesn't support \S and \s
    local check_cmd="$subcmd"
    while echo "$check_cmd" | grep -qE '^[A-Za-z_][A-Za-z0-9_]*=[^ ]+[ ]'; do
      check_cmd=$(echo "$check_cmd" | sed -E 's/^[A-Za-z_][A-Za-z0-9_]*=[^ ]+[ ]+//')
    done

    local allowed=false
    for prefix in "${ALLOW_PREFIXES[@]}"; do
      if [[ "$check_cmd" == "$prefix"* ]]; then
        allowed=true
        break
      fi
    done

    if [ "$allowed" = false ]; then
      all_allowed=false
      break
    fi
  done <<< "$subcmds"

  if [ "$all_allowed" = true ]; then
    approve
  fi

  # Unknown command — output no decision → Claude Code shows permission prompt
  echo '{}'
  exit 0
}

check_command "$COMMAND"
