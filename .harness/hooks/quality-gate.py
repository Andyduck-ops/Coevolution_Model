#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SubagentStop hook: enforce failure budget and verification commands."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

DIR_HARNESS = ".harness"
FILE_CURRENT_TASK = ".current-task"
MAX_DEBUG_CYCLES = 3
MAX_ITERATIONS = 20
STATE_TIMEOUT_MINUTES = 30
VERIFY_TIMEOUT_SECONDS = 120


def find_harness_dir() -> Path | None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        candidate = Path(project_dir) / DIR_HARNESS
        if candidate.is_dir():
            return candidate

    candidate = Path.cwd() / DIR_HARNESS
    if candidate.is_dir():
        return candidate
    return None


def get_current_task_dir(harness_dir: Path) -> Path | None:
    marker = harness_dir / FILE_CURRENT_TASK
    if not marker.is_file():
        return None
    task_dir = marker.read_text(encoding="utf-8").strip()
    if not task_dir:
        return None
    path = Path(task_dir)
    return path if path.is_dir() else None


def new_state() -> dict:
    return {
        "iteration": 0,
        "debug_count": 0,
        "completions": [],
        "last_updated": datetime.now().isoformat(),
    }


def load_state(task_dir: Path) -> dict:
    state_file = task_dir / ".state.json"
    if not state_file.is_file():
        return new_state()
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return new_state()

    stamp = state.get("last_updated", "")
    try:
        ts = datetime.fromisoformat(stamp)
        if datetime.now() - ts > timedelta(minutes=STATE_TIMEOUT_MINUTES):
            return new_state()
    except ValueError:
        return new_state()

    return state


def save_state(task_dir: Path, state: dict) -> None:
    state["last_updated"] = datetime.now().isoformat()
    dst = task_dir / ".state.json"
    tmp = task_dir / ".state.json.tmp"
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(dst)


def get_verify_commands(harness_dir: Path) -> list[str]:
    workflow = harness_dir / "workflow.md"
    if not workflow.is_file():
        return []

    keys = (
        "- **Test**:",
        "- **Lint**:",
        "- **Build**:",
        "- **E2E Smoke**:",
        "- **Hook Replay**:",
        "- **Ops Full Check**:",
        "- **Governance Check**:",
    )
    commands: list[str] = []

    for raw in workflow.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith(keys):
            continue
        parts = line.split("`")
        if len(parts) >= 2:
            cmd = parts[1].strip()
            if cmd and not cmd.startswith("_PLACEHOLDER"):
                commands.append(cmd)
    return commands


def run_verify_command(command: str) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=VERIFY_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False, f"timeout after {VERIFY_TIMEOUT_SECONDS}s"
    except OSError as exc:
        return False, f"os error: {exc}"

    ok = proc.returncode == 0
    output = (proc.stdout + "\n" + proc.stderr).strip()
    if len(output) > 800:
        output = output[-800:]
    return ok, output


def detect_stage(hook_input: dict) -> str:
    # Codex SubagentStop payload carries flattened `agent_type`.
    agent_type = str(hook_input.get("agent_type", "")).lower()
    if not agent_type:
        tool_input = hook_input.get("tool_input", {})
        if isinstance(tool_input, dict):
            agent_type = str(tool_input.get("subagent_type", "")).lower()

    if any(k in agent_type for k in ("check", "review", "verify", "qa")):
        return "check"
    if any(k in agent_type for k in ("debug", "fix", "bugfix")):
        return "debug"
    if "finish" in agent_type:
        return "finish"
    if "implement" in agent_type:
        return "implement"

    msg = str(hook_input.get("last_assistant_message", "")).lower()
    if "verify" in msg or "check" in msg:
        return "check"
    if "debug" in msg or "fix" in msg:
        return "debug"
    return "unknown"


def deny(reason: str) -> None:
    json.dump({"decision": "deny", "reason": reason}, sys.stdout, ensure_ascii=False)


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    # Only enforce at SubagentStop event.
    if str(hook_input.get("hook_event_name", "")).lower() != "subagentstop":
        return

    harness_dir = find_harness_dir()
    if not harness_dir:
        return

    task_dir = get_current_task_dir(harness_dir)
    if not task_dir:
        return

    state = load_state(task_dir)
    stage = detect_stage(hook_input)

    state["iteration"] = int(state.get("iteration", 0)) + 1
    if state["iteration"] > MAX_ITERATIONS:
        save_state(task_dir, state)
        deny(f"Safety limit reached: iteration > {MAX_ITERATIONS}. Please review task flow.")
        return

    if stage == "debug":
        state["debug_count"] = int(state.get("debug_count", 0)) + 1
        if state["debug_count"] >= MAX_DEBUG_CYCLES:
            save_state(task_dir, state)
            deny(
                "Failure budget exhausted (debug >= 3). Escalate with A/B options and risks."
            )
            return

    if stage == "check":
        failures: list[str] = []
        for cmd in get_verify_commands(harness_dir):
            ok, output = run_verify_command(cmd)
            if not ok:
                failures.append(f"{cmd}\n{output}")

        if failures:
            save_state(task_dir, state)
            reason = "Quality gate failed.\n\n" + "\n\n---\n\n".join(failures)
            deny(reason)
            return

    state.setdefault("completions", []).append(
        {"stage": stage, "timestamp": datetime.now().isoformat()}
    )
    save_state(task_dir, state)


if __name__ == "__main__":
    main()
