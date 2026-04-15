# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
## Critical Rules

- **Be extremely concise** in all interactions, plans, and commit messages. Sacrifice grammar for concision.
- **No legacy commentary**: when changing or replacing behavior, just write the new state. Never add comments explaining what was removed, what used to work, or why the old approach was replaced.
- **Compile after .kt changes**: `./gradlew compileKotlin compileTestKotlin detekt` — quiet/plain output is configured in `gradle.properties`; only errors/violations are shown.
- **Restart app after code changes**: use the `/restart` skill before verifying in the browser.
- **DB changes → migration first**: when planning, the first phase must be "Workflow for Database Migration"
- **All user-visible text in German. All developer-facing content (plans, docs, commits, comments) in English.**
- **When writing migrations use the design-postgres-table skill**
- **Use the `/test` skill to run tests** — accepts filter patterns: `/test *SetupTest *LobbyTest`.
- **Multi-instance safe**: no in-memory state for dedup/guards; use DB checks. Use `AdvisoryLock.kt` for distributed consensus (hash semantic key to bigint, fail-fast, auto-released on tx end).
- **Verify before done**: never mark a task complete without proving it works (run tests, check logs, demonstrate correctness). For UI fixes, screenshot with agent-browser. For code fixes, verify ALL cases are covered.
- **Always use `/frontend` for UI work**: creating new HTML/components, redesigning existing pages, adjusting layouts, or any visual changes. Use it to design first, then implement, then verify with `agent-browser`.
- **Delete unused code** — never keep dead endpoints, constants, or methods "because tests reference them". Delete the code AND update the tests. Dead code is worse than no code.
- **Never suppress detekt violations** — fix the code instead (extract methods, restructure). If the rule is genuinely wrong for the pattern, ask the user before suppressing.
- **Commit after each phase** — when implementing a plan, commit after completing each phase

## Workflow Rules
- **Plan complex tasks**: for non-trivial work (3+ steps or architectural decisions), save a plan as `docs/dev/YYYY-MM-DD-hh-mm_plan-task-description.md`. Do NOT implement without confirmation.
When the plan is implemented completely move it to docs/dev/finished
- **Don't rabbit-hole**: if exploration isn't converging, summarize findings and ask before continuing.
- **When things break**, stop and re-plan rather than pushing a broken approach.

## MCP Usage

- **Use JetBrains MCP tools for refactoring**: Prefer `mcp__jetbrains__reformat_file` for formatting and `mcp__jetbrains__rename_refactoring` for renaming symbols across the project
- **Fix import issues with JetBrains MCP**: When there are unused/missing imports, call `mcp__jetbrains__reformat_file` - this automatically optimizes imports
- **Use JavaDoc Central MCP for JVM library documentation** (Spring, jOOQ, and all Maven Central artifacts) — queries `https://www.javadocs.dev/mcp`
- **Use jOOQ MCP for jOOQ documentation and DSL reference**
- **Use Context7 MCP only for non-JVM library/API documentation** (e.g. frontend libs, Tailwind, Alpine.js, HTMX)

## Product Information

PhotoQuest is a wedding photo game platform that turns guests into creative photographers through personalized photo missions. It creates a digital guestbook with photos, videos, and audio messages.

## Core Products

**PhotoQuest (Main Product)**: 500+ creative photo missions on printed cards with unique QR codes. Guests scan and upload directly. 30+ card designs on 250g paper.

**PhotoSafari (Simplified Version)**: Spontaneous uploads without specific tasks. Same QR system, lower barrier.

**Key Features**: digital guestbook, audio messages, live slideshow, bulk download.

If you need more product context: [produktwissen.md](docs/business/produktwissen.md)


## Build & Development Commands

```bash
# Compile only (use this to check for syntax errors)
./gradlew compileKotlin compileTestKotlin
```

**Application logs**: In dev, logs are written to `build/app.log`. When something isn't behaving properly at runtime (unexpected responses, errors, failing requests), read the tail of this file to check for exceptions, stack traces, or unexpected log output before asking the user.

## Architecture

### Package Structure

All code under `de.tschuehly.photoquest`:

- `analytics/` - Tracking events and analytics types
- `common/` - Shared config (`config/`) and exceptions (`exception/`)
- `core/` - Business/domain logic: `auth`, `event`, `file`, `payment`, `submission`, `task`, `wedding`, `user`, `reminder`
- `web/` - HTTP layer & server-rendered UI: controllers in `web/` and `web/page/**`, ViewComponents + templates in `web/page/**`
- `tracking/` - Cookie encryption, Meta conversions, tracking tags


