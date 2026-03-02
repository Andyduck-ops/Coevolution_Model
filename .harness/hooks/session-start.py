#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SessionStart hook — inject global context at session start.

Derived from Trellis session-start.py (battle-tested, 18 rounds of iteration).

Injected context:
- Workflow guide summary
- Top lessons from lessons/index.md
- Staleness warnings (if any)
- Current task pointer (if active)
"""

# IMPORTANT: Suppress all warnings FIRST
import warnings
warnings.filterwarnings("ignore")

import json
import os
import sys
from io import StringIO
from pathlib import Path

# IMPORTANT: Force stdout to use UTF-8 on Windows
if sys.platform == "win32":
    import io as _io
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    elif hasattr(sys.stdout, "detach"):
        sys.stdout = _io.TextIOWrapper(
            sys.stdout.detach(), encoding="utf-8", errors="replace"
        )

# =============================================================================
# Configuration
# =============================================================================

DIR_HARNESS = ".harness"
FILE_CURRENT_TASK = ".current-task"
FILE_STALE = ".stale-knowledge.json"
MAX_STALE_WARNINGS = 5
MAX_LESSONS_CHARS = 4000  # ~1000 tokens


def should_skip_injection() -> bool:
    """Skip injection in non-interactive mode (CI, background agents)."""
    return (
        os.environ.get("CLAUDE_NON_INTERACTIVE") == "1"
        or os.environ.get("OPENCODE_NON_INTERACTIVE") == "1"
        or os.environ.get("CODEX_NON_INTERACTIVE") == "1"
    )


def find_harness_dir() -> Path | None:
    """Find .harness/ directory, checking CLAUDE_PROJECT_DIR first."""
    # Try environment variable first
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        candidate = Path(project_dir) / DIR_HARNESS
        if candidate.is_dir():
            return candidate

    # Try current directory
    candidate = Path.cwd() / DIR_HARNESS
    if candidate.is_dir():
        return candidate

    # Walk up to find .git, then check for .harness/ there
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / ".git").exists() and (current / DIR_HARNESS).is_dir():
            return current / DIR_HARNESS
        current = current.parent

    return None


def read_file(path: Path, max_chars: int = 0, fallback: str = "") -> str:
    """Read file with optional truncation and UTF-8 safety."""
    try:
        content = path.read_text(encoding="utf-8")
        if max_chars and len(content) > max_chars:
            content = content[:max_chars] + "\n\n[... truncated ...]"
        return content
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return fallback


def main():
    if should_skip_injection():
        sys.exit(0)

    harness_dir = find_harness_dir()
    if not harness_dir:
        sys.exit(0)

    output = StringIO()
    output.write("<harness-context>\n")
    output.write("You are in a Harness-managed project. "
                 "Specs are injected by hooks — do not manually load them.\n\n")

    # 1. Inject lessons index (always, budget-limited)
    lessons_index = harness_dir / "spec" / "lessons" / "index.md"
    content = read_file(lessons_index, max_chars=MAX_LESSONS_CHARS)
    if content:
        output.write("## Project Lessons\n\n")
        output.write(content)
        output.write("\n\n")

    # 2. Inject staleness warnings
    stale_file = harness_dir / FILE_STALE
    if stale_file.is_file():
        try:
            stale = json.loads(stale_file.read_text(encoding="utf-8"))
            if stale:
                output.write("## Stale Knowledge Detected\n\n")
                for entry in stale[:MAX_STALE_WARNINGS]:
                    output.write(
                        f"- `{entry.get('file', '?')}` modified since "
                        f"`{entry.get('spec', '?')}` was last updated\n"
                    )
                output.write("\n")
        except (json.JSONDecodeError, KeyError):
            pass

    # 3. Inject current task pointer
    current_task_file = harness_dir / FILE_CURRENT_TASK
    if current_task_file.is_file():
        task_dir = current_task_file.read_text(encoding="utf-8").strip()
        if task_dir:
            output.write(f"## Active Task\n\n")
            output.write(f"Task directory: `{task_dir}`\n")
            prd_path = Path(task_dir) / "prd.md"
            if prd_path.is_file():
                output.write(f"PRD: `{prd_path}`\n")
            output.write("\n")

    output.write("</harness-context>")

    result = output.getvalue()
    if result.strip():
        json.dump({"result": result}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
