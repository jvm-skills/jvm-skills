# Speaker → GitHub matching rules

Guidance the resolver (scout.py) and the investigate agent use to map a conference speaker
(name + affiliation) to a GitHub login. The matching-refinement agent appends learnings here.
Confirmed/rejected decisions are persisted structurally in `db/aliases.csv` (read first, authoritative).

## Goal: prefer RECALL with corroboration

A speaker at a JVM conference very often HAS a GitHub account; missing them loses real skills.
So accept a candidate when the name matches AND at least one corroborating signal agrees — don't
demand a perfect company-string match.

## Decision order

1. **Alias ledger (`db/aliases.csv`) is authoritative.** `confirm` → use that login (HIGH). `reject`
   → never pick that login for this person.
2. **Name match** = both first and last name tokens (ASCII-folded) appear in the GitHub profile name.
3. **Corroboration (any ONE promotes a name-match to HIGH):**
   - affiliation token appears in the profile company or bio, OR
   - an org the user belongs to matches the affiliation, OR
   - the user has JVM-relevant repos (Java/Kotlin/Groovy/Scala, or Gradle/Maven), OR
   - the user is a dominant single match (has a company, >=50 followers, >= 3x the runner-up).
4. **No corroboration** → MED (send to the investigate stage).

## Investigate stage (the deeper look)

For a MED candidate, read the candidate profile(s): bio, company, orgs, top repos, and cross-check
against the conference and the speaker's likely topic (a JVM-conference speaker with Java/Kotlin repos
is almost certainly the right person even if the company string differs). Decide accept(login) or
reject, and record it in `db/aliases.csv` (source=auto) so the decision carries forward.

## Cautions

- Common names need stronger corroboration (a generic "John Smith" name-match alone is not enough).
- Don't match an obvious org/bot account or a fork-only profile.

## Learnings changelog

<!-- The matching-refinement agent prepends dated entries here. -->
- 2026-06-27 — seeded. Confirmed by human: azzazzel=Milen Dyankov, cmandesign=Soroosh Khodami,
  ikolaxis=Ioannis Kolaxis (these were correct people previously parked as MED — matching was too strict).
