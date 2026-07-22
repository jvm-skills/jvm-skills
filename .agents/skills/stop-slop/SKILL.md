---
name: stop-slop
description: Remove AI writing patterns from prose. Use when drafting, editing, or reviewing text to eliminate predictable AI tells.
metadata:
  trigger: Writing prose, editing drafts, reviewing content for AI patterns
  author: Hardik Pandya (https://hvpandya.com)
---

# Stop Slop

Eliminate predictable AI writing patterns from prose.

## Core Rules

1. **Cut filler phrases and AI-marker words.** Remove throat-clearing openers and emphasis crutches; replace excess LLM vocabulary (delve, underscore, foster, pivotal). See [references/phrases.md](references/phrases.md).

2. **Break formulaic structures.** Avoid binary contrasts, dramatic fragmentation, rhetorical setups. See [references/structures.md](references/structures.md).

3. **Vary rhythm.** Mix sentence lengths. Two items beat three. End paragraphs differently.

4. **Trust readers.** State facts directly. Skip softening, justification, hand-holding.

5. **Cut quotables.** If it sounds like a pull-quote, rewrite it.

6. **No em-dashes.** Replace every em-dash (`—`), whether before a reveal, around an aside, or anywhere else, with a colon (introducing a list or expansion), commas or parentheses (around an aside), or a full stop. The em-dash is one of the strongest AI tells; the target in prose is zero. Keep dashes only in numeric ranges (`8–25`, an en-dash) and inside code.

## Quick Checks

Before delivering prose:

- Three consecutive sentences match length? Break one.
- Paragraph ends with punchy one-liner? Vary it.
- Any em-dash (`—`) at all? Replace it with a colon, commas, parentheses, or a full stop. Zero em-dashes in prose.
- Explaining a metaphor? Trust it to land.

## Two-Pass Audit

Before scoring, run one reflective pass:

1. Ask: "What in this draft makes it obviously AI-written?" Name the specific tells.
2. Fix exactly those. Don't rewrite blind — target what the first pass found.

This catches patterns the rules miss. The rubric below measures; this pass thinks.

## Scoring

Rate 1-10 on each dimension:

| Dimension | Question |
|-----------|----------|
| Directness | Statements or announcements? |
| Rhythm | Varied or metronomic? |
| Trust | Respects reader intelligence? |
| Authenticity | Sounds human? |
| Density | Anything cuttable? |

Below 35/50: revise.

## Audit Mode

Use this when reviewing a draft cold, from a separate session or subagent that did not write it. **Report only. Do not edit.** The cold read is the point; rewriting throws it away.

Output, in order:

1. **Tells found**: a table, one row per concrete instance:

   | Tell | Location (line / quote) | Fix |
   |------|-------------------------|-----|

   Scan for em-dashes explicitly and flag **every em-dash (`—`) in prose** as its own row; the target is zero.

2. **Rubric score**: the five dimensions above, each 1-10, plus the total.
3. **Verdict**: pass (≥35/50, no Tier-1 LLM vocabulary, and no em-dashes in prose) or revise.

Quoting the exact line keeps the fixer honest. The writer applies the fixes; the auditor never touches the prose.

## Examples

See [references/examples.md](references/examples.md) for before/after transformations.

## License

MIT
