---
title: "The 9-Step TDD Loop: Making AI Development Predictable and Proven"
slug: tdd-task-skill-walkthrough
date: 2026-04-21
draft: false
author: Thomas Schilling
description: "A disciplined 9-step TDD loop that forces AI agents to prove bugs before fixing them. See how we’re bringing rigorous software engineering standards to AI-driven development."
skills:
  - testing/tdd-task
  - testing/test-gradle
  - testing/ui-review
  - workflow/commit
tags:
  - tdd
  - claude-code
  - skills
  - spring-boot
  - ai-coding
---

A [PhotoQuest](https://photoquest.wedding/) customer spent onboarding curating 120 wedding tasks — keeping some, rejecting others. Months later she bumped her order to 200 printed cards. Cards 121–200 came back filled with tasks she had explicitly rejected — including one that made no sense at all: *"Foto mit der Mutter des Bräutigams"* on a wedding where the groom's mother had passed years ago.

The root cause was a clean one: rejecting a task hard-deleted the `event_task` row, and the fill query in `WeddingTaskService.getTasks` only excluded UUIDs still referenced by live rows. A deleted task left no trace, so the pool could re-pick it the moment more cards were ordered — which is exactly what happened when she bumped her quest card count from 120 to 200.

I fixed it with the [tdd-task](https://github.com/jvm-skills/jvm-skills/blob/main/.claude/skills/tdd-task/SKILL.md) skill. One `/tdd-task` invocation, nine steps, one commit. This post is the walk-through — every step as it actually ran.

## What the skill enforces

The skill isn't "write a test first." That's the easy part. What it actually enforces:

0. **Plan** — a `TaskCreate` todolist before any other action
1. **Understand** — read the closest analog end-to-end
2. **Clarify** — batch `AskUserQuestion` calls if there's real ambiguity
3. **Classify** — pick the test base class *and* decide if a Playwright E2E is mandatory
4. **Red** — write a test that compiles, runs, and fails with an *assertion error* (not a compile error)
5. **Green** — minimum code to pass
6. **Refactor** — `/simplify` pass
7. **Verify** — service test + Playwright + `ui-review` for template changes
8. **Beautify** — `/frontend` if the UI is new
9. **Commit** — `/commit`

The gates are the point. Without the skill the loop collapses into "write code that looks right, run tests, fix what breaks." With it, each phase has a hard exit criterion — and an agent that skips a gate will notice because the todolist still has an open task.

## Step 0 — Plan

First action of the session: nine `TaskCreate` calls for the nine steps. It sounds like theatre. It's not — and the reason is about attention, not accountability.

If I front-load all the workflow rules into the skill prompt, Claude reads them once at the top of the session and they drift out of working memory as the context fills with code, test output, and tool results. By the time the model is 200 tool calls deep into a refactor, the "don't skip the RED gate" instruction is competing with a wall of jOOQ query results for the same attention budget. It loses.

The todolist flips this. The workflow isn't described *once* at the top of a prompt — it's *reified* as nine tasks that sit in the context and get re-surfaced every time Claude marks one complete. Each `TaskUpdate` call reloads the list. The current step is always the one that's `in_progress`, and the next step is always the next `pending` task. Claude doesn't have to remember what comes next; it just reads the list.

A secondary benefit: anticipated sub-steps land on the list up front. Reading the bug description during Step 0, Claude saw a junction table would be needed and slotted `Migrate — add junction table + codegen` between Classify and Red before touching a single file. Claude also omitted Beautify — the fix was pure data-layer, no UI polish to do. I ended the session with 10 tasks for what the skill specifies as 9 — the extra one being the Playwright E2E that Step 2 Clarify decided was needed.

## Step 1 — Understand

Before writing anything, Claude reads `WeddingTaskService.kt` end to end. Two functions read from the `wedding_task` pool:

- `getTasks(eventId, questTaskCount, couple)` — the fill query, called on every render when the live task count is below `questCardCount`
- `getReplacementTaskInternal(eventId, couple)` — called after an interactive reject, picks a single replacement

Both excluded UUIDs the same way: `SELECT source_task FROM event_task WHERE event_id = ? AND source_task IS NOT NULL`. Neither knew about deletions.

The production incident was the fill path — the customer kept 120 tasks, then bumped her order to 200, and `getTasks` re-picked 80 rejected UUIDs. The replacement path was structurally the same bug but masked in practice by the `swapped_count` increment that happens on every reject — a just-rejected UUID has the highest count in the queue, so it won't resurface until hundreds of other rejects drag it back to the top. I fixed both for completeness, but only one cost the customer an 80-card reprint.

## Step 2 — Clarify

This step is new in v1.3 of the skill. Before it, Claude would guess and start coding. Now, when there's real ambiguity, it batches questions via `AskUserQuestion` — each with 2 – 4 concrete options I can click.

The bug had two real ambiguities:

1. **Scope** — which delete paths should record a rejection? Only the explicit user reject (`deleteTaskAndReplace`), or also the two internal trim paths?
2. **E2E** — the user-facing reject button lives in `TaskManagerComponent`. Do I add a Playwright E2E too, or is the service test enough?

I answered: explicit user reject only, plus a Playwright E2E. Those two answers cut the solution in half — no over-scoping, no under-scoping. The skill's `Clarify` rules are strict:

> Ask only when the answer changes what you build. Do NOT ask trivial style/naming choices. Do NOT ask "should I do TDD?" — that's why this skill is running.

If exploration answered everything, Claude marks the task complete with a one-line note and moves on. No fabricated questions to fill the step.

## Step 3 — Classify

This is where the *mandatory E2E rule* kicks in. Quote from the skill:

> If a user can trigger or see the change via the UI (any HTTP route, any rendered template, any HTMX/JS interaction), the task needs BOTH:
> 1. A unit/service/integration test that drives the change
> 2. A Playwright E2E test that proves the user-facing path works end-to-end

"Only a service-layer bug" is not a valid skip. I answered the Clarify question with "Add Playwright E2E too," so now I had two RED tests to write in Step 4.

Base class: `DataBaseTest` for the service layer, `PlaywrightBase` for the E2E. The project overlay (`references/project.md`) listed both, so no guesswork.

## Step 4 — Red

The skill's hard rule: the test must **fail with an assertion error**, not a compile error. A compile error only proves the code doesn't exist. An assertion error proves the *current* behavior is wrong.

For the DB migration, the skill said "run the migration and codegen first" — so Claude wrote `V25__event_rejected_wedding_task.sql` before the test. Junction table, `(event_id, wedding_task_id)` composite PK, `ON DELETE CASCADE` on both FKs.

Then four service tests. The headline one:

```kotlin
@Test
@Transactional
fun `rejected source uuid does not reappear via getReplacementTaskInternal`() {
    clearAndSeedPool(listOf(0, 0))
    weddingTaskService.getTasks(eventId, 1, couple)
    val initialSource = sourceTasksForEvent().single()

    val firstReject = weddingTaskService.deleteTaskAndReplace(
        eventTaskIdForSource(initialSource), eventId, couple
    )
    assertThat(firstReject.replacementTask).isNotNull()
    val replacementSource = sourceTasksForEvent().single()
    assertThat(replacementSource).isNotEqualTo(initialSource)

    val secondReject = weddingTaskService.deleteTaskAndReplace(
        eventTaskIdForSource(replacementSource), eventId, couple
    )
    assertThat(secondReject.replacementTask).isNull()
    assertThat(sourceTasksForEvent()).isEmpty()
}
```

Two wedding_tasks in the pool, both with `swapped_count=0`. Reject both. After the second reject, the replacement should be `null` — there are no un-rejected tasks left. The bug returned Task 1 (the first one rejected). RED.

Second test — the fill path — needed a subtler setup. The live code orders by `swapped_count asc`, and rejection *increments* the count. So the naturally-rejected UUID sinks to the bottom of the queue. To reproduce the bug I had to make the *other* UUID start at a much higher `swapped_count`, forcing the fill query to prefer the rejected one:

```kotlin
clearAndSeedPool(listOf(0, 100))   // UUID-A=0, UUID-B=100
// reject A (count becomes 1)
// clear all event_task rows
// request fill — without the fix, A (count=1) is picked over B (count=100)
```

Three of four service tests went RED. The fourth — a sanity check that rejecting a CUSTOM task (no `source_task`) records nothing — passed immediately.

Here's where the session slipped off the rails — and it was structural, not accidental. When Step 2 Clarify added the Playwright E2E to the plan, Claude created the task as `Red+Green — Playwright E2E rejection replay test`. One task, two responsibilities. The RED gate for the Playwright half was never encoded in the todolist.

What the skill actually requires when an E2E is needed:

> Write the service/unit test first and get it RED, then write the Playwright test and get it RED too. Both must be failing before you start Step 5.

Service tests went RED, Step 5 Green shipped the fix, and only then did Claude write the Playwright test — at which point it passed on the first run. It never failed.

A passing Playwright test is a useful regression guard, but it isn't proof it *would have* caught the bug. A `git stash` of the service fix and a re-run of the Playwright test would have closed the loop — that step never happened. Claude omitted the gate from the plan during Step 2 and then executed the plan faithfully. Making the RED-Playwright step its own todolist item is the fix.

## Step 5 — Green

The fix lives in three places:

- `excludedSourceTasks(eventId)` — a single helper returning a `Set<UUID>` combining assigned + rejected source UUIDs via a UNION query
- `deleteTaskAndReplace` — insert into `event_rejected_wedding_task` **before** `task.delete()`, inside the existing `AdvisoryLock.xact` so concurrent rejects serialize
- Both pool queries (`getTasks` fill + `getReplacementTaskInternal`) use `WEDDING_TASK.UUID.notIn(excludedSourceTasks(eventId))`

The rejection insert respects the project's I-3 invariant (no check-then-write races) because it runs inside the same advisory lock that guards the delete.

All four service tests green. Playwright green too — after a `/restart` to pick up the compiled Kotlin.

## Step 6 — Refactor

`/simplify` launches three review agents in parallel — reuse, quality, efficiency — against the diff. The consensus finding was that Claude's first implementation did the exclusion as two separate `fetchSet()` round trips joined by `.filterNotNull().toSet()`. Ugly and redundant: `fetchSet` already returns a Set.

The collapsed version:

```kotlin
private fun excludedSourceTasks(eventId: Long): Set<UUID> {
    val assigned = sql.select(EVENT_TASK.SOURCE_TASK)
        .from(EVENT_TASK)
        .where(EVENT_TASK.EVENT_ID.eq(eventId))
        .and(EVENT_TASK.SOURCE_TASK.isNotNull)
    val rejected = sql.select(EVENT_REJECTED_WEDDING_TASK.WEDDING_TASK_ID)
        .from(EVENT_REJECTED_WEDDING_TASK)
        .where(EVENT_REJECTED_WEDDING_TASK.EVENT_ID.eq(eventId))
    return assigned.union(rejected).fetchSet(0, UUID::class.java)
}
```

One round trip, one set. The agents also flagged a redundant `idx_event_rejected_wedding_task_event_id` (the composite PK already indexes `event_id` as leading column) — Claude dropped it before the migration ever left the branch.

The Playwright test was using `locator("p").first().textContent()` to read the card title. Fragile — a layout refactor would silently break the test. Claude added a `data-testid="swipe-title"` to the template, a `SWIPE_TITLE` TestId constant, a `swipeTitle` accessor in the page object. Now the test reads the title by ID.

All tests still green after the refactor.

## Step 7 — Verify

Three categories, three different proof requirements:

- **Non-user-observable** (background jobs, internal refactors) — service tests are sufficient proof
- **User-observable** (the wedding task bug) — the Playwright E2E green is the proof, not the service tests alone
- **UI changes** (any template file modified) — spawn the `ui-review` subagent on the screenshot folder

Claude modified `TaskManagerComponent.html` — only the `data-testid` attribute, invisible in the rendered DOM. The Playwright screenshots showed no visual delta, so Claude skipped the explicit `ui-review` call since the test already took 10 screenshots through the reject flow.

## Step 8 — Beautify

No new UI elements. Beautify wasn't on the todolist.

## Step 9 — Commit

A single `/commit` call with a Conventional Commits message:

```
fix(wedding-task): persist rejected source uuids in junction table

Rejected ASSIGNED tasks hard-deleted the EVENT_TASK row, leaving no
trace of which WEDDING_TASK.uuid the guest had rejected. Fill and
replacement queries excluded only UUIDs still referenced by live rows,
so a rejected task could re-appear on newly ordered cards.

- Add event_rejected_wedding_task junction (event_id, wedding_task_id)
- Record rejection inside deleteTaskAndReplace under existing xact lock
- Exclude rejected + still-assigned source_tasks via single UNION query
- Cover both pool paths (getTasks fill, getReplacementTaskInternal) with
  DataBaseTest + Playwright reject-replay test
```

14 files, 501 insertions, 13 deletions. Migration, generated jOOQ code, three source edits, two new test files, one page-object update.

## Why the gates matter

I could have fixed this bug without the skill. A capable engineer would look at `WeddingTaskService.kt`, spot the three call sites, add a junction table, and ship. Maybe 30 minutes of work.

What the skill bought me:

- **Step 0 todolist** — Claude didn't forget the Playwright E2E mid-session when the DB migration turned out to be more involved than expected
- **Step 2 Clarify** — the "only explicit reject" scope decision cut the implementation in half; the fallback where Claude auto-scopes "all three delete paths" would have added 40 lines of code and two more tests for no business benefit
- **Step 4 Red gate** — the fill-path test passed initially because `swapped_count` ordering naturally hid the bug; the gate forced Claude to construct a seeding that actually reproduced it
- **Step 6 `/simplify`** — three parallel review agents caught a redundant index, a redundant `filterNotNull().toSet()`, and a fragile test locator I wouldn't have caught in review alone
- **Step 7 Verify** — the "UI changes need `ui-review`" rule forced Claude to stop and notice the template change, even though it was invisible in the rendered DOM

The gates make it impossible to accidentally ship half a fix. That's the whole value proposition.

## Feedback loop: what this session changed in the skill

The real learning from this session wasn't the bug fix — it's that every tdd-task run is worth analysing after the fact, and each analysis compounds into the next skill version. Writing the post didn't surface the Step 4 skip. Handing the session log to a second Claude instance and asking what the narrative glossed over did. That's a repeatable move: run the skill, commit, then analyse the log before the lessons evaporate.

The analysis caught several things the prose had smoothed over — Migrate being planned up front rather than surfacing mid-session, Beautify never making the initial list — and, most importantly, it made the Step 4 skip visible for what it really was: a structural gap, not an in-flight deviation. The Playwright task in the todolist was titled `Red+Green`. One task, two responsibilities. Claude marked it complete after the test passed, because there was no separate RED gate to clear. The E2E half was dangling in a task name, which a single `TaskUpdate` swallowed whole.

The skill's Step 0 default tasks had originally packed Step 4 into a single item with a parenthetical for the E2E half. After the analysis I split it:

```
4a. Red — write failing service/unit test; confirm RED
```

And added a conditional rule:

> If E2E is required, add `4b. Red — write failing Playwright E2E test; confirm RED` to the todolist.

Two tasks, two `TaskUpdate` calls, two completion signals when E2E is in play. Claude can't mark the step "done" until both gates have been hit. The same argument I made in Step 0 about why the todolist beats a front-loaded prompt applies at task granularity: a gate that lives as a sentence inside one task is easier to skip than one that lives as its own task. The attention budget rewards the visible over the nested.

That's the loop: run the skill, analyse the log, compound the gap into the next version. The next caller inherits the improvement. Shipped as `tdd-task v1.4.0`.

## Install it

One file: [`.claude/skills/tdd-task/SKILL.md`](https://github.com/jvm-skills/jvm-skills/blob/main/.claude/skills/tdd-task/SKILL.md). Drop it into your project's `.claude/skills/` directory. Add a `references/project.md` overlay with your test base classes and build commands. Then `/tdd-task <description>` on your next bug.

The skill lists these dependencies but all are optional — it has inline fallbacks for every one of them:

- [`test-gradle`](https://github.com/jvm-skills/jvm-skills/blob/main/.claude/skills/test-gradle/SKILL.md) — headless test runner, returns only failing output
- [`commit`](https://github.com/jvm-skills/jvm-skills/blob/main/.claude/skills/commit/SKILL.md) — Conventional Commits from a diff
- [`restart`](https://github.com/jvm-skills/jvm-skills/blob/main/.claude/skills/restart-spring-boot/SKILL.md) — IntelliJ run config restart + wait-for-ready
- [`ui-review`](https://github.com/jvm-skills/jvm-skills/blob/main/.claude/skills/ui-review/SKILL.md) — subagent that reviews Playwright screenshots for UX regressions
- `simplify`, `frontend`, `e2e-test` — project-specific in my setup; fall back to manual review if you don't have them

If you get stuck, open an issue on [jvm-skills](https://github.com/jvm-skills/jvm-skills) — the skill's evals run against real PhotoQuest tickets, so improvements flow back to the registry.
