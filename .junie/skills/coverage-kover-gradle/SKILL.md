---
name: coverage-kover-gradle
description: Run test coverage report using Kover/Gradle and create test improvement plan document
invocation: user
---

# Coverage Analysis Skill

Run test coverage and generate improvement plan.

## Steps

1. **Run coverage report**
   ```bash
   ./gradlew -Pplaywright.headless=true koverXmlReport
   ```

2. **Run analysis script**
   ```bash
   kotlin scripts/coverage-analysis.main.kts
   ```

3. **Create improvement document**
   Create `docs/dev/YYYY-MM-DD_test-improvements.md` with:
   - Current coverage %
   - Packages below 50% coverage
   - Priority classes needing tests (0-30% coverage)
   - Specific test cases to write for top 5 priority classes
   - Test patterns/examples from existing tests

## Output Format

```markdown
# Test Improvement Plan - {date}

**Current Coverage: X%**

## Priority Packages
| Package | Coverage |
|---------|----------|
| core.x  | X%       |

## Priority Classes
1. **ClassName** (X%) - path/to/Class.kt
   - Test case 1
   - Test case 2

## Next Steps
- [ ] Create XTest.kt
- [ ] Create YTest.kt
```

## After Completion

Open the created document in IntelliJ:
```bash
idea docs/dev/YYYY-MM-DD_test-improvements.md
```
