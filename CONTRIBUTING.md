# Contributing to jvm-skills

Thanks for your interest in contributing! jvm-skills is a curated directory of AI coding skills for JVM developers.

## Adding a Skill Listing

The easiest way to contribute is to add a new skill listing.

### Step-by-step

1. **Fork** this repository
2. **Create a YAML file** in the appropriate category directory:
   ```
   skills/<category>/<name>.yaml
   ```
   Categories: `framework`, `language`, `database`, `testing`, `fullstack`, `web`, `workflow`, `tool`

3. **Fill in all required fields:**

   ```yaml
   name: My Awesome Skill
   description: >-
     A one-paragraph description of what this skill teaches AI coding tools.
     Be specific about the technologies and patterns covered.
   repo: your-username/your-skill-repo
   category: database
   tools:
     - claude
     - cursor
   languages:
     - kotlin
     - java
   trust: community
   author: Your Name
   tags:
     - relevant
     - tags
   ```

   Optional fields: `maintainer`, `version`, `last_updated`, `min_spring_boot`, `screenshots`

4. **Open a PR** — CI will automatically validate your YAML

### Field Reference

| Field | Required | Notes |
|-------|----------|-------|
| `name` | yes | Display name |
| `description` | yes | One paragraph, shown on the card |
| `repo` | yes | GitHub `owner/repo` where the skill lives |
| `category` | yes | One of: framework, language, database, testing, fullstack, web, workflow, tool |
| `tools` | yes | AI tools: claude, cursor, copilot, windsurf, aider |
| `languages` | yes | kotlin, java, or both |
| `trust` | yes | `community` for PR submissions (`official` and `curated` assigned by maintainers) |
| `author` | yes | Person or org who created the skill |
| `tags` | no | Freeform tags for filtering |

### Trust Levels

- **Official** — The library/tool maker wrote this skill (e.g., Lukas Eder for jOOQ). Assigned by maintainers.
- **Curated** — Written by a recognized expert, vetted by maintainers. Assigned by maintainers.
- **Community** — Submitted via PR. Set `trust: community` in your YAML.

## Local Development

Build the site locally to preview your changes:

```bash
# Requires Kotlin (https://kotlinlang.org/docs/command-line.html)
# Install via: sdk install kotlin
kotlin site/build.main.kts
open dist/index.html

# Or use the live-reload dev server
./site/watch.sh
```

## Questions?

Open an issue or reach out to [@tschuehly](https://github.com/tschuehly).
