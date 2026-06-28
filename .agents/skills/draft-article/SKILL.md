---
name: draft-article
description: Capture and organize private article draft source material in a sibling drafts repo, including Codex session JSONL logs, shell snapshots, ChatGPT markdown exports, readable extracts, source notes, and outline updates. Use when creating a new article draft folder, adding supporting Codex session ids one by one, moving ChatGPT exports into a draft, or maintaining a local evidence trail for a blog article. This skill is local-only and must not publish, push, or create public repos.
---

# Draft Article

Use this skill to build a private local article draft folder with supporting source logs added incrementally. From the `jvm-skills` workspace, keep one folder per draft under `../jvm-skills-article-drafts/drafts/<draft-slug>/`.

Do not publish, push, create public repositories, or create PRs as part of this skill. This skill captures local draft evidence only. Raw Codex logs, shell snapshots, and ChatGPT exports belong in the private drafts repo, not in the public `jvm-skills` repo.

## Folder Contract

For each draft, keep this shape:

```text
../jvm-skills-article-drafts/drafts/<draft-slug>/
|-- README.md
|-- first-draft-outline.md
|-- conversation-extract-<session-id>.md
|-- notes/
|   `-- source-<short-topic>.md
`-- raw/
    |-- chatgpt/
    |   `-- <export>.md
    |-- session/
    |   |-- codex-session-<session-id>.jsonl
    |   `-- shell-snapshot-<session-id>.sh
    `-- skill/
        `-- <optional skill snapshot or git log>
```

Use `conversation-extract.md` only for the primary session if the draft already has that convention. For every additional Codex session, prefer `conversation-extract-<session-id>.md`.

## Workflow

1. Identify or create the draft folder.
   - If the user provides a title, slugify it in lowercase kebab-case.
   - If the user refers to an existing draft, inspect `../jvm-skills-article-drafts/drafts/` and use the matching folder.
   - If no draft exists, create the folder contract above.

2. Add source material.
   - For a Codex session id, run `scripts/capture-codex-session.py`.
   - For a ChatGPT markdown export, move or copy it into `raw/chatgpt/`.
   - Preserve raw source material. Do not edit raw logs or exports.

3. Generate readable source artifacts.
   - Codex sessions need a readable `conversation-extract-<session-id>.md`.
   - ChatGPT exports can remain raw, but create a note when the source materially affects the article.

4. Add or update `notes/source-<topic>.md`.
   - Summarize what the source adds.
   - Capture concrete commits, files, workflow lessons, or product decisions.
   - State cautions so the article does not overclaim.

5. Update the draft `README.md`.
   - List new raw sources, extracts, and notes.
   - Keep the article angle current.

6. Update `first-draft-outline.md` when the new source changes the narrative.
   - Add lessons learned from the new source.
   - Do not turn the outline into a full transcript.
   - Keep the product example subordinate to the article thesis.

7. Check status.
   - Run `git -C ../jvm-skills-article-drafts status --short drafts/<draft-slug>` and `git status --short .agents/skills/draft-article`.
   - Report files changed.
   - Do not commit unless the user asks for a commit.

## Codex Session Capture

Use the helper script:

```bash
python3 .agents/skills/draft-article/scripts/capture-codex-session.py \
  --session-id <session-id> \
  --draft-dir ../jvm-skills-article-drafts/drafts/<draft-slug>
```

The script:

- finds the matching Codex JSONL under `$HOME/.codex`
- copies it to `raw/session/codex-session-<session-id>.jsonl`
- copies the shell snapshot when available
- writes `conversation-extract-<session-id>.md`
- verifies line counts and checksum parity

If the script cannot find the session, search manually with `rg -l <session-id> "$HOME/.codex"` and report the blocker.

## ChatGPT Export Capture

When the user provides a ChatGPT markdown export path:

1. Create `raw/chatgpt/` if needed.
2. Move the file there unless the user asks for a copy.
3. Read headings and the end of the export with `rg -n "^(#|##|###) "` and `tail`.
4. Add `notes/source-<topic>.md` when it contains article-relevant decisions or workflow evidence.

## Source Notes

Use this shape for notes:

```md
# Source Notes: <Topic>

Source files:

- `raw/session/codex-session-<session-id>.jsonl`
- `conversation-extract-<session-id>.md`

## What This Source Adds

...

## Key Article Relevance

...

## Caution

...
```

Keep notes factual and concise. Include exact commit hashes, paths, session ids, or commands when they matter.

## Article Discipline

Challenge scope drift. The source folder is evidence for an article, not the article itself.

Prefer this framing:

- the article thesis
- the workflow that produced the artifact
- the reusable skill/process lesson
- a concrete product example only as evidence

Avoid this framing:

- a full product spec
- a full debugging diary
- a transcript dump
- old-vs-new migration narrative

Documentation should describe the current supported workflow and intended state. Historical details belong in source notes only when they explain why the article changed.
