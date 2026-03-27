---
name: restart-spring-boot
description: Restart the app via IntelliJ run configuration and wait until ready. Use after Kotlin code changes before browser verification. NOT needed for HTML template changes (LiveReload handles those automatically).
---

# Restart App Skill

Restart the Spring Boot app via IntelliJ and wait for readiness.

**When to use**: Only after `.kt` file changes. HTML template changes are auto-reloaded by Spring DevTools LiveReload — just refresh the browser.

## Instructions

1. **Stop the old app and wait for port release** (Bash tool):
   ```bash
   ./scripts/restart-app.sh stop
   ```
   This kills the process on port 8443 and waits for it to release.

2. **Start the app** via JetBrains MCP (this will timeout — that's expected):
   ```
   mcp__jetbrains__execute_run_configuration(
     configurationName: "DevelopmentPhotoQuest",
     timeout: 5000
   )
   ```

3. **Wait for readiness** (Bash tool, timeout 60000):
   ```bash
   ./scripts/restart-app.sh wait
   ```

4. **Report result**: "App restarted and ready" or "App failed to start — check `build/app.log`".
