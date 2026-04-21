# Installing `test-gradle` in your project

This skill was born in a real project and still carries some of its DNA — a wrapper script at `./scripts/run-tests.sh`, a live-tail Kitty tab, and a `build/gradle-test-out.txt` output path. One-time adaptation makes it yours.

## Prerequisites

- Gradle build (Kotlin or Groovy DSL)
- Bash environment
- Optional: [Kitty terminal](https://sw.kovidgoyal.net/kitty/) if you want the live-tail tab (skip step 3 in `SKILL.md` otherwise)

## Steps

1. Copy `SKILL.md` → `.claude/skills/test-gradle/SKILL.md` in your project
2. Copy `templates/run-tests.sh` → `scripts/run-tests.sh` and `chmod +x`
3. Paste this prompt into Claude Code:

> Adapt the `test-gradle` skill I just installed to this project.
>
> 1. Read `build.gradle.kts` (or `build.gradle`) to identify the test task name and any custom test args I use. Update `scripts/run-tests.sh` to call the right task.
> 2. If my project is multi-module, adjust the script to target the right module(s) or run `./gradlew test` from the root.
> 3. Replace `build/gradle-test-out.txt` in the script with my actual Gradle test report path if different.
> 4. If I am not using Kitty, remove the `kitty @ launch` line from `SKILL.md` step 1 and keep only the direct script call.
> 5. Run `./scripts/run-tests.sh` once to confirm a successful full-suite pass. If it fails, fix the wrapper before proceeding.
> 6. Replace the `*RankingGameSetupTest` style examples in `SKILL.md` with real test class names from my project so future invocations have accurate patterns.

## Verify

After adaptation, run `/test-gradle` with no arguments — it should run the full suite. Then run `/test-gradle *SomeTest` to confirm filter passthrough works.
