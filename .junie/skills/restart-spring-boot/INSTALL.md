# Installing `restart-spring-boot` in your project

This skill was born in a real project and still carries some of its DNA — port `8443`, IntelliJ run configuration `DevelopmentPhotoQuest`, log path `build/app.log`. One-time adaptation replaces those with your values.

## Prerequisites

- IntelliJ IDEA open on your project with a Spring Boot run configuration
- [JetBrains MCP](https://github.com/JetBrains/mcpjetbrains) enabled in Claude Code (`mcp__jetbrains__execute_run_configuration`)

## Steps

1. Copy `SKILL.md` → `.claude/skills/restart-spring-boot/SKILL.md` in your project
2. Copy `templates/restart-app.sh` → `scripts/restart-app.sh` and `chmod +x`
3. Paste this prompt into Claude Code:

> Adapt the `restart-spring-boot` skill I just installed to this project.
>
> 1. Read `src/main/resources/application.yml` (and active profile overrides) and update `PORT` in `scripts/restart-app.sh` and every `8443` mention in `SKILL.md`.
> 2. Call `mcp__jetbrains__get_run_configurations`, list the options, and ask me which one starts the dev server. Replace `DevelopmentPhotoQuest` in `SKILL.md` with that name.
> 3. Update the readiness probe `URL` in the script to a cheap public endpoint that returns 200 when the app is up (`/actuator/health`, or the login page, or `/` if unauthenticated).
> 4. Update the log file path (`build/app.log`) if my logs go somewhere else.
> 5. Run `./scripts/restart-app.sh stop` then `./scripts/restart-app.sh wait` once to confirm the stop + wait paths work.

## Verify

After adaptation, run `/restart-spring-boot` (or invoke the skill however your client exposes it). First invocation should stop any running app, trigger the IntelliJ run config, and block until the health check passes.
