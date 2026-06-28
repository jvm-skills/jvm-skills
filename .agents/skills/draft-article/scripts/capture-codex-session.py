#!/usr/bin/env python3
"""Copy a Codex session into a private article draft and create a readable extract."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def find_session(codex_home: Path, session_id: str) -> Path:
    matches = []
    search_roots = [
        codex_home / "sessions",
        codex_home / "archived_sessions",
    ]
    for root in search_roots:
        if root.exists():
            matches.extend(root.rglob(f"*{session_id}*.jsonl"))

    if not matches:
        for path in codex_home.rglob("*.jsonl"):
            try:
                if session_id in path.read_text(errors="ignore"):
                    matches.append(path)
            except OSError:
                continue

    matches = sorted(set(matches))
    exact = [path for path in matches if session_id in path.name]
    if exact:
        return exact[0]
    if matches:
        return matches[0]
    raise FileNotFoundError(f"No Codex session found for {session_id} under {codex_home}")


def find_shell_snapshot(codex_home: Path, session_id: str) -> Path | None:
    snapshot_dir = codex_home / "shell_snapshots"
    if not snapshot_dir.exists():
        return None
    matches = sorted(snapshot_dir.glob(f"{session_id}*.sh"))
    return matches[0] if matches else None


def content_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return str(content.get("text") or content.get("content") or "")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            elif item is not None:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return "" if content is None else str(content)


def message_from_record(record: dict) -> tuple[str, str, str] | None:
    timestamp = str(record.get("timestamp", ""))
    payload = record.get("payload") or {}

    if record.get("type") == "response_item" and payload.get("type") == "message":
        role = payload.get("role")
        if role in {"user", "assistant"}:
            return timestamp, role, content_text(payload.get("content"))

    event_type = payload.get("type")
    if event_type in {"user_message", "agent_message"}:
        role = "user" if event_type == "user_message" else "assistant"
        text = content_text(payload.get("message") or payload.get("text") or payload.get("content"))
        return timestamp, role, text

    return None


def write_extract(raw_session: Path, extract_path: Path) -> int:
    count = 0
    with raw_session.open("r", encoding="utf-8", errors="replace") as source:
        with extract_path.open("w", encoding="utf-8") as target:
            for line in source:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                message = message_from_record(record)
                if message is None:
                    continue
                timestamp, role, text = message
                if not text.strip():
                    continue
                target.write(f"--- {timestamp} {role} ---\n{text}\n\n")
                count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--draft-dir", required=True, type=Path)
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    args = parser.parse_args()

    draft_dir = args.draft_dir
    session_dir = draft_dir / "raw" / "session"
    session_dir.mkdir(parents=True, exist_ok=True)

    source_session = find_session(args.codex_home, args.session_id)
    target_session = session_dir / f"codex-session-{args.session_id}.jsonl"
    shutil.copy2(source_session, target_session)

    source_snapshot = find_shell_snapshot(args.codex_home, args.session_id)
    target_snapshot = None
    if source_snapshot:
        target_snapshot = session_dir / f"shell-snapshot-{args.session_id}.sh"
        shutil.copy2(source_snapshot, target_snapshot)

    extract_path = draft_dir / f"conversation-extract-{args.session_id}.md"
    message_count = write_extract(target_session, extract_path)

    source_hash = sha256(source_session)
    target_hash = sha256(target_session)
    if source_hash != target_hash:
        raise RuntimeError("Copied session checksum does not match source")

    print(f"session: {source_session}")
    print(f"copied: {target_session}")
    print(f"session_lines: {line_count(target_session)}")
    print(f"extract: {extract_path}")
    print(f"messages: {message_count}")
    if target_snapshot:
        print(f"snapshot: {target_snapshot}")
    else:
        print("snapshot: none")
    print(f"sha256: {target_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
