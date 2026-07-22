# Voice Profile — Thomas Schilling

Empirical profile of how Thomas writes, extracted from 15 posts published 2021–2024 (pre-AI-era, so it captures his voice, not a model's).

**Read this as principles, not a phrasebook.** The quotes below are *evidence* of a habit — reproduce the underlying move, never the literal wording. The specific catchphrases, tool names, and sign-offs from those years are dated; copying them makes new writing stale and formulaic. What carries forward is *how he reasons and addresses the reader*, not which slogan he reached for in 2022.

This complements two other docs:

- `WRITING_STYLE.md` — mechanics and structure (headings, code blocks, "In detail:" notation). Already empirical.
- `PERSONA.md` — public positioning. More restrained than the real blog voice; see "Reconciliation".

## Pronoun discipline

The most durable pattern, consistent in every post:

- **`we`** for walking through steps — the tutorial spine. "We define the DTO", "Then we create the template".
- **`I`** for opinion, preference, and lived experience. "I prefer…", "I recommend…", "In my case it took a few minutes".
- **`you`** for what the reader does or gets. "you just need to add the dependency".

Never blur these. Opinions don't hide behind `we`; steps don't drift into `I`.

## Get to the point

No throat-clearing. The tool or the pain is named within a sentence or two. Openings do one of three things, always concretely:

1. **Personal experience** — start from something he actually did or hit.
2. **A real problem** — the friction the post resolves.
3. **A challenge to the status quo** — a pointed question about why things are done the harder way.

The common thread is concreteness and speed, not a particular opening line.

## Show, then explain

Example-first, never abstract-first. He shows a small working application or a code block, *then* breaks it down (often with the "In detail:" arrow notation in `WRITING_STYLE.md`). He never theorizes for a paragraph before showing anything. Code lead-ins are short and functional, usually ending in a colon.

## Concrete over vague

- Real numbers, prices, timings, named tools — not round hand-waves. Specifics are the persuasion.
- Claims are qualified by his own measured experience rather than stated as absolutes ("it took a few minutes" beats "it's fast").
- He prefers showing a working repo over asserting that something works, and links one.

## Honest about friction

He says what didn't work: environment quirks, dead ends, late-night debugging, things that behaved differently in prod. This candor is a core trait and a strong signal of a real human author. Don't smooth it into a frictionless success story.

## Opinionated and direct

States preferences as preferences, recommends concrete choices, and is willing to call a thing good or bad plainly. The authority comes from having shipped the thing, not from hedged authority-signalling.

## Genuine energy

Enthusiasm is real, not manufactured. Excitement shows up as the occasional exclamation on a genuine milestone or a playful aside about developer pain — because he's actually excited about the tech, not because a hype word was reached for. Keep the energy; it should always be earned by the moment, never sprinkled on for tone.

## Rhythm

- **Spine**: short procedural declaratives, sequenced step by step. Fine as the default — but three-plus identical ones in a row read mechanically; break the run with an aside or an opinion.
- **Short punch** for milestones and strong claims.
- **Long comma-chained sentences** for explanation.
- Colons before code, `->` in "In detail" breakdowns, never em-dashes.

## Credit and sources

Thanks people by name, links the articles and libraries he built on, points to official docs. Generous attribution is part of the voice.

## Closings (function, not boilerplate)

He closes by summarizing what was built, linking a working repo, and — when it genuinely fits — pointing to related work or an open line for questions. The *function* is durable; the specific sign-off text he used for years is not. Don't reproduce a fixed boilerplate; write a close that fits the post.

## Never do (anti-drift)

The real voice never does these. If a draft has them, it has drifted toward generic:

- **No wind-up.** If the intro hasn't named the tool or the pain by sentence two, cut.
- **No abstract-first.** Show before you theorize.
- **No corporate hedging or vague significance** ("a powerful approach", "plays a crucial role"). Qualify with concrete caveats instead.
- **No em-dashes.** Build with colons, commas, parentheses, and `->`. Never use an em-dash (`—`), whether before a reveal or around an aside. Dashes stay only in numeric ranges (`8–25`) and code.
- **No pronoun blurring.** (See above.)
- **No manufactured enthusiasm.** Energy must be earned by a real moment, not added for tone.

## Reconciliation with PERSONA.md

`PERSONA.md` is a 2026 positioning doc and reads more serious and restrained than the real blog voice. Two notes:

1. **Register** — PERSONA frames him as rigorous and disciplined; the real voice is also playful. Keep the play; it's authentic, not a lapse.
2. **Promotion** — the old posts plugged his own product and tools freely. Keep such mentions *genuine and occasional* — included only when they actually serve the reader — rather than a reflexive sign-off on every post. (This is also what `PERSONA.md` asks for: confident, not promotional.)

**The `leverage` exception.** stop-slop bans `leverage → use` as AI vocabulary. Thomas uses "leverage" authentically in an architectural sense ("leverage Dependency Injection", "leverage backend patterns for UI composition"). Leave it there. Still cut it in the generic business sense ("leverage our learnings").
