#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inject task context into spawned agents (Codex hook compatible)."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

DIR_HARNESS = ".harness"
FILE_CURRENT_TASK = ".current-task"
MAX_FILES = 20
MAX_CHARS_PER_FILE = 12000

AGENT_KEYWORDS = [
    (["check", "review", "verify", "qa"], "check"),
    (["debug", "fix", "bugfix"], "debug"),
    (["finish", "complete", "pr"], "finish"),
    (["research", "explore", "analyze"], "research"),
    (["implement", "code", "build", "create", "develop"], "implement"),
]


def find_harness_dir() -> Path | None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        candidate = Path(project_dir) / DIR_HARNESS
        if candidate.is_dir():
            return candidate

    candidate = Path.cwd() / DIR_HARNESS
    if candidate.is_dir():
        return candidate

    current = Path.cwd().resolve()
    while current != current.parent:
        candidate = current / DIR_HARNESS
        if (current / ".git").exists() and candidate.is_dir():
            return candidate
        current = current.parent
    return None


def read_jsonl(filepath: str) -> list[dict]:
    entries: list[dict] = []
    if not os.path.isfile(filepath):
        return entries
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except (OSError, UnicodeDecodeError):
        return []
    return entries


def read_file_content(path: str, max_chars: int = MAX_CHARS_PER_FILE) -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(max_chars + 1)
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[... truncated ...]"
        return content
    except (OSError, UnicodeDecodeError):
        return None


def read_directory_md_files(path: str, max_chars: int = MAX_CHARS_PER_FILE) -> str | None:
    if not os.path.isdir(path):
        return None
    chunks: list[str] = []
    per_file = max(max_chars // 10, 2000)
    for filename in sorted(os.listdir(path)):
        if not filename.endswith(".md"):
            continue
        content = read_file_content(os.path.join(path, filename), per_file)
        if content:
            chunks.append(f"### {filename}\n\n{content}")
    return "\n\n".join(chunks) if chunks else None


def extract_file_paths_from_prd(prd_path: str) -> list[str]:
    if not os.path.isfile(prd_path):
        return []
    try:
        text = Path(prd_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    patterns = [
        r"`([\w./\-]+\.[a-zA-Z]{1,6})`",
        r"\b(src/[\w./\-]+\.[a-zA-Z]{1,6})\b",
        r"\b(tests/[\w./\-]+\.[a-zA-Z]{1,6})\b",
        r"\b(configs/[\w./\-]+\.[a-zA-Z]{1,6})\b",
    ]
    found: set[str] = set()
    for pattern in patterns:
        for item in re.findall(pattern, text):
            if not item.startswith("http") and os.path.isfile(item):
                found.add(item)
    return list(found)[:5]


def resolve_path(path: str, harness_dir: Path, task_dir: str | None) -> str | None:
    candidate = str(harness_dir / path)
    if os.path.exists(candidate):
        return candidate
    if task_dir:
        candidate = os.path.join(task_dir, path)
        if os.path.exists(candidate):
            return candidate
    if os.path.exists(path):
        return path
    return None


def detect_stage(agent_hint: str, prompt_hint: str) -> str:
    agent_hint = agent_hint.lower()
    prompt_hint = prompt_hint.lower()
    combined = f"{agent_hint} {prompt_hint}"

    for keys, stage in AGENT_KEYWORDS:
        if any(k in agent_hint for k in keys):
            return stage
    for keys, stage in AGENT_KEYWORDS:
        if any(k in combined for k in keys):
            return stage
    return "implement"


def parse_hook_agent_context(hook_input: dict) -> tuple[str, str] | None:
    event_name = str(hook_input.get("hook_event_name", "")).lower()

    if event_name == "subagentstart":
        agent_type = str(hook_input.get("agent_type", ""))
        return agent_type, ""

    if event_name == "pretooluse":
        tool_name = str(hook_input.get("tool_name", ""))
        if tool_name not in {"Task", "spawn_agent", "spawn_team", "team_message"}:
            return None

        tool_input = hook_input.get("tool_input", {})
        if not isinstance(tool_input, dict):
            tool_input = {}

        agent_type = str(tool_input.get("agent_type") or tool_input.get("subagent_type") or "")
        prompt_parts: list[str] = []
        for key in ("prompt", "message", "task"):
            value = tool_input.get(key)
            if isinstance(value, str):
                prompt_parts.append(value)

        items = tool_input.get("items")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    prompt_parts.append(item["text"])

        return agent_type, "\n".join(prompt_parts)

    return None


def main() -> None:
    harness_dir = find_harness_dir()
    if not harness_dir:
        return

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    parsed = parse_hook_agent_context(hook_input)
    if parsed is None:
        return

    agent_hint, prompt_hint = parsed
    stage = detect_stage(agent_hint, prompt_hint)

    current_task = harness_dir / FILE_CURRENT_TASK
    if not current_task.is_file():
        return
    task_dir = current_task.read_text(encoding="utf-8").strip()
    if not task_dir:
        return

    entries = read_jsonl(os.path.join(task_dir, f"{stage}.jsonl"))
    if not entries:
        entries = read_jsonl(os.path.join(task_dir, "spec.jsonl"))

    if stage == "implement":
        prd_path = os.path.join(task_dir, "prd.md")
        auto_paths = extract_file_paths_from_prd(prd_path)
        existing = {entry.get("file") or entry.get("path") for entry in entries}
        for path in auto_paths:
            if path not in existing:
                entries.append({"file": path, "reason": "auto-discovered from prd.md"})

    if not entries:
        return

    blocks: list[str] = []
    for entry in entries[:MAX_FILES]:
        path = entry.get("file") or entry.get("path")
        if not path:
            continue
        file_type = entry.get("type", "file")
        resolved = resolve_path(path, harness_dir, task_dir)
        if not resolved:
            continue

        if file_type == "directory":
            content = read_directory_md_files(resolved)
        else:
            content = read_file_content(resolved)
        if not content:
            continue

        reason = entry.get("reason", "")
        title = f"## [{path}]" + (f" — {reason}" if reason else "")
        blocks.append(f"{title}\n\n{content}")

    if not blocks:
        return

    payload = (
        f"# Injected Context ({stage} stage)\n\n"
        + "\n\n---\n\n".join(blocks)
    )
    json.dump({"additionalContext": payload}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
