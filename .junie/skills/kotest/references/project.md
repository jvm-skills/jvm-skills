# PhotoQuest overlay

PhotoQuest-specific context for the `kotest` skill. Overrides shared defaults
in `references/*.md` when they conflict. This file is gitignored in jvm-skills
and stripped from the published SkillsJar.

## Test base classes

All base classes live in `de.tschuehly.photoquest.util`.

- **`DataBaseTest`** — jOOQ + embedded PostgreSQL (Zonky). Use for
  service, repository, and domain tests. DB is reset
  `AFTER_EACH_TEST_METHOD` — do not add manual cleanup.
  - Injects `sql: DSLContext` as `lateinit var`.
  - Exposes `fixtures: TestFixtures` (lazy).
  - Profile: `@ActiveProfiles("test")`.
- **`S3Test`** — extends `DataBaseTest`, adds LocalStack S3 (`@Testcontainers`).
  Use for `FileService`, `CacheService`, PDF, anything that reads/writes S3.
  - Injects `s3Client: S3Client`.
- **`PlaywrightBase`** — full Spring Boot + Playwright + LocalStack (S3, SES).
  Browser-visible UI flows. 90s JUnit timeout.

**Rule of thumb:** start at `DataBaseTest`. Go to `S3Test` only if S3 is
touched. Go to `PlaywrightBase` only if there's a UI flow under test.

Do **not** use `@SpringBootTest` directly — pick the base class.

## Single-test command

PhotoQuest uses the `/test` skill, which wraps `./scripts/run-tests.sh`:

```
/test *MyTest              # one class
/test *SetupTest *LobbyTest # multiple filters
```

Translate to shell when scripting:

```bash
./scripts/run-tests.sh --tests "*MyTest"
```

`/test` with no arguments runs the whole suite — only pass patterns when you
mean to filter.

## Factories and test data

Two things, both in `de.tschuehly.photoquest.util`:

1. **`TestFixtures`** — jOOQ inserts for arbitrary new fixtures. Accessed via
   the `fixtures` property on any `DataBaseTest` subclass. All inserters have
   sensible defaults:
   - `fixtures.insertUser()` → returns `UUID` (supabaseId)
   - `fixtures.insertEvent()` → returns `Long` (event id)
   - `fixtures.insertMembership(eventId, userId, role = ...)`
   - etc. for memberships, emails, tasks, etc.

   Pattern: zero-arg when defaults suffice, pass only fields the test asserts
   on or needs for uniqueness. Do not restate default values.

2. **`TestData`** (object) — pre-seeded fixtures that correspond to
   `testdata.sql`. Use these before creating new events:
   - `TestData.wedding1` — Event 1, subdomain `cassandra-thomas`, has Stripe
     payments, completed onboarding.
   - `TestData.GuestCookieToken.EVENT_1` — pre-registered guest token for
     bypassing guest registration.
   - `TestData.quest887` / `safari889` / `exampleHeic` — image fixtures with
     matching `ClassPathResource`.
   - `TestData.initImages(s3Client)` — uploads all image fixtures to S3.

   Prefer existing events in `TestData` over inserting new ones. Only
   `fixtures.insertEvent()` when the test needs a specific state not present
   in `testdata.sql`.

## Mocking library

**MockK** is the project convention (used in ~7 test files, mostly around
OAuth/PDF/email lifecycle). Most tests don't mock — they run against the real
embedded Postgres + LocalStack instead (integration over mocks).

Rule: if a collaborator talks to Postgres, S3, or SES, **don't mock it** —
use the base class and let Zonky / LocalStack provide the real thing. Mock
only:

- External HTTP APIs without a local container (Stripe, OAuth providers).
- PDF renderer when the PDF content isn't what's under test.
- Email sender when testing scheduling logic, not content.

## Current assertion state

Most PhotoQuest tests currently use **JUnit assertions** (`assertEquals`,
`assertThrows`, etc.) — not Kotest. Adoption is a direction, not a fait
accompli. When using the `kotest` skill:

- **Create track** — write Kotest from the start. Don't match the legacy
  style in neighbouring files.
- **Modernize track** — you will almost always find JUnit assertions (not
  AssertJ). Apply the JUnit → Kotest mappings in `references/kotest-matchers.md`.

Kotest dependencies (`io.kotest.matchers.*`, `io.kotest.assertions.*`) are
already on the test classpath — no Gradle changes needed.

## Injection style

All three base classes currently use `@Autowired lateinit var` fields, not
constructor injection. This is a legacy pattern; the shared references say
constructor injection is preferred.

**For new test classes:** use `@Autowired constructor(...)` on the subclass.
The base class's `lateinit var` fields stay as-is (changing them is a
cross-cutting refactor outside the scope of this skill).

**For modernization:** only convert field injection to constructor injection
if the fields are declared in the test class itself, not inherited from the
base. Do not touch the base class from this skill.

## Naming

Backticked sentences in German or English, matching existing test in the
area. Examples from the codebase:

```kotlin
@Test
fun `Should enqueue E-Mail`() { ... }

@Test
fun `OAuth provider returns anonymous user without email`() { ... }
```

User-visible product text is German; test names can mix.

## Package structure

Tests mirror production under `src/test/kotlin/de/tschuehly/photoquest/`:

- `analytics/` / `common/` / `core/<feature>/` / `tracking/` / `web/` — same
  split as main code
- `util/` — test infrastructure (base classes, fixtures, page objects)

Place new tests next to the production code they exercise. Playwright page
objects go under `util/page/`.

## Gotchas

- **Thread-local cleanup is automatic** in base classes (`SecurityContextHolder`,
  `RequestContextHolder`). Don't add your own `@AfterEach` for these.
- **ViewContext test IDs**: Playwright tests should use `TestId` constants
  defined on the `ViewContext` companion, not hardcoded selectors. See
  existing page objects.
- **Gallery Playwright screenshots**: never use `fullPage = true` — gallery
  has infinite scroll; full-page captures are misleading.
- **Advisory locks**: multi-instance-safe code uses `AdvisoryLock.kt`. When
  testing concurrency, assert through the DB, not in-memory state.
- **German user-visible text**: assertions against rendered HTML or email
  content check German strings. Test names and code comments stay English.

## Related conventions

- Full testing reference: `docs/architecture/playwright-testing.md`,
  `docs/architecture/test-data.md`.
- Rule file loaded by path: `.claude/rules/testing.md` (auto-attached when
  working under `src/test/kotlin/**`).
