# Skill-Scout data store — CSV

Git-tracked CSV files are the **system of record** for the speaker→github→skill loop.
Plain text → diffable in PRs, greppable, editable, no binary, no dependency. `candidates.md`
is a **generated human view**; these CSVs are the source it's built from.

Joins use **natural keys** (`norm_name`, `login`, `repo`) so the files read on their own.

`conferences.csv` is the **queue**: rows with empty `roster_fetched_at` are unscanned. It is seeded from
the community list at https://github.com/javaconferences/javaconferences.github.io (latest already-held
edition of each conference, ~last year; general/non-JVM mega-conferences trimmed). `apply.py` stamps the
date as each is scanned.

| File | Grain | Columns | Key / dedupe |
|---|---|---|---|
| `conferences.csv` | one conference | `name, url, roster_fetched_at` | `name` |
| `speakers.csv` | one person | `name, norm_name, affiliation` | `norm_name` |
| `speaker_conferences.csv` | speaker×conference | `norm_name, conference` | both |
| `resolutions.csv` | github identity per speaker | `norm_name, github_login, confidence, gh_name, gh_company, followers, method, resolved_at, recheck_after` | `norm_name` |
| `repos.csv` | owned non-fork repo | `login, name, is_fork, stars, pushed_at, head_sha, last_scanned_at` | `login,name` |
| `skill_files.csv` | one **promoted** skill (found/needs_review) | `login, repo, path, status, depth, jvm_fit, category, lines, notes, first_seen, last_seen` | `login,repo,path` |
| `rejected.csv` | every scanned hit **not** promoted | `login, repo, path, reason, note, first_seen, last_seen` | `login,repo,path` |
| `runs.csv` | append-only ledger | `started_at, conference, speakers, resolved, scanned_repos, skipped_repos, found, parked, notes` | append |

`confidence` ∈ `HIGH｜MED｜UNRESOLVED`. `skill_file.status` ∈ `found｜needs_review`.

**`rejected.csv` `reason`** (auto-classified by `harness/classify.py`, so nothing is silently dropped):
`jvm-collection` (real JVM skill in a found collection — promote-worthy) · `off-topic-workflow` /
`off-topic-service` / `off-topic-tech` (real reusable skills that are **not** JVM-specific — reviewable) ·
`demo` · `boilerplate` (OpenSpec / Tessl iikit / SDD templates) · `vendored` (third-party skill copied in) ·
`project-doc` (bare CLAUDE.md/AGENTS.md) · `test-fixture` · `already-listed` (EXCLUDE) · `review` (unjudged).

## How the loop uses it (no SQL engine required)
- **Dedupe / upsert:** before writing, the loop checks the key columns; existing row → update in place,
  else append. (A few lines of Python/awk; idempotent by key.)
- **Incremental re-fetch:** compare a repo's live HEAD `sha`/`pushed_at` to the stored value in
  `repos.csv`; re-walk only changed/new repos. Retry `resolutions.csv` rows whose `recheck_after <= today`.
- **Quoting:** fields containing commas are double-quoted (RFC-4180), e.g. `"Code Monkey, LLC"`.

## Querying (optional)
No import step needed. Examples:
```bash
# pretty-print
column -s, -t skill_files.csv | less -S

# SQL directly over CSV (no load) — DuckDB
duckdb -c "SELECT login,repo,category,depth,stars
           FROM 'skill_files.csv' s JOIN 'repos.csv' r USING(login)
           WHERE s.status='found' ORDER BY stars DESC;"

# repos due for re-scan (plain awk)
awk -F, 'NR>1 && $7 < "2026-05-27"' repos.csv
```
