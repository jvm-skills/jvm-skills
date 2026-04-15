# SkillsJar packaging

Packages the locally-authored skills in this repo as a [SkillsJar](https://www.skillsjars.com/docs) for distribution via Maven Central.

## What gets shipped

`stage-skills.sh` walks `skills/<category>/*.yaml` and includes every entry where `repo: jvm-skills/jvm-skills`. For each match it copies the directory pointed to by `skill_path` (e.g. `.claude/skills/commit/`) into `target/staging-skills/<skill-name>/`. Externally-hosted skills listed in the registry are ignored.

Registry entry in → skill out: the registry is the source of truth. To add or drop a skill from the SkillsJar, edit its `skills/<category>/*.yaml` entry.

## Build

```
mvn package
```

Produces `target/jvm-skills-<version>.jar` with each skill at `META-INF/skills/<group>/<skill>/SKILL.md` plus any bundled helper files.

## Publish

SkillsJars has no public API/CLI. Publishing is one-click via their web form:

1. Push `main` to `github.com/jvm-skills/jvm-skills` (public).
2. Go to https://www.skillsjars.com/ and submit the repo URL via **Publish a SkillsJar**.
3. Their backend runs `mvn package` at the repo root and deploys to Maven Central.

To cut a new version, bump `<version>` in `pom.xml`, push, and re-submit the form.
