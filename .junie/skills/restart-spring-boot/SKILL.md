---
name: restart-spring-boot
description: Restart the app via IntelliJ run configuration and wait until ready. Use after Kotlin code changes before browser verification. NOT needed for HTML template changes (LiveReload handles those automatically).
context: fork
agent: general-purpose
---

# Restart App Skill

Restart the Spring Boot app via IntelliJ and wait for readiness.

**When to use**: Only after `.kt` file changes. HTML template changes are auto-reloaded by Spring DevTools LiveReload — just refresh the browser.

## Instructions

1. **Stop the old app and wait for port release** (Bash tool):
   ```bash
   ./scripts/restart-app.sh stop
   ```
   This kills the process on the app port and waits for it to release. Check `references/project.md` for the project's port number.

2. **Start the app** via JetBrains MCP (this will timeout — that's expected):
   ```
   mcp__jetbrains__execute_run_configuration(
     configurationName: "<run-config-name>",
     timeout: 5000
   )
   ```
   Check `references/project.md` for the exact run configuration name.

3. **Wait for readiness** (Bash tool, timeout 60000):
   ```bash
   ./scripts/restart-app.sh wait && touch .claude/.last-restart
   ```

4. **Check for new errors** (Bash tool — only if a log-check hook exists):
   ```bash
   ./.claude/hooks/post-bash-log-check.sh < /dev/null
   ```
   If the project has a post-restart log-check hook (path in `references/project.md`), run it to scan `build/app.log` for new ERROR entries since the last check. If errors are found, investigate and fix them before proceeding. If no hook exists, skip this step.

5. **Report result**: "App restarted and ready" or "App failed to start — check `build/app.log`".

## Project Customization

Read `references/project.md` in this skill's directory if it exists. It provides project-specific context:
- App port
- IntelliJ run configuration name
- Post-restart log-check hook path (if any)
- Any other project-specific patterns
