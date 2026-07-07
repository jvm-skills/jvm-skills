#!/usr/bin/env python3
"""Append new alias decisions from per-conference add-files into db/aliases.csv, skipping duplicates.
Parallel investigate agents each write their own add-file; this serial step merges them safely.
Usage: merge_aliases.py <aliases.csv> <add1.csv> [add2.csv ...]
Add-file rows: norm_name,github_login,decision,source,note,decided_at  (no header).
"""
import csv, sys, os, io
COLS = ["norm_name", "github_login", "decision", "source", "note", "decided_at"]
master, adds = sys.argv[1], sys.argv[2:]
rows, seen, added = [], set(), 0
if os.path.exists(master):
    for r in csv.DictReader(open(master)):
        rows.append(r); seen.add((r["norm_name"], r["github_login"]))
for a in adds:
    if not os.path.exists(a):
        continue
    for line in csv.reader(open(a)):
        if len(line) < 2 or not line[0].strip() or line[0].strip() == "norm_name":
            continue
        rec = dict(zip(COLS, (line + [""] * 6)[:6]))
        k = (rec["norm_name"], rec["github_login"])
        if k in seen:
            continue
        seen.add(k); rows.append(rec); added += 1
buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=COLS, lineterminator="\n"); w.writeheader()
for r in rows:
    w.writerow({c: r.get(c, "") for c in COLS})
open(master, "w").write(buf.getvalue())
print(f"aliases: +{added} new ({len(rows)} total)")
