# Phase-1 TRIAL results — Spring I/O 2026, first 15 speakers

Run 2026-06-26 per `HANDOFF.md`. Scratch output — **not** merged into `candidates.md`.

## Verdict: ⚠️ TRIAL FAILED (gates #2 and #3) — but highly productive

The failures are method bugs, not dead ends: fixing them is cheap, and the corrected scan **overturns
my earlier "conferences yield 0 created skills" claim** — this cohort of 15 produced 2 strong candidates.

| Gate | Target | Result | |
|---|---|---|---|
| #1 Resolution recall | ≥ 70% | **93%** (14/15) | ✅ PASS |
| #2 Zero false-positive handles | 0 | **1 FP** (`jean-developer` for Arnaud Jean) | ❌ FAIL |
| #3 Scan method agreement | code-search ≈ tree-scan | code-search missed **everything** | ❌ FAIL |
| #4 Artifact hygiene | clean buckets, deduped | clean | ✅ PASS |

---

## Stage 2 — Resolution (14/15)

HIGH = name+affiliation match (auto-accept). MED = name-only (FP-prone). UNRESOLVED = parked.

| Speaker | Affil | Handle | Conf | Correct? |
|---|---|---|---|---|
| Adib Saikali | Broadcom | `asaikali` | MED | ✅ (ex-VMware) |
| Alex Soto | IBM | `lordofthejars` | HIGH | ✅ |
| Alexander Chatzizacharias | jDriven | — | UNRESOLVED | (no hits) |
| Alina Yurenko | Oracle | `alina-yur` | HIGH | ✅ |
| Andrea Peruffo | IBM | `andreaTP` | HIGH | ✅ |
| Andreas Lange | Broadcom | `andrlange` | MED | ⚠️ unconfirmed (no co) |
| Annegret Junker | codecentric | `Grinseteddy` | HIGH | ✅ |
| Anthony Dahanne | HeroDevs | `anthonydahanne` | HIGH | ✅ |
| Anton Arhipov | JetBrains | `antonarhipov` | HIGH | ✅ |
| **Arnaud Jean** | AWS | `jean-developer` | MED | ❌ **FALSE POSITIVE** — "Jean Carlos Arnaud B." @SoutLogic, jarnaud.com |
| Badr Nass Lahsen | CyberArk | `bnasslahsen` | HIGH | ✅ |
| Brian Vermeer | Snyk | `bmvermeer` | HIGH | ✅ |
| Catherine Edelveis | BellSoft | `des-felins` | MED | ⚠️ unconfirmed (name-exact) |
| Christian Beikov | IBM | `beikov` | HIGH | ✅ |
| Christian Tzolov | Broadcom | `tzolov` | HIGH | ✅ |

**Finding:** all 10 HIGH = correct. The 1 FP and 2 "unconfirmed" are all **MED (name-only)**. → auto-accept HIGH only; route MED to manual confirm.

## Stage 3–4 — Scan (corrected: REST tree-scan, forks excluded) + evaluation

### ✅ Found (genuine, deep, JVM-relevant created skills)
| Skill | Repo | Author | Evidence |
|---|---|---|---|
| Agent Skills collection | `antonarhipov/agentskills` | Anton Arhipov (JetBrains, 614 flw) | 13★; `spring-batch-6/SKILL.md` (217 lines), `defend-your-pr`, `review-prototype`. Also `antonarhipov/kotlinconf-sdd` → `kotlin-language-features/SKILL.md` (**423 lines**, 12★) + `java-spring` skill. curated. |
| Java Migration & Modernization | `lordofthejars/java-migration-modernization-bob` | Alex Soto (IBM/Red Hat, 602 flw) | 14★; `step-2/SKILL.md` (107 lines). Java migration skill. curated. |

### 🟡 Needs-review
| Repo | Author | Note |
|---|---|---|
| `andreaTP/skill-compile-to-wasm` (5★) | Andrea Peruffo (IBM) | Niche Java→WASM skill — verify depth/reuse |
| `Grinseteddy/DomainDrivenApiDesign` (6★), `AiCollections` (5★) | Annegret Junker (codecentric) | DDD / OpenAPI / AsyncAPI spec-author skills; partly language-agnostic (book samples) |
| `lordofthejars/test-codeassistants-workshop` | Alex Soto | `playwright-java` skill — testing, workshop context |

### ❌ Rejected (skill file present but not a reusable JVM skill)
| Repo | Reason |
|---|---|
| `tzolov/voxxeddays2026-demo` (31★), `playground-flight-booking` (349★), `docs` | Demo/talk skills (ai-tutor, pdf, travel-planner) + Spring AI demo `AGENTS.md` — not reusable best-practice |
| `asaikali/remote-mcp-protocol` | Bare `CLAUDE.md` = project instructions, not a skill |
| `anthonydahanne/jellyfin-music-helper` | Personal hobby `AGENTS.md` |
| `antonarhipov` SDD boilerplate (`01-spec`…`06-execute`, repeated across sdd-demo/midifx/sdd-workshop) | Generic spec-driven-dev template duplicated across demos; canonical home is `agentskills` (listed in Found) |

### 📇 Parked (resolved, no qualifying created skill)
`alina-yur`, `andrlange`, `bnasslahsen`, `bmvermeer`, `des-felins`, `beikov` — 0 skill files (tree-scanned).
`jean-developer` — FALSE POSITIVE, discard. `Alexander Chatzizacharias` — UNRESOLVED.

---

## Required loop fixes before EXECUTE (v3)

1. **Scan = REST tree-scan is PRIMARY** (code-search `--owner` has unacceptable recall — it returned 0
   for `tzolov`/`antonarhipov`/`lordofthejars` while tree-scan found 13★/14★ skill repos). Code-search
   only as a cheap pre-filter, never authoritative.
2. **Throttle the tree-scan** (~0.7s between tree calls) — bulk scanning tripped a GitHub **secondary
   rate limit**, producing false "0 repos" for the last 3 speakers until re-run slowly.
3. **Resolution: auto-accept HIGH only.** MED (name-only) → "manual-confirm" bucket; never feed an
   unconfirmed handle to the scan as attributed (the `jean-developer` FP).
4. **Evaluation must filter** forks, demo/talk/workshop repos, and duplicated boilerplate templates;
   keep original reusable JVM skills.

**Recommendation:** apply v3 fixes, re-trial the same 15 (cheap, mostly cached), confirm gates #2/#3
pass, then EXECUTE the remaining ~70 Spring I/O speakers.
