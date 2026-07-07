#!/usr/bin/env python3
"""Split a <conf>_speakers.json ([[name,aff],...]) into chunk files of <=SIZE.
Usage: split_speakers.py <speakers.json> <out_prefix> <size>
Writes <out_prefix>_0.json, _1.json, ... and prints the chunk count (stdout, single int).
Chunking keeps each downstream scout.py call under the 10-min foreground Bash timeout.
"""
import json, sys
src, prefix, size = sys.argv[1], sys.argv[2], int(sys.argv[3])
sp = json.load(open(src))
if len(sys.argv) > 4 and sys.argv[4].isdigit() and int(sys.argv[4]) > 0:
    sp = sp[:int(sys.argv[4])]  # optional speaker cap (for small trials)
chunks = [sp[i:i+size] for i in range(0, len(sp), size)] or [[]]
for i, c in enumerate(chunks):
    json.dump(c, open(f"{prefix}_{i}.json", "w"))
print(len(chunks))
