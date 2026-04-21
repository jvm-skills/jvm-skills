---
name: spec
description: Generate a feature spec with user stories directly from conversation context and codebase exploration — no interview needed. Use this when the user has already described what they want (in the current conversation, a doc, or a plan) and just needs it formalized into a spec. Also use when the user says "write a spec", "create a spec", "spec this out", or similar.
---
Generate a comprehensive feature spec with user stories by synthesizing information already available in context — conversation history, referenced documents, and codebase exploration. Skip any interview or Q&A phase.

## How to gather information

Instead of asking the user questions, proactively resolve unknowns by:

1. **Mining the conversation**: Extract every detail the user has already shared — requirements, constraints, examples, preferences, edge cases mentioned in passing.
2. **Exploring the codebase**: Look at existing patterns, related features, navigation structure, roles, and state management to fill gaps. Check controllers, services, templates/views, and domain logic relevant to the feature.
3. **Reading project docs**: Check `docs/` for architecture docs, onboarding flows, and existing specs that inform the design.
4. **Making reasonable assumptions**: Where information is genuinely missing and can't be inferred from codebase/docs, state your assumption explicitly in the spec (mark with "**Assumption:**").

## Required coverage

The spec must address all of these, even if the user didn't mention them explicitly — infer from codebase patterns:

- **Entry points**: Where does the user navigate FROM? What existing page/nav/button changes?
- **User journey**: Complete flow from discovery → interaction → completion → return
- **Roles**: Which roles interact? Identify all user roles from the codebase (or check `references/project.md`).
- **Edge cases**: Error states, empty states, concurrent access, mobile vs desktop
- **State transitions across roles**: Which roles see each change? How (real-time — SSE/websockets, polling, refresh)? What does each role's screen show before/after?
- **Terminal states**: What does the user do next at every end-state? Every screen must have a forward action. URL params, cookies, or tokens needed?

## Output format

Write the spec to `docs/dev/YYYY-MM-DD-hh-mm_spec-<feature-name>.md` and open it with `idea` (or your editor).

The spec must end with a structured `## User Stories` section:

```markdown
## User Stories

- **US-1**: As a [role], I [action] so that [outcome].
- **US-2**: As a [role], I [action] so that [outcome].
...
```

Rules for user stories:
- Every user role that interacts with the feature must have at least one story
- Navigation/entry point stories come FIRST
- Cover the happy path, key error states, and edge cases
- Stories must be specific enough to verify — "I can use the feature" is too vague
- Number them (US-1, US-2, ...) so the plan can reference them

## Project Customization

Read `references/project.md` in this skill's directory if it exists. It provides project-specific context:
- User roles and their permissions
- View layer technology (e.g. ViewComponents, Thymeleaf, JSP, React)
- Real-time transport preference (SSE, websockets, polling)
- Output directory conventions
- Any other project-specific patterns
