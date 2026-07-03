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
- 2026-07-03 (JPoint 2025) — **`norm()` collapses any name written entirely in a non-Latin script
  (Cyrillic, CJK, etc.) to an empty string, and the empty-string dedupe key then silently blackholes
  every other such speaker across every conference, not just the one that hit it first.** `norm()`
  (scout.py) does NFKD-decompose + strip-combining-marks + `[^a-z0-9]+` filtering, which folds
  accented Latin (é→e) but drops non-Latin letters entirely, leaving `nn=""` for e.g. "Владимир
  Плизга". The first such speaker processed gets a real (failed) search and is cached in
  `resolutions.csv` as one row with `norm_name=""`, confidence=UNRESOLVED. Every subsequent speaker
  anywhere whose name also normalizes to `""` then hits `nn in seen` and gets `reused-from-db` —
  reusing that SAME cached UNRESOLVED row without any per-person search ever running. JPoint 2025's
  roster (43 speakers, almost entirely Cyrillic names) resolved only 1/43 (the one Latin-script name,
  Brian Matthews); the other 42 were never actually searched, just short-circuited onto the shared
  empty-key cache entry. **For a roster with non-Latin-script names, don't trust a near-zero resolve
  rate as "no GitHub presence" — it's a normalization collision. Either transliterate the name to
  Latin script before resolving/investigating, or treat every `norm_name=""` UNRESOLVED result as
  untried and manually re-resolve via web/GitHub search per person.**
- 2026-07-03 (betterCode() Spring 2025) — **When corroboration confirms a MED candidate is the right
  person, also check whether that corroborating signal (bio link, twitter handle, etc.) points to a
  DIFFERENT, more active GitHub account for the same person — alias to the account that will actually
  be scanned, not just whichever candidate surfaced in the name search.** A confirmed alias with 0
  public repos produces a permanent zero-signal scan for that speaker in every future conference,
  silently hiding their real work. (e.g., Lofi Dewanto: MED candidate `blasiuslofidewantodevk` (0
  repos, 0 followers, dormant `@devk-insurance` employer account) was confirmed via its bio's twitter
  handle matching a separate, unlinked `lofidewanto` account with 71 Java repos and 49 followers — but
  the alias was recorded against the dormant account, so `lofidewanto`'s real repos will never be
  scanned unless corrected.)
- 2026-07-03 — Community Day for Java 2025, Ahmedabad MED investigation. The correct login for
  "Vaibhav Choudhary" (a JVM engineer @ Salesforce, confirmed via forks of jdk25u/javafest) did not
  appear anywhere in the auto-generated name-search `cands` array — every candidate listed
  (chanakya-vc, choudhary-vaibhav, vaibhavchoudhary10, …) was a different, unrelated person. It
  surfaced only by checking the conference's own official speaker/session page, which linked
  directly to the speaker's real GitHub profile. **When a MED's whole candidate list looks like
  name-collisions with no real corroboration, check the conference site's speaker bio/session page
  for a direct GitHub link before concluding no match exists** — the true login may not surface via
  name search at all. Distinct from the JCON OpenBlend web-search tactic (searching "<name>
  <company>" to disambiguate *among* existing candidates): here the lookup replaces the candidate
  list entirely.
- 2026-07-03 — JConf Dominicana 2025. **Honorific prefixes ("Dr.", "Prof.", "Mr.") create a
  duplicate norm_name identity and can mask an already-resolved HIGH match.** `norm()` only
  lowercases and strips punctuation — it does not strip titles — so "Dr. Venkat Subramaniam" and
  "Venkat Subramaniam" hash to two different norm_name keys even though they're the same speaker
  with the same affiliation. This run's roster carried "Dr. Venkat Subramaniam" as UNRESOLVED
  (`broad`) while a HIGH resolution (`venkats`, verified same "Agile Developer, Inc." affiliation)
  already existed from a prior conference under the honorific-free norm_name. Before investigating
  a fresh MED/UNRESOLVED, strip common honorifics from the name and check `resolutions.csv` for a
  HIGH match under that variant — reuse it rather than re-resolving or leaving it UNRESOLVED.
- 2026-07-03 — JJUG CCC 2025 Spring MED investigation (13 MEDs: 4 confirm / 9 reject, incl. 2
  corrections to prior auto-decisions). The automated `jvm_repo` flag only scans a candidate's
  most-recently-pushed repos (window ~25), so it can miss real JVM work if the user's newest pushes
  are in other languages. Caught two false rejects this way: nannany (yoshihiko minami) has 39+ Java
  repos (Spring Boot/JPA/WebFlux/RabbitMQ/Spring-Actuator) but they're all from 2018-2023, pushed
  behind newer TS/Python side-projects; toru-takahashi has an authored (non-fork) Java Embulk plugin
  from 2016 matching his stated Fluentd/Embulk/Digdag OSS bio — both flipped reject→confirm in
  db/aliases.csv. Also: for takumi endo, the top-ranked candidate (ENDOTAKUMI, most followers) had
  zero JVM/company signal while a lower-ranked cand in the same list (endo-cariot, company="Cariot,
  Inc." exact match to speaker's employer) was clearly the right person — investigate stage should
  scan the whole `cands` array, not just the top pick. **When investigating a MED, don't trust
  `jvm_repo:false` alone — pull the candidate's full non-fork repo list
  (`gh api users/<login>/repos?per_page=100&sort=pushed`) and check language distribution across ALL
  of it, not just the pinned/recent ones.**
- 2026-07-03 — JCON OpenBlend Slovenia MED investigation (11 confirm / 3 reject). Patterns worth
  noting: (1) acquisition lag — gh_company can be a pre-acquisition employer name (e.g. "Trivadis
  GmbH") while aff lists the acquirer ("Accenture") months/years later; treat these as matching, not
  conflicting, once you confirm the acquisition via search. (2) same-name-different-person is real —
  "Julian Frey" candidate JulFrey had company "University of Freiburg" + forestry/LiDAR repos while
  the actual speaker (confirmed via web search) is an Oracle ACE Director at CITE GmbH, Switzerland;
  a plausible-looking single candidate can still be the wrong person when the repo/company domain
  contradicts the speaker's known field — reject in that case even though it was the only candidate.
  (3) the jvm_repo flag can miss real JVM signal buried in a repo's secondary language (e.g.
  davidsenica/quarkus-angular-starter has Java as its 2nd-largest language by bytes but the flag was
  false) — worth spot-checking repo language breakdowns, not just the boolean, for borderline cases.
  (4) web search for "<name> <aff-derived-company/org>" is often decisive for MED cases with thin
  GitHub profiles (0 repos/followers) — several confirms here (Aleš Kravos, Federico Venturin, Radovan
  Bacovic, Mihael Škarabot, Domen Dolar) rested on finding the person's real employer/role externally
  and matching it to gh_company or aff, not on GitHub signals alone.
- 2026-06-27 — seeded. Confirmed by human: azzazzel=Milen Dyankov, cmandesign=Soroosh Khodami,
  ikolaxis=Ioannis Kolaxis (these were correct people previously parked as MED — matching was too strict).
