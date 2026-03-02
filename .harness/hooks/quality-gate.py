#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SubagentStop hook — quality gate enforcement.

Derived from Trellis ralph-loop.py (battle-tested quality gate).

Triggered on: SubagentStop (when any subagent finishes)
Enforces:
- Verification commands must pass (not just be mentioned)
- Failure budget tracking (≤3 same-type failures)
- Per-task state isolation (F4 feature)
- State timeout (30 min staleness reset)

Key patterns from ralph-loop:
- Run verify commands externally, don't trust agent self-report
- Per-task state file (not global — parallel safe)
- Atomic state writes (temp + rename)
- MAX_ITERATIONS safety limit
"""

# IMPORTANT: Suppress all warnings FIRST
import warnings
warnings.filterwarnings("ignore")

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
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
MAX_DEBUG_CYCLES = 3       # Failure budget (3-Failure Protocol)
MAX_ITERATIONS = 5         # Safety limit to prevent infinite loops
STATE_TIMEOUT_MINUTES = 30 # Reset state if older than this
VERIFY_TIMEOUT_SECONDS = 60  # Per-command timeout


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

    return None


def get_current_task_dir(harness_dir: str) -> str | None:
    """Read the current active task directory."""
    current_task_file = os.path.join(harness_dir, FILE_CURRENT_TASK)
    if not os.path.isfile(current_task_file):
        return None
    try:
        with open(current_task_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return content if content else None
    except (IOError, UnicodeDecodeError):
        return None


def load_task_state(task_dir: str) -> dict:
    """Load task state from task-specific state file (F4: per-task isolation)."""
    state_file = os.path.join(task_dir, ".state.json")
    if not os.path.isfile(state_file):
        return _new_state()
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)

        # Check for state timeout (stale state from abandoned session)
        last_updated = state.get("last_updated", "")
        if last_updated:
            try:
                last_dt = datetime.fromisoformat(last_updated)
                if datetime.now() - last_dt > timedelta(minutes=STATE_TIMEOUT_MINUTES):
                    return _new_state()  # Reset stale state
            except (ValueError, TypeError):
                pass

        return state
    except (json.JSONDecodeError, IOError):
        return _new_state()


def _new_state() -> dict:
    """Create a fresh state object."""
    return {
        "iteration": 0,
        "debug_count": 0,
        "completions": [],
        "last_updated": datetime.now().isoformat(),
    }


def save_task_state(task_dir: str, state: dict):
    """Save task state atomically (temp file + rename)."""
    state["last_updated"] = datetime.now().isoformat()
    state_file = os.path.join(task_dir, ".state.json")
    tmp_file = state_file + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.rename(tmp_file, state_file)
    except IOError:
        if os.path.exists(tmp_file):
            os.unlink(tmp_file)


def get_verify_commands(harness_dir: str) -> list[str]:
    """Read verification commands from workflow.md."""
    workflow_path = os.path.join(harness_dir, "workflow.md")
    if not os.path.isfile(workflow_path):
        return []

    commands = []
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("- **Test**:") or \
                   line.startswith("- **Lint**:") or \
                   line.startswith("- **Build**:"):
                    parts = line.split("`")
                    if len(parts) >= 2:
                        cmd = parts[1].strip()
                        if cmd and not cmd.startswith("_PLACEHOLDER"):
                            commands.append(cmd)
    except (IOError, UnicodeDecodeError):
        pass

    return commands


def run_verify_command(cmd: str) -> tuple[bool, str]:
    """Run a verification command and return (passed, output)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=VERIFY_TIMEOUT_SECONDS,
            cwd=os.getcwd(),
        )
        passed = result.returncode == 0
        output = result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
        if not passed:
            output += "\n" + (result.stderr[-300:] if len(result.stderr) > 300 else result.stderr)
        return passed, output.strip()
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {VERIFY_TIMEOUT_SECONDS}s"
    except (FileNotFoundError, PermissionError) as e:
        return False, f"Command error: {e}"


def detect_agent_type(hook_input: dict) -> str:
    """Detect which pipeline stage just completed."""
    # Try to get from the stop event metadata
    tool_input = hook_input.get("tool_input", {})
    agent_type = tool_input.get("subagent_type", "").lower()

    if "check" in agent_type or "review" in agent_type:
        return "check"
    if "debug" in agent_type or "fix" in agent_type:
        return "debug"
    if "implement" in agent_type:
        return "implement"
    if "finish" in agent_type:
        return "finish"

    # Fallback: scan tool output for clues
    output = hook_input.get("tool_output", "").lower()
    if "check" in output[:200] or "verify" in output[:200]:
        return "check"
    if "debug" in output[:200] or "fix" in output[:200]:
        return "debug"

    return "unknown"


def main():
    harness_dir = find_harness_dir()
    if not harness_dir:
        return

    # Read hook input
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    task_dir = get_current_task_dir(harness_dir)
    if not task_dir:
        return

    state = load_task_state(task_dir)
    agent_type = detect_agent_type(hook_input)

    # Increment iteration counter (safety limit)
    state["iteration"] = state.get("iteration", 0) + 1
    if state["iteration"] > MAX_ITERATIONS:
        warning = (
            f"\n\n## Safety Limit Reached\n\n"
            f"Max iterations ({MAX_ITERATIONS}) exceeded.\n"
            f"This is a safety limit to prevent infinite loops.\n"
            f"Please review the task state and restart if needed.\n"
        )
        json.dump({"result": warning}, sys.stdout, ensure_ascii=False)
        save_task_state(task_dir, state)
        return

    # === FAILURE BUDGET (3-Failure Protocol) ===
    if agent_type == "debug":
        state["debug_count"] = state.get("debug_count", 0) + 1
        if state["debug_count"] >= MAX_DEBUG_CYCLES:
            escalation = (
                f"\n\n## Failure Budget Exhausted\n\n"
                f"Debug cycle {state['debug_count']}/{MAX_DEBUG_CYCLES} reached.\n"
                f"**STOP** and escalate to human with structured request:\n\n"
                f"1. What was attempted (all {state['debug_count']} cycles)\n"
                f"2. What error persists\n"
                f"3. Your top 2 recommended approaches (with trade-offs)\n"
                f"4. What information you're missing\n"
                f"5. Default recommendation if human doesn't respond\n"
            )
            json.dump({"result": escalation}, sys.stdout, ensure_ascii=False)
            save_task_state(task_dir, state)
            return

    # === QUALITY GATE (verify commands) ===
    if agent_type == "check":
        verify_cmds = get_verify_commands(harness_dir)
        if verify_cmds:
            failed_cmds = []
            for cmd in verify_cmds:
                passed, output = run_verify_command(cmd)
                if not passed:
                    failed_cmds.append((cmd, output))

            if failed_cmds:
                gate_result = "\n\n## Quality Gate: Verification Failed\n\n"
                for cmd, output in failed_cmds:
                    gate_result += f"### `{cmd}` — FAILED\n\n"
                    if output:
                        gate_result += f"\n\n"
                gate_result += (
                    "Please fix the failing checks before marking the task complete.\n"
                    "If you cannot fix them, escalate with a structured request.\n"
                )
                json.dump({"result": gate_result}, sys.stdout, ensure_ascii=False)
                save_task_state(task_dir, state)
                return

    # Record completion
    state.setdefault("completions", []).append({
        "agent": agent_type,
        "timestamp": datetime.now().isoformat(),
    })

    save_task_state(task_dir, state)


if __name__ == "__main__":
    main()
