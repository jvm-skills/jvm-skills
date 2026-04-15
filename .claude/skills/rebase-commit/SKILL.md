# Rebase Commit Skill

Rebase all non-pushed commits and uncommitted changes into clean logical feature commits.

## Steps

1. Run `git status` and `git diff` (staged + unstaged) to understand uncommitted changes
2. Find the remote tracking branch and list non-pushed commits:
   `git log @{upstream}..HEAD --oneline` (if no upstream, fall back to the default branch — check `references/project.md` for the base branch name; defaults to `origin/main`)
3. Read the diffs of all non-pushed commits: `git diff <last-pushed-commit>..HEAD`
4. Combine non-pushed commits + uncommitted changes: analyze all changes and group by logical feature/intent.
   **Vertical-slice rule**: preserve vertical slices (feature + tests in one commit). If the original commits represent incremental phases/slices of a feature (e.g. "user registration", "profile page", "settings"), keep them as separate commits — do NOT merge them into one giant feature commit. Each slice should be independently reviewable with its own tests. Only merge commits that touch the same slice (e.g. a phase commit + its bugfix later). If a bugfix commit touches multiple slices, split its hunks across the relevant slice commits using `git add -p`.
   **Infra/tooling grouping**: non-feature commits (tooling, config, skills, CI) CAN be grouped by concern since they don't follow the vertical-slice pattern.
5. `git reset --soft <last-pushed-commit>` to unstage everything back to the last pushed state
6. Stage any previously uncommitted files too (`git add` relevant files)
7. For each logical group, stage only the files belonging to that group and commit using a HEREDOC with a concise, action-oriented message (e.g. "Add X", "Fix Y", "Refactor Z"). No conventional commit prefixes. Append:
   `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`
8. Repeat step 7 until all changes are committed
9. Run `git log @{upstream}..HEAD --oneline` (or `<base-branch>..HEAD`) to show final commit list
10. Report the resulting commits

## Project Customization

Read `references/project.md` in this skill's directory if it exists. It provides project-specific context:
- Base branch name (e.g. `main`, `master`, `stage`, `develop`) for fallback when no upstream is set
- Any other project-specific patterns
