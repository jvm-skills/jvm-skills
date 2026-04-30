---
title: "The Package Is Too Large: The Planning Failure AI Agents Should Catch Early"
slug: the-package-is-too-large
date: 2026-04-30
draft: false
author: Thomas Schilling
description: "A feature package can be too large long before implementation starts. Here is how I learned to make interview and splitting skills stop early, propose smaller dependent packages, and wait for a manual restart."
skills:
  - workflow/interview
  - workflow/spec
tags:
  - planning
  - ai-coding
  - skills
  - specs
---

I hit a planning failure recently that looked, at first, like a bad slice split.

It wasn't.

The real bug was one level higher: the **package itself was too large**.

I was working on an onboarding redesign for a real product. On paper it looked like one coherent initiative. In practice it bundled all of this into one package:

- public acquisition and event creation
- free-to-paid upgrades
- a premium onboarding redesign
- payment return behavior
- detached account-claim restoration
- print release and fulfillment locking
- reminder deep links
- analytics across the whole funnel

Once I ran the package through the planning flow, the symptoms were obvious.

Every slice wanted to be `planned`. The shared base spec kept growing because every slice needed the same workflow model, same payment semantics, same return-path rules, same route coordination. The dependency graph was technically valid, but mostly sequential. And the first proposed slice kept drifting toward "workflow foundation" instead of a concrete feature.

That is the tell.

If your slice generator keeps inventing setup-heavy slices, the problem is often not the slice generator. The problem is that it is trying to force **multiple product increments through one package boundary**.

## What "too large" actually means

This is not about line count or story count.

A package is too large when it stops being one coherent product increment and starts behaving like several dependent increments that happen to share a domain model.

The easiest way to spot it is to ask a simple question:

> If I ship only the first third of this package, does that still read like one product outcome?

If the answer is no, you probably do not have one package. You have a stack of packages.

In my case, the onboarding redesign really wanted to be four packages:

| Package | Concrete outcome |
|---|---|
| `free-qr-entry` | Verified free landing page creates a free event, lands on the manager home, exposes the QR utility, guests can open the event |
| `light-upgrades` | Free managers buy add-ons or a light digital package and return to paid QR utility outcomes |
| `photoquest-onboarding-redesign` | Full premium entry and upgrade path, manager home, stepper semantics, package selection, early payment, claim and payment resume |
| `print-release-redesign` | Full and QR print review, explicit confirmation, terminal print state, reminder return |

Those packages are not unrelated branches. They are sequential increments on one shared workflow model. But that is fine. They do not need to be independent in the sense of "can be built in any order." They need to be **separately reviewable and shippable**.

That is a much more useful boundary.

## The bad instinct: keep slicing anyway

The wrong move here is to say:

"Yes, it is big, but let's keep the package and just make thinner slices."

That sounds disciplined. It is not.

What actually happens is:

- the first slices become foundation buckets
- migrations get pulled too early because later slices all depend on them
- analytics becomes a fake horizontal cleanup slice at the end
- the spec grows a giant shared context section because every slice needs to understand everything
- review quality drops because no human can hold the whole package in their head anymore

This is the planning equivalent of forcing a God object through code review because you promise to keep the methods short.

The methods are not the main problem.

## The rule changes I made

I ended up changing two skills.

First, the interview skill now checks the **package boundary before the main interview**. If the scope already looks like multiple dependent product increments, it has to challenge that scope immediately instead of writing one giant product spec and discovering the problem later.

Second, the slice-splitting skill now checks the **package boundary before it even tries to create slices**. If the package is too large, it must stop, propose `2-5` smaller packages with concrete outcomes and dependencies, and wait for user approval.

The most important part is the stop behavior.

Once the package has been split into smaller packages, the agent should **not** continue automatically into the child packages. The user has to explicitly restart the workflow on one of the children.

That sounds like extra ceremony, but it fixes a real failure mode. Without the stop, the agent keeps carrying the parent package context into the child packages and starts hallucinating continuity that no longer exists. Manual restart is a context reset.

## The heuristics that turned out to matter

These are the signals I now care about most:

### 1. Most slices want to be planned

If nearly every slice needs special coordination, concurrency notes, shared route semantics, or careful workflow explanations, the package is probably trying to own too much.

### 2. The base spec starts becoming a mini-architecture document

The base spec should be a substitute spec for downstream work. If it starts reading like a survival manual for a complex distributed initiative, the package boundary is wrong.

### 3. The dependency graph is mostly sequential

Some dependencies are normal. But if the graph looks like one long staircase, you are often not looking at "thin vertical slices." You are looking at several product increments pretending to be one package.

### 4. The slices keep drifting toward shared workflow state

When the first proposed slices are things like "workflow foundation", "state model", or "routing ownership", the planner is telling you that the feature split is not concrete enough.

### 5. The package contains multiple demo narratives

This was the clearest sign in hindsight. "User verifies and creates a free event" is one demo. "Manager upgrades to digital package and gets paid outcomes" is another. "Manager confirms printed output and locks fulfillment state" is another. If your package has several of these, you probably have several packages.

## What I would do now, from the start

If I were starting the same initiative again, I would force this sequence:

1. Product interview asks whether the scope is one package or several dependent packages.
2. If it is several, stop and create package-level outcomes first.
3. Run the interview again only for the chosen child package.
4. Run the technical spec for that child package.
5. Run slice splitting only inside that child package.

That is slower by one step and faster by several days.

The key insight is simple:

**Do not use slicing to compensate for a bad package boundary.**

Slicing works well once the package is already a coherent product increment. It works badly when it is being asked to decompose an initiative that should have been split one level higher.

## Why this matters for AI-assisted planning

A human planner can sometimes feel that a package is too broad and stop on instinct.

An AI agent is more dangerous here because it is usually rewarded for continuing. Give it a big enough spec and it will happily produce:

- a giant product spec
- a giant tech spec
- a giant base spec
- fourteen plausible slices
- and a deeply misleading sense of progress

The output looks organized. The package is still wrong.

This is why I increasingly care about **stop conditions** in planning skills.

The most valuable thing an AI planning agent can say is not always "here is your breakdown."

Sometimes it is:

> This should not be one package. Stop here.

That is not failure. That is the skill doing its job.
