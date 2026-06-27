#!/usr/bin/env python3
"""Cross-repo skill dedup for the human views (candidates.md / review.html).

The eval judges each SKILL.md file independently, so an author who copies the same skill into
several repos (e.g. Anton Arhipov's `spring-batch-6` lives in agentskills + sdd-demo + sdd-workshop)
gets it promoted N times — and, because the Opus recheck's "lives in a demo repo" bias fires
non-deterministically, the SAME skill can land in BOTH the found and the rejected pile. That is the
opposite of "easy to decide".

These helpers collapse that at the view layer (the CSVs stay lossless, full provenance intact):
  - dedup_found(rows, stars_by): one canonical row per (author, skill-name); prefer a non-demo repo,
    then most stars, then name. The canonical row gets r["_dupes"] = [other repo names].
  - found_keys(rows): the set of (login, skill-name) already promoted — use it to drop the duplicate
    copies out of the rejected/review sections so a promoted skill never also shows as rejected.
"""
import re

# repo-name shapes that make a worse "canonical home" for a reusable skill than a plain collection
DEMO_RX = re.compile(r"(demo|workshop|sample|example|playground|talk|kata|sdd|training|tutorial|conf\b)", re.I)


def skill_name(path):
    """The skill's identity within a repo: the dir holding SKILL.md, else the file stem."""
    if "/" in path:
        return path.split("/")[-2]
    return path.rsplit(".", 1)[0] if "." in path else path


def _stars(stars_by, r):
    try:
        return int(stars_by.get((r["login"], r["repo"]), 0) or 0)
    except (TypeError, ValueError):
        return 0


def _key(r):
    return (r["login"], skill_name(r.get("path", "")))


def dedup_found(rows, stars_by):
    """Collapse same-author same-skill copies to one canonical row (+ ._dupes list of other repos)."""
    groups = {}
    for r in rows:
        groups.setdefault(_key(r), []).append(r)
    out = []
    for g in groups.values():
        ranked = sorted(g, key=lambda r: (bool(DEMO_RX.search(r["repo"])), -_stars(stars_by, r), r["repo"]))
        canon = dict(ranked[0])
        canon["_dupes"] = [r["repo"] for r in ranked[1:]]
        out.append(canon)
    return out


def found_keys(rows):
    """(login, skill-name) pairs that were promoted — drop their copies from the rejected views."""
    return {_key(r) for r in rows}
