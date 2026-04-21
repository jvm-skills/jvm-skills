#!/usr/bin/env python3
"""Triage pitest survivors into LIKELY_KILLABLE / LIKELY_EQUIVALENT / AMBIGUOUS.

Reads `mutations.xml`, opens the source line at each survivor's `file:line`,
and applies three static archetypes (v0.3):

    A. Logger-gate conditionals   — `if (X > 0) { logger.info(...) }`
    B. Loop-bound mutations        — on `for` / `while` / `do..while` conditions
    C. Null-elvis throw            — `<value> ?: throw ...` where `<value>` is
                                     non-nullable in practice

Anything that matches no archetype is AMBIGUOUS (bias: never flag real gaps as
equivalent — false negatives are cheap, false positives silently hide bugs).

Usage:
    triage.py <mutations.xml> <source-root> [--out-dir DIR]

Outputs `triage.md` (human) and `triage.json` (machine) next to mutations.xml
by default, or in --out-dir if given.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path

LOGGER_CALL = re.compile(
    r"\b(logger|log|slf4j|klog|klogger|tracer|tracing|metrics?)\s*\.\s*"
    r"(info|warn|warning|error|debug|trace|fine|finer|finest|severe|log|record|measure|increment|counter|gauge)\s*\("
)
NULL_ELVIS_THROW = re.compile(r"\?:\s*throw\b")
LOOP_HEADER = re.compile(r"^\s*(for|while|do)\b|^\s*\}\s*while\b")
JUNIT5_CLASS = re.compile(r"\[class:([^\]]+)\]")
JUNIT5_METHOD = re.compile(r"\[method:([^\]]+?)\]")

CONDITIONAL_MUTATORS = {
    "ConditionalsBoundary",
    "RemoveConditional_ORDER_ELSE",
    "RemoveConditional_ORDER_IF",
    "RemoveConditional_EQUAL_ELSE",
    "RemoveConditional_EQUAL_IF",
}


@dataclass
class Survivor:
    file: str
    line: int
    fqn: str
    method: str
    mutator: str
    description: str
    bucket: str
    reason: str
    covering_tests: list[str]


def short_mutator(fqn: str) -> str:
    return fqn.rsplit(".", 1)[-1].replace("Mutator", "")


def parse_covering_tests(raw: str | None) -> list[str]:
    """Parse pitest's `<coveringTests>` / `<succeedingTests>` payload.

    Format (fullMutationMatrix=true, junit5): each entry is
        <classFQN>.[engine:junit-jupiter]/[class:<classFQN>]/[method:<name>()]
    separated by `|`. Returns `ShortClass.methodName` pairs for display.
    Falls back to the raw entry if the junit5 ID pattern doesn't match
    (e.g. junit4 or older pitest versions).
    """
    if not raw:
        return []
    out: list[str] = []
    for item in raw.split("|"):
        item = item.strip()
        if not item:
            continue
        cls_match = JUNIT5_CLASS.search(item)
        method_match = JUNIT5_METHOD.search(item)
        if cls_match and method_match:
            short_cls = cls_match.group(1).rsplit(".", 1)[-1]
            method = method_match.group(1).strip()
            if method.endswith("()"):
                method = method[:-2]
            out.append(f"{short_cls}.{method}")
        else:
            out.append(item)
    return out


def resolve_source(src_root: Path, source_file: str, class_fqn: str) -> Path | None:
    pkg = class_fqn.rsplit(".", 1)[0]
    # Nested / inner classes: pkg has $ — strip back to the enclosing class's package
    pkg = pkg.split("$", 1)[0]
    pkg_path = pkg.replace(".", "/")
    for base in ("src/main/kotlin", "src/main/java"):
        candidate = src_root / base / pkg_path / source_file
        if candidate.exists():
            return candidate
    return None


def body_is_logger_only(lines: list[str], header_idx: int) -> bool:
    """header_idx is 0-indexed line of the `if (...)` header."""
    if header_idx >= len(lines):
        return False
    header = lines[header_idx]
    # Single-statement form: `if (X > 0) logger.info(...)` without braces
    if "{" not in header:
        if header_idx + 1 < len(lines):
            after = lines[header_idx + 1].strip()
            return bool(LOGGER_CALL.search(after))
        return False
    # Multi-line form: walk body until matching closing brace
    depth = header.count("{") - header.count("}")
    # Any content on same line after the opening brace
    tail = header.split("{", 1)[1].strip()
    if tail and not tail.startswith("}"):
        if not LOGGER_CALL.search(tail):
            return False
    i = header_idx + 1
    while i < len(lines) and depth > 0:
        raw = lines[i]
        stripped = raw.strip()
        depth += raw.count("{") - raw.count("}")
        if stripped and not stripped.startswith("//") and not stripped.startswith("*"):
            content = stripped.rstrip("}").rstrip(",").strip()
            if content and not content.startswith("//"):
                # Allow string-continuation arguments spilling across lines
                if content.startswith('"') or content.endswith(","):
                    i += 1
                    continue
                if not LOGGER_CALL.search(content):
                    return False
        i += 1
    return True


def classify(mutation: ET.Element, src_root: Path) -> Survivor | None:
    if mutation.attrib.get("status") != "SURVIVED":
        return None

    mutator = short_mutator(mutation.findtext("mutator", ""))
    source_file = mutation.findtext("sourceFile", "")
    fqn = mutation.findtext("mutatedClass", "")
    method = mutation.findtext("mutatedMethod", "")
    line = int(mutation.findtext("lineNumber", "0"))
    description = mutation.findtext("description", "")

    # Prefer <succeedingTests> — the matrix of tests that ran and let this
    # mutant live (present when fullMutationMatrix=true). Fall back to
    # <coveringTests> (line-coverage based).
    covering = parse_covering_tests(
        mutation.findtext("succeedingTests") or mutation.findtext("coveringTests")
    )

    path = resolve_source(src_root, source_file, fqn)
    if not path or line < 1:
        return Survivor(source_file, line, fqn, method, mutator, description,
                        "AMBIGUOUS", "source file not resolved", covering)

    lines = path.read_text().splitlines()
    if line > len(lines):
        return Survivor(source_file, line, fqn, method, mutator, description,
                        "AMBIGUOUS", f"line {line} out of range ({len(lines)} lines)", covering)
    line_text = lines[line - 1]
    stripped = line_text.strip()

    # Archetype C — null-elvis throw
    if NULL_ELVIS_THROW.search(line_text) and mutator in {
        "RemoveConditional_EQUAL_IF", "RemoveConditional_EQUAL_ELSE",
    }:
        return Survivor(source_file, line, fqn, method, mutator, description,
                        "LIKELY_EQUIVALENT", "archetype C: null-elvis throw on value non-nullable in practice", covering)

    # Archetype A — logger-gate
    if mutator in CONDITIONAL_MUTATORS and stripped.startswith("if "):
        if body_is_logger_only(lines, line - 1):
            return Survivor(source_file, line, fqn, method, mutator, description,
                            "LIKELY_EQUIVALENT", "archetype A: logger-gate conditional", covering)

    # Archetype B — loop bound
    if mutator in CONDITIONAL_MUTATORS and LOOP_HEADER.match(line_text):
        return Survivor(source_file, line, fqn, method, mutator, description,
                        "LIKELY_EQUIVALENT", "archetype B: loop-bound comparison", covering)

    return Survivor(source_file, line, fqn, method, mutator, description,
                    "LIKELY_KILLABLE", "no archetype matched", covering)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mutations_xml", type=Path)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--out-dir", type=Path, default=None,
                        help="Output directory (default: alongside mutations.xml)")
    args = parser.parse_args(argv[1:])

    if not args.mutations_xml.is_file():
        print(f"error: {args.mutations_xml} not found", file=sys.stderr)
        return 1
    if not args.source_root.is_dir():
        print(f"error: {args.source_root} not a directory", file=sys.stderr)
        return 1

    tree = ET.parse(args.mutations_xml)
    survivors: list[Survivor] = []
    for m in tree.getroot().findall("mutation"):
        s = classify(m, args.source_root)
        if s is not None:
            survivors.append(s)

    buckets: dict[str, list[Survivor]] = defaultdict(list)
    for s in survivors:
        buckets[s.bucket].append(s)

    out_dir = args.out_dir or args.mutations_xml.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "triage.md"
    json_path = out_dir / "triage.json"

    total = len(survivors)
    with md_path.open("w") as f:
        f.write(f"# Triage of {total} survivors\n\n")
        for bucket in ("LIKELY_KILLABLE", "AMBIGUOUS", "LIKELY_EQUIVALENT"):
            entries = buckets.get(bucket, [])
            f.write(f"## {bucket} ({len(entries)})\n\n")
            for e in sorted(entries, key=lambda s: (s.file, s.line, s.mutator)):
                f.write(f"- `{e.file}:{e.line}` **{e.mutator}** — {e.description}\n")
                f.write(f"  - in `{e.fqn.rsplit('.', 1)[-1]}.{e.method}()`\n")
                f.write(f"  - reason: {e.reason}\n")
                if e.covering_tests:
                    f.write("  - covering tests:\n")
                    for t in e.covering_tests:
                        f.write(f"    - `{t}`\n")
                else:
                    f.write("  - covering tests: _none named — enable `fullMutationMatrix=true` in `pitest {}`_\n")
                f.write("\n")

    json_path.write_text(json.dumps(
        {bucket: [asdict(s) for s in entries] for bucket, entries in buckets.items()},
        indent=2,
    ))

    for bucket in ("LIKELY_KILLABLE", "AMBIGUOUS", "LIKELY_EQUIVALENT"):
        print(f"{bucket:<20} {len(buckets.get(bucket, [])):3d}")
    print(f"\nWrote {md_path}")
    print(f"Wrote {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
