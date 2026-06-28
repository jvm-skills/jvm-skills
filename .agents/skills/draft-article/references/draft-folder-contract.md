# Article Draft Source Folder Contract

Use one folder per article draft:

```text
../jvm-skills-article-drafts/drafts/<draft-slug>/
|-- README.md
|-- first-draft-outline.md
|-- conversation-extract-<session-id>.md
|-- notes/
|   `-- source-<short-topic>.md
`-- raw/
    |-- chatgpt/
    |-- session/
    `-- skill/
```

Raw source material belongs in the private sibling drafts repo. Public repositories should contain only cleaned article text, supported workflow documentation, or intentionally shared examples.

## README Requirements

The README should list:

- raw Codex sessions
- shell snapshots
- ChatGPT exports
- readable extracts
- notes
- skill snapshots or git logs
- current article angle

## Note Requirements

Every note should answer:

- What source file or session is this?
- What does it add?
- Why does it matter for the article?
- What should the article avoid overclaiming?

## Naming

- Codex raw session: `raw/session/codex-session-<session-id>.jsonl`
- Codex shell snapshot: `raw/session/shell-snapshot-<session-id>.sh`
- Codex readable extract: `conversation-extract-<session-id>.md`
- ChatGPT export: `raw/chatgpt/<original-name>.md`
- Source note: `notes/source-<topic>.md`
