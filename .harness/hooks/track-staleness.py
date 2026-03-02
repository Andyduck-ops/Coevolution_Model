#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PostToolUse hook — detect knowledge staleness.

Derived from Trellis track-knowledge-staleness.py (~140 lines, battle-tested).

Triggered on: Edit, Write, MultiEdit tool calls
Detects: When modified files overlap with JSONL-referenced files
Writes: .harness/.stale-knowledge.json

Zero LLM calls — pure text matching.
"""

# IMPORTANT: Suppress all warnings FIRST
import warnings
warnings.filterwarnings("ignore")

import json
import os
import sys
from datetime import datetime
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
FILE_STALE = ".stale-knowledge.json"


def find_repo_root() -> str | None:
    """Find git repo root from cwd upwards."""
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return str(current)
        current = current.parent
    return None


def find_harness_dir() -> str | None:
    """Find .harness/ directory."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        candidate = os.path.join(project_dir, DIR_HARNESS)
        if os.path.isdir(candidate):
            return candidate

    candidate = os.path.join(os.getcwd(), DIR_HARNESS)
    if os.path.isdir(candidate):
        return candidate

    repo_root = find_repo_root()
    if repo_root:
        candidate = os.path.join(repo_root, DIR_HARNESS)
        if os.path.isdir(candidate):
            return candidate

    return None


def collect_jsonl_references(harness_dir: str) -> set[str]:
    """Collect all file paths referenced in JSONL and spec files."""
    refs = set()

    # Scan task JSONL files
    tasks_dir = os.path.join(harness_dir, "tasks")
    if os.path.isdir(tasks_dir):
        for task_name in os.listdir(tasks_dir):
            task_path = os.path.join(tasks_dir, task_name)
            if not os.path.isdir(task_path):
                continue
            for jsonl_name in ("implement.jsonl", "check.jsonl", "debug.jsonl", "spec.jsonl"):
                jsonl_path = os.path.join(task_path, jsonl_name)
                if not os.path.exists(jsonl_path):
                    continue
                try:
                    with open(jsonl_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            try:
                                item = json.loads(line)
                                for key in ("file", "path"):
                                    val = item.get(key, "")
                                    if val:
                                        refs.add(val)
                            except json.JSONDecodeError:
                                continue
                except (IOError, UnicodeDecodeError):
                    continue

    # Scan knowledge.jsonl
    knowledge_path = os.path.join(harness_dir, "index", "knowledge.jsonl")
    if os.path.exists(knowledge_path):
        try:
            with open(knowledge_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        val = item.get("path", "")
                        if val:
                            refs.add(val)
                    except json.JSONDecodeError:
                        continue
        except (IOError, UnicodeDecodeError):
            pass

    # Include spec .md files as implicit references
    spec_dir = os.path.join(harness_dir, "spec")
    if os.path.isdir(spec_dir):
        for root, _dirs, files in os.walk(spec_dir):
            for fname in files:
                if fname.endswith(".md"):
                    rel = os.path.relpath(os.path.join(root, fname), harness_dir)
                    refs.add(rel)

    return refs


def load_stale_entries(stale_path: str) -> list[dict]:
    """Load existing stale knowledge entries."""
    if not os.path.isfile(stale_path):
        return []
    try:
        with open(stale_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_stale_entries(stale_path: str, entries: list[dict]):
    """Save stale knowledge entries atomically (temp file + rename)."""
    tmp_file = stale_path + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        os.rename(tmp_file, stale_path)
    except IOError:
        # Clean up temp file on failure
        if os.path.exists(tmp_file):
            os.unlink(tmp_file)


def main():
    harness_dir = find_harness_dir()
    if not harness_dir:
        return

    # Read hook input
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return

    # Get modified file path
    tool_input = hook_input.get("tool_input", {})
    modified_file = tool_input.get("file_path", "")
    if not modified_file:
        return

    # Normalize to project-relative path
    repo_root = find_repo_root() or os.getcwd()
    if modified_file.startswith(repo_root):
        modified_file = os.path.relpath(modified_file, repo_root)

    # Skip modifications to .harness/ itself (self-updates, not staleness)
    if modified_file.startswith(DIR_HARNESS + "/") or modified_file.startswith(DIR_HARNESS + os.sep):
        return

    # Check if this file is referenced by any JSONL or spec
    refs = collect_jsonl_references(harness_dir)

    is_referenced = False
    matching_spec = None
    for ref in refs:
        # Direct match
        if modified_file == ref or modified_file.endswith("/" + ref):
            is_referenced = True
            matching_spec = ref
            break
        # Modified file is inside a referenced directory
        if modified_file.startswith(ref + "/"):
            is_referenced = True
            matching_spec = ref
            break
        # Basename match (looser, catches renames)
        if os.path.basename(modified_file) == os.path.basename(ref):
            is_referenced = True
            matching_spec = ref
            break

    if not is_referenced:
        return

    # Add stale entry (deduplicated)
    stale_path = os.path.join(harness_dir, FILE_STALE)
    entries = load_stale_entries(stale_path)

    existing_files = {e.get("file") for e in entries}
    if modified_file not in existing_files:
        entries.append({
            "file": modified_file,
            "spec": matching_spec,
            "detected": datetime.now().isoformat(),
        })
        save_stale_entries(stale_path, entries)


if __name__ == "__main__":
    main()
