---
name: spec-to-plan
description: Turn a spec into a multi-phase implementation plan using tracer-bullet vertical slices with TDD. Use when user wants to break down a spec, create an implementation plan, or plan phases.
---

# PRD to Plan

Break a PRD/spec into a phased implementation plan using vertical tracer-bullet slices. Output is a Markdown file in
`docs/dev/`.

## Process

### 1. Confirm the PRD is in context

The PRD should already be in the conversation. If not, ask the user to paste it or point to the file.

### 2. Explore the codebase

If you have not already explored the codebase, do so to understand the current architecture, existing patterns, and
integration layers.
Read relevant files in [architecture](docs/architecture)

### 3. Identify durable architectural decisions

Before slicing, lock in decisions that span all phases:

- Route structures / URL patterns (as constants)
- Database schema shape (tables, columns, constraints, indexes)
- Key data models / domain classes
- Authentication / authorization approach
- Real-time communication pattern (SSE channels, websockets, messaging) — if applicable
- Package placement (`core/<feature>/` for logic, `web/<area>/<feature>/` for UI)

These go in the plan header so every phase can reference them.

### 4. Verify user story coverage

Before slicing, check the spec's `## User Stories` section:

- **Every story must map to at least one future phase.** If a story has no home, a phase is missing.
- **Navigation/entry point stories** (how the user arrives at the feature) must be covered — typically as a dedicated phase or merged into the first UI phase.
- If the spec lacks user stories, STOP and ask the user to run `/interview` first or write them now.

### 5. Draft vertical slices

Break the PRD into **tracer bullet** phases. Each phase is a thin END-TO-END slice.

**Phase 0 is always Database Migration** — schema must exist before ORM/DSL codegen.

<vertical-slice-rules>
- Each slice delivers a NARROW but COMPLETE user-visible behavior through ALL layers: service + controller + view/template + test
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
- Do NOT include file names, function signatures, or implementation details likely to change
- DO include durable decisions: route paths, schema shapes, domain class names
- Each slice that creates/changes UI should follow: design → implement → verify → refine → verify
- Each slice ends with a commit checkpoint
- **Each phase must list which user stories (US-N) it covers**
- Any phase with a state transition should include an end-to-end test that verifies the transition from every affected role's perspective
</vertical-slice-rules>

**TDD in each slice**: List test scenarios as acceptance criteria. End-to-end tests must **interact** with every button, form, and link — not just assert visibility. Verify the result of each interaction (page navigates, content updates, state changes). During implementation, follow red-green-refactor:

1. Write ONE failing test
2. Write minimum code to pass
3. Repeat for next test
4. Refactor after a logical group passes

**Test approach selection** — each phase must specify which test type:

| Scenario                                   | Test approach          |
|--------------------------------------------|------------------------|
| Service/repository logic, DB queries       | Integration tests with real DB |
| File uploads, external storage             | Integration tests with mocks/stubs |
| Browser-visible UI, full user flows        | End-to-end browser tests |

### 6. Quiz the user

Present the proposed breakdown as a numbered list. Per phase show:

- **Title**: short descriptive name
- **User stories**: which US-N this phase covers
- **Delivers**: what user-visible behavior works after this phase

After the list, show a **coverage check**: list any user stories NOT covered by any phase. If there are uncovered stories, add phases or explain why they're out of scope.

Ask:

- Does the granularity feel right?
- Should any phases be merged or split?
- Missing edge cases or constraints?

Iterate until the user approves.

### 7. Write the plan file

Write as `docs/dev/YYYY-MM-DD-hh-mm_plan-<feature>.md`. Open in IDE after writing.

Keep the plan SCANNABLE — aim for 2-6 lines per phase section. No code snippets unless they capture a durable decision (
schema shape, route constant). The plan is a compass, not a GPS.

<plan-template>
# Plan: <Feature Name>

> Source: <link to spec file>

## Architectural decisions

- **Routes**: path patterns, API endpoints
- **Schema**: table shapes (columns, types, constraints) — if applicable
- **Models**: domain classes in appropriate package
- **Auth**: who accesses this, which security rules
- **Real-time**: channel name, payload shape (if applicable)

---

## Phase 0: Database Migration (if applicable)

Design tables and create migration. Add test fixtures as needed.

- [ ] Migration runs, codegen completes
- [ ] Fixtures available
- [ ] `/commit`

---

## Phase N: <Verb + User-Visible Outcome>

**User stories**: US-N, US-M

<2-3 sentences: what end-to-end behavior this slice delivers>

**Test** (appropriate test type):

- <scenario>: <expected behavior>
- <scenario>: <expected behavior>

**Verify**: `/test *FilterPattern`

- [ ] Tests green
- [ ] Refactor (`/simplify`)
- [ ] `/commit`

---

<!-- For UI phases, add: -->

## Phase N: <Verb + UI Outcome>

**User stories**: US-N, US-M

<2-3 sentences: what end-to-end behavior this slice delivers>

**UI**: design → implement → verify → refine → verify

**Test** (end-to-end tests):

- <scenario>: <expected behavior>

**Verify**: `/test *FilterPattern` + UI verification

- [ ] Tests green
- [ ] Refactor (`/simplify`)
- [ ] `/commit`

---

## Coverage check

All user stories covered: US-1 ✓, US-2 ✓, US-3 ✓, ...

Uncovered stories: (none — or list with justification)
  </plan-template>
