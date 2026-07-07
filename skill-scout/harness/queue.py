#!/usr/bin/env python3
"""Emit unscanned conferences (empty roster_fetched_at) with DETERMINISTIC slugs, as JSON:
{"confs":[{"name","url","slug"}]}. Deterministic slug = lowercase-alnum of the name minus the
year, deduped with a numeric suffix. Replaces LLM slug generation so trials/reruns are reproducible
and cached rosters (<slug>_speakers.json) reliably match.
"""
import csv, json, re, sys, os
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db")

def slugify(name):
    s = re.sub(r"\b(19|20)\d{2}\b", "", name)        # drop a 4-digit year
    return re.sub(r"[^a-z0-9]+", "", s.lower()) or "conf"

rows = list(csv.DictReader(open(os.path.join(DB, "conferences.csv"))))
seen, out = {}, []
for r in rows:
    if r.get("roster_fetched_at"):
        continue
    base = slugify(r["name"]); s = base; i = 2
    while s in seen:
        s = f"{base}{i}"; i += 1
    seen[s] = 1
    out.append({"name": r["name"], "url": r["url"], "slug": s})
json.dump({"confs": out}, sys.stdout)
