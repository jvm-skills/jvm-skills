---
name: ui-review
description: "Verify UI/UX by running Playwright tests and reviewing screenshots. Use when you want to check that a page looks correct and the user flow works — after implementing UI changes, fixing visual bugs, or verifying an existing page. Triggers: 'check the UI', 'does this page look right', 'verify the layout', 'review screenshots', 'run UI tests'."
dependencies:
  - test
agents:
  - ui-review
---

# UI Review

Run Playwright tests to generate fresh screenshots, then review them for UI/UX correctness.

## Process

### 1. Identify what to review

Determine which page/component to verify. The user may specify:
- A test class name (e.g. `*LoginTest`)
- A page or component name (search for the corresponding Playwright test)
- A screenshot folder to review directly (skip to step 3)

### 2. Run tests to generate screenshots

Run the relevant Playwright test(s) to produce fresh screenshots. Check `references/project.md` for the exact test command and flags. If no project overlay exists, run:

```
/test *TestClassName
```

If no Playwright test exists for this page, tell the user — don't silently skip.

### 3. Review screenshots

Spawn the `ui-review` subagent on the screenshot folder. Provide:
- The screenshot path (check `references/project.md` for the convention, or search for the test's screenshot output)
- The expected flow: what each step should show, what the user should see

```
Agent(subagent_type="ui-review", prompt="Review screenshots for UI/UX correctness.

Screenshots: <screenshot-path>

Test: '<test name>'
Purpose: <what this test verifies>
Expected flow:
- 01: <what should be visible>
- 02: <next step>
- ...

Flag any problems: broken layouts, blank pages, missing elements, bad UX flow.")
```

### 4. Report and fix

- If the subagent reports problems, fix them and re-run (go back to step 2)
- If everything looks good, report confirmation to the user

## Project Customization

Read `references/project.md` in this skill's directory if it exists. It provides project-specific context:
- Test command and flags for headless Playwright
- Screenshot output directory convention
- Any other project-specific patterns
