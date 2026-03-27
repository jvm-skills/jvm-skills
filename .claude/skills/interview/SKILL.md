---
name: interview
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Outputs a spec with user stories.
---
Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

Use the AskUserQuestionTool to ask about literally anything: technical implementation, UI & UX, concerns, tradeoffs, etc. — but make sure the questions are not obvious.

If a question can be answered by exploring the codebase, explore the codebase instead.

## Mandatory interview topics

Beyond the feature’s core mechanics, you MUST explicitly probe these areas:

- **Entry points**: Where does the user navigate FROM to reach this feature? What existing page/nav/button needs to change?
- **User journey start-to-finish**: Walk through the complete flow from "user is on an existing page" → "user discovers feature" → "user completes the feature" → "user returns to where they were"
- **Roles**: Which user roles interact with this feature? (manager, guest, admin, unauthenticated)
- **Edge cases**: What happens on error, empty state, concurrent access, mobile vs desktop?
- **State transitions across roles**: For each state change, ask: which roles see this change? How (websockets, SSE, polling, manual refresh)? What does each role's screen show before and after the transition?
- **Terminal states & dead ends**: For every end-state, ask: what does the user do next? Every screen must have a forward action. Also: what URL params, cookies, or tokens does the entry point URL need?

## Output format

Be very in-depth and continue interviewing me continually until it’s complete, then write the spec to the file.

The spec MUST end with a structured `## User Stories` section. Derive these from the interview — every agreed-upon behavior becomes a story:

```markdown
## User Stories

- **US-1**: As a [role], I [action] so that [outcome].
- **US-2**: As a [role], I [action] so that [outcome].
...
```

Rules for user stories:
- Every user role that interacts with the feature must have at least one story
- Navigation/entry point stories come FIRST (e.g. "As a manager, I see a game button on my dashboard so that I can start a ranking game")
- Cover the happy path, key error states, and edge cases
- Stories must be specific enough to verify — "I can use the feature" is too vague
- Number them (US-1, US-2, ...) so the plan can reference them