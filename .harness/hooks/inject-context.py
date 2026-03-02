#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreToolUse hook — inject context from JSONL into subagent tasks.

Derived from Trellis inject-subagent-context.py (820 lines, battle-tested).
Simplified to ~150 lines while preserving core patterns.

Triggered on: Task tool calls
Reads: {task_dir}/implement.jsonl, check.jsonl, debug.jsonl
Injects: File contents declared in JSONL into the agent's context

Key features from Trellis:
- UTF-8 safety (Windows compatible)
- CLAUDE_PROJECT_DIR awareness
- Repo root walking
- File path extraction from prd.md (F5 feature)
- spec.jsonl fallback
- Silent skip on missing files (defensive design)
"""

# IMPORTANT: Suppress all warnings FIRST
import warnings
warnings.filterwarnings("ignore")

import json
import os
import re
import sys
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
MAX_FILES = 20
MAX_CHARS_PER_FILE = 12000  # ~3000 tokens
AGENTS_NO_PHASE_UPDATE = {"debug", "research"}

# Agent type detection — order matters (first match wins)
AGENT_KEYWORDS = [
    (["check", "review", "verify", "qa"], "check"),
    (["debug", "fix", "bugfix"], "debug"),
    (["finish", "complete", "pr"], "finish"),
    (["research", "explore", "analyze"], "research"),
    (["implement", "code", "build", "create", "develop"], "implement"),
]


def find_harness_dir() -> Path | None:
    """Find .harness/ directory."""
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
        if (current / ".git").exists() and (current / DIR_HARNESS).is_dir():
            return current / DIR_HARNESS
        current = current.parent

    return None


def detect_agent_type(tool_input: dict) -> str:
    """Detect pipeline stage from subagent_type and prompt."""
    agent_type = tool_input.get("subagent_type", "").lower()
    prompt = tool_input.get("prompt", "").lower()
    combined = f"{agent_type} {prompt}"

    for keywords, stage in AGENT_KEYWORDS:
        for kw in keywords:
            if kw in agent_type:  # Prioritize explicit type
                return stage

    for keywords, stage in AGENT_KEYWORDS:
        for kw in keywords:
            if kw in combined:
                return stage

    return "implement"  # Default


def read_jsonl(filepath: str) -> list[dict]:
    """Read JSONL file, skip comments and invalid lines."""
    entries = []
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
    except (IOError, UnicodeDecodeError):
        pass
    return entries


def extract_file_paths_from_prd(prd_path: str) -> list[str]:
    """Extract file paths mentioned in prd.md (F5 feature from Trellis)."""
    if not os.path.isfile(prd_path):
        return []
    try:
        with open(prd_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, UnicodeDecodeError):
        return []

    # Match common path patterns: src/foo/bar.ts, ./components/X.tsx, etc.
    patterns = [
        r'`([\w./\-]+\.[a-zA-Z]{1,5})`',       # `path/to/file.ext`
        r'\b(src/[\w./\-]+\.[a-zA-Z]{1,5})\b',  # src/path/to/file.ext
        r'\b(app/[\w./\-]+\.[a-zA-Z]{1,5})\b',  # app/path/to/file.ext
        r'\b(lib/[\w./\-]+\.[a-zA-Z]{1,5})\b',  # lib/path/to/file.ext
    ]
    paths = set()
    for pattern in patterns:
        for match in re.findall(pattern, content):
            if not match.startswith("http") and os.path.isfile(match):
                paths.add(match)
    return list(paths)[:5]  # Cap at 5 auto-discovered files


def resolve_file(file_path: str, harness_dir: Path, task_dir: str | None) -> str | None:
    """Resolve file path relative to .harness/, task dir, or project root."""
    # 1. Relative to .harness/
    candidate = str(harness_dir / file_path)
    if os.path.exists(candidate):
        return candidate

    # 2. Relative to task dir
    if task_dir:
        candidate = os.path.join(task_dir, file_path)
        if os.path.exists(candidate):
            return candidate

    # 3. Absolute or project-relative
    if os.path.exists(file_path):
        return file_path

    return None  # Silent skip — defensive design


def read_file_content(filepath: str, max_chars: int = MAX_CHARS_PER_FILE) -> str | None:
    """Read file content with truncation."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(max_chars + 1)
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[... truncated ...]"
        return content
    except (IOError, UnicodeDecodeError):
        return None


def read_directory_md_files(dirpath: str, max_chars: int = MAX_CHARS_PER_FILE) -> str | None:
    """Read all .md files in a directory."""
    if not os.path.isdir(dirpath):
        return None
    contents = []
    budget_per_file = max(max_chars // 10, 2000)
    for fname in sorted(os.listdir(dirpath)):
        if fname.endswith(".md"):
            fpath = os.path.join(dirpath, fname)
            content = read_file_content(fpath, budget_per_file)
            if content:
                contents.append(f"### {fname}\n\n{content}")
    return "\n\n".join(contents) if contents else None


def main():
    harness_dir = find_harness_dir()
    if not harness_dir:
        return

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Task":
        return

    tool_input = hook_input.get("tool_input", {})

    # Get current task
    current_task_file = harness_dir / FILE_CURRENT_TASK
    if not current_task_file.is_file():
        return
    task_dir = current_task_file.read_text(encoding="utf-8").strip()
    if not task_dir:
        return

    agent_type = detect_agent_type(tool_input)

    # Determine which JSONL to read
    jsonl_path = os.path.join(task_dir, f"{agent_type}.jsonl")
    entries = read_jsonl(jsonl_path)

    # Fallback to spec.jsonl (Trellis compat)
    if not entries:
        entries = read_jsonl(os.path.join(task_dir, "spec.jsonl"))

    # F5: Auto-extract file paths from prd.md for implement stage
    if agent_type == "implement":
        prd_path = os.path.join(task_dir, "prd.md")
        auto_paths = extract_file_paths_from_prd(prd_path)
        for p in auto_paths:
            # Don't duplicate existing entries
            existing_files = {e.get("file") or e.get("path") for e in entries}
            if p not in existing_files:
                entries.append({"file": p, "reason": "auto-discovered from prd.md"})

    if not entries:
        return

    # Resolve and read files
    context_blocks = []
    files_loaded = 0

    for entry in entries[:MAX_FILES]:
        file_path = entry.get("file") or entry.get("path")
        if not file_path:
            continue

        file_type = entry.get("type", "file")
        resolved = resolve_file(file_path, harness_dir, task_dir)
        if not resolved:
            continue  # Silent skip — defensive design

        if file_type == "directory":
            content = read_directory_md_files(resolved)
        else:
            content = read_file_content(resolved)

        if content:
            reason = entry.get("reason", "")
            header = f"## [{file_path}]" + (f" — {reason}" if reason else "")
            context_blocks.append(f"{header}\n\n{content}")
            files_loaded += 1

    if context_blocks:
        result = (
            f"# Injected Context ({agent_type} stage, {files_loaded} files)\n\n"
            + "\n\n---\n\n".join(context_blocks)
        )
        json.dump({"result": result}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
