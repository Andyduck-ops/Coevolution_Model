#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay minimal hook payloads to verify hook runtime behavior."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK_DIR = ROOT / ".harness" / "hooks"
CURRENT_TASK = ROOT / ".harness" / ".current-task"


@dataclass
class ReplayCase:
    name: str
    hook: str
    payload: dict
    expect_json: bool


def run_case(case: ReplayCase) -> tuple[bool, str]:
    hook_path = HOOK_DIR / case.hook
    if not hook_path.is_file():
        return False, f"missing hook: {hook_path}"

    proc = subprocess.run(
        ["python3", str(hook_path)],
        input=json.dumps(case.payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        cwd=str(ROOT),
    )

    if proc.returncode != 0:
        return False, f"exit={proc.returncode}, stderr={proc.stderr.strip()}"

    out = proc.stdout.strip()
    if case.expect_json:
        if not out:
            return False, "expected JSON output but got empty stdout"
        try:
            json.loads(out)
        except json.JSONDecodeError as exc:
            return False, f"invalid JSON output: {exc}"
    return True, "ok"


def main() -> None:
    task_dir = None
    if CURRENT_TASK.is_file():
        task_dir = Path(CURRENT_TASK.read_text(encoding="utf-8").strip())

    cases = [
        ReplayCase(
            name="session-start",
            hook="session-start.py",
            payload={"hook_event_name": "SessionStart", "source": "startup"},
            expect_json=True,
        ),
        ReplayCase(
            name="inject-context",
            hook="inject-context.py",
            payload={
                "hook_event_name": "PreToolUse",
                "tool_name": "spawn_agent",
                "tool_input": {
                    "agent_type": "implement",
                    "message": "run implement stage",
                },
            },
            expect_json=True,
        ),
        ReplayCase(
            name="track-staleness",
            hook="track-staleness.py",
            payload={
                "hook_event_name": "PostToolUse",
                "tool_name": "Edit",
                "tool_input": {"file_path": str(ROOT / ".harness" / "workflow.md")},
            },
            expect_json=False,
        ),
        ReplayCase(
            name="quality-gate",
            hook="quality-gate.py",
            payload={
                "hook_event_name": "SubagentStop",
                "agent_type": "implement",
                "last_assistant_message": "implement stage done",
            },
            expect_json=False,
        ),
    ]

    failures: list[str] = []
    for case in cases:
        ok, detail = run_case(case)
        if not ok:
            failures.append(f"{case.name}: {detail}")

    # Keep replay side effects minimal.
    if task_dir is not None:
        state_file = task_dir / ".state.json"
        if state_file.exists():
            state_file.unlink()

    if failures:
        print("[FAIL] hook replay failed")
        for item in failures:
            print(f"- {item}")
        raise SystemExit(1)

    print("[OK] hook replay passed")


if __name__ == "__main__":
    main()
