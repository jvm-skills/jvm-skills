#!/usr/bin/env python3
"""Merge chunked scout outputs into one <conf>_scout.json.
Usage: merge_scout.py <out.json> <part0.json> [<part1.json> ...]
Concatenates `resolutions` and dict-merges `scans` (keyed by login). Idempotent.
"""
import json, sys
out, parts = sys.argv[1], sys.argv[2:]
merged = {"resolutions": [], "scans": {}}
for p in parts:
    d = json.load(open(p))
    merged["resolutions"].extend(d.get("resolutions", []))
    merged["scans"].update(d.get("scans", {}))
json.dump(merged, open(out, "w"), indent=2)
n_hits = sum(len(h["paths"]) for s in merged["scans"].values() for h in s["hits"])
print(f"merged {len(parts)} parts -> {out}: {len(merged['resolutions'])} resolutions, "
      f"{len(merged['scans'])} scanned handles, {n_hits} skill-file hits")
