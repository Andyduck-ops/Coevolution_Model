#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SessionStart hook: inject harness context for Codex hooks."""

from __future__ import annotations

import json
import os
import sys
from io import StringIO
from pathlib import Path

DIR_HARNESS = ".harness"
FILE_CURRENT_TASK = ".current-task"
FILE_STALE = ".stale-knowledge.json"
MAX_STALE_WARNINGS = 5
MAX_LESSONS_CHARS = 4000


def should_skip_injection() -> bool:
    return (
        os.environ.get("CLAUDE_NON_INTERACTIVE") == "1"
        or os.environ.get("OPENCODE_NON_INTERACTIVE") == "1"
        or os.environ.get("CODEX_NON_INTERACTIVE") == "1"
    )


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


def read_file(path: Path, max_chars: int = 0, fallback: str = "") -> str:
    try:
        content = path.read_text(encoding="utf-8")
        if max_chars and len(content) > max_chars:
            return content[:max_chars] + "\n\n[... truncated ...]"
        return content
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return fallback


def main() -> None:
    if should_skip_injection():
        return

    harness_dir = find_harness_dir()
    if not harness_dir:
        return

    output = StringIO()
    output.write("<harness-context>\n")
    output.write("Harness runtime active. Follow .harness/workflow.md and current task boundaries.\n\n")

    lessons_index = harness_dir / "spec" / "lessons" / "index.md"
    lessons = read_file(lessons_index, max_chars=MAX_LESSONS_CHARS)
    if lessons:
        output.write("## Project Lessons\n\n")
        output.write(lessons)
        output.write("\n\n")

    stale_file = harness_dir / FILE_STALE
    if stale_file.is_file():
        try:
            stale_items = json.loads(stale_file.read_text(encoding="utf-8"))
            if stale_items:
                output.write("## Stale Knowledge\n\n")
                for entry in stale_items[:MAX_STALE_WARNINGS]:
                    output.write(
                        f"- `{entry.get('file', '?')}` drifted from `{entry.get('spec', '?')}`\n"
                    )
                output.write("\n")
        except (json.JSONDecodeError, OSError):
            pass

    current_task_file = harness_dir / FILE_CURRENT_TASK
    if current_task_file.is_file():
        task_dir = current_task_file.read_text(encoding="utf-8").strip()
        if task_dir:
            output.write("## Active Task\n\n")
            output.write(f"- task_dir: `{task_dir}`\n")
            prd_path = Path(task_dir) / "prd.md"
            if prd_path.is_file():
                output.write(f"- prd: `{prd_path}`\n")
            output.write("\n")

    output.write("</harness-context>")
    payload = output.getvalue().strip()
    if payload:
        json.dump({"additionalContext": payload}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