**Rule**: New functionality must follow this separation:
- Business/domain logic → `core/<feature>/`
- HTTP controllers & endpoints → `web/**`
- ViewComponents & templates → `web/page/**`
- Shared config / cross-cutting concerns → `common/**`
- Tracking / analytics → `analytics/**` or `tracking/**`

### Key Technologies & Docs

When changing a component, update its corresponding doc.

- **Framework**: Spring Boot 4 + Jackson 3
- **View Layer**: Spring ViewComponent (Thymeleaf-based) with HTMX
- **Database**: PostgreSQL with jOOQ for type-safe SQL (generated code in `src/main/jooq`)
- **Migrations**: Flyway (changelogs in `src/main/resources/db/migration`)
- **Authentication**: Spring Security 7 (OAuth2/OIDC, Magic Link, Remember-Me) — update [auth](docs/architecture/auth.md)
- **Storage**: S3-compatible storage (AWS S3 or MinIO for development/testing)
- **Frontend**: Tailwind CSS 4 + DaisyUI 5, Alpine.js — update [tailwind-usage](docs/architecture/tailwind-usage-notes.md)
- **Email**: SES integration, scheduled jobs, webhooks — update [email](docs/architecture/email.md)
- **Testing**: Testcontainers, Playwright — update [playwright](docs/architecture/playwright-testing.md), [test-data](docs/architecture/test-data.md)
- **Analytics**: Application events, tracking — update [events](docs/architecture/application-events.md)
- **UI/Design**: Design system patterns — embedded in `/frontend` skill (`.claude/skills/frontend/SKILL.md`)
- **Onboarding**: Multi-step flow — update [onboarding](docs/architecture/onboarding-flow.md)
- **PDF**: pdfme viewer integration — update [pdfme-viewer](docs/architecture/pdfme-viewer.md)
- **Bot Blocking**: Servlet filter for scanner/bot traffic — update [bot-blocker](docs/architecture/bot-blocker.md)

## Conventions

Detailed conventions are in `.claude/rules/` (loaded automatically by file path):

- **Invariants** (SSoT — authz, concurrency, SSE pairing, output escaping, empty state, server-authoritative state, trust boundary, spec coherence) → `invariants.md` — **also consumed by `/interview`, `/review-fix`, `/codex:adversarial-review`, Ralph planner/executor, `/split-spec`. Add new cross-cutting bug classes here, not in the skills.**
- **Kotlin** (jOOQ, AdvisoryLock, exceptions, properties) → `kotlin-conventions.md`
- **ViewComponent & HTMX** (path constants, currentEvent guard, German text) → `viewcomponent.md`
- **Tailwind v4 + DaisyUI v5** (migration pitfalls, class renames) → `tailwind-daisyui.md`
- **Database migrations** (Flyway naming, jOOQ codegen) → `database-migration.md`
- **Testing** (base classes, Playwright, test data) → `testing.md`
- **Auth** (OTT, OAuth, Apple quirk, principal hierarchy) → `auth.md`
- **Email** (SES, idempotency, unsubscribe rules) → `email.md`
- **Analytics** (event publishing, dedup strategies) → `analytics-events.md`
- **Onboarding** (step flow, value-first, dynamic steps) → `onboarding.md`
- **Real-time SSE** (pg_notify, ranking game state machine) → `realtime-sse.md`
- **Subdomain auth** (cookie isolation, guest flow) → `subdomain-auth.md`
- **Payment** (Stripe integration) → `payment.md`
- **Svelte islands** (Svelte 5, Bun build) → `frontend-islands.md`

## Frontend

- **UI verification**: use `/agent-browser` to screenshot after creating/adjusting UI elements. Authenticated routes: `http://localhost:8443/dev/login?redirect=<target-path>`
- **agent-browser screenshots**: always save to `screenshots/` (gitignored) instead of `/tmp` — e.g. `agent-browser screenshot screenshots/my-page.png`
- **Images**: use `/image-modify` skill to properly size images


## IntelliJ Integration

- Open files in IntelliJ IDE: use `mcp__jetbrains__open_file_in_editor`
- Automatically open plan files after creating them