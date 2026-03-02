#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit review artifacts and reviewer independence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURRENT_TASK = ROOT / ".harness" / ".current-task"

REQUIRED_CHECK_MARKERS = [
    "- [x] lint",
    "- [x] test",
    "- [x] build",
    "- [x] e2e",
    "- [x] hook replay",
    "- [x] ops full-check",
]


def load_current_task() -> Path | None:
    if not CURRENT_TASK.is_file():
        return None
    raw = CURRENT_TASK.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    p = Path(raw)
    return p if p.is_dir() else None


def run(task_dir: Path) -> dict:
    findings: list[dict] = []
    expected_agents: dict = {}

    task_meta_file = task_dir / "task.json"
    if not task_meta_file.is_file():
        findings.append({"severity": "error", "item": "task-meta", "detail": "missing task.json"})
    else:
        try:
            task_meta = json.loads(task_meta_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            task_meta = {}
            findings.append({"severity": "error", "item": "task-meta", "detail": "invalid task.json"})
        expected_agents = task_meta.get("agents", {})
        if not isinstance(expected_agents, dict):
            findings.append({"severity": "error", "item": "task-agents", "detail": "task.json.agents must be object"})
            expected_agents = {}
        for key in ["implementer", "reviewer"]:
            if not str(expected_agents.get(key, "")).strip():
                findings.append({"severity": "error", "item": "task-agents-field", "detail": f"missing: agents.{key}"})
        if expected_agents.get("implementer") == expected_agents.get("reviewer"):
            findings.append(
                {
                    "severity": "error",
                    "item": "task-agents-independence",
                    "detail": "task.json agents implementer/reviewer must be different",
                }
            )

    check_result = task_dir / "agent-outputs" / "check-result.md"
    if not check_result.is_file():
        findings.append({"severity": "error", "item": "check-result", "detail": "missing file"})
    else:
        text = check_result.read_text(encoding="utf-8")
        for marker in REQUIRED_CHECK_MARKERS:
            if marker not in text:
                findings.append(
                    {"severity": "error", "item": "check-result-marker", "detail": f"missing: {marker}"}
                )
        if "- [x] 通过" not in text:
            findings.append(
                {
                    "severity": "error",
                    "item": "check-result-status",
                    "detail": "review result not marked as pass",
                }
            )

    review_meta = task_dir / "evidence" / "review_meta.json"
    if not review_meta.is_file():
        findings.append(
            {"severity": "error", "item": "review-meta", "detail": "missing evidence/review_meta.json"}
        )
    else:
        meta = json.loads(review_meta.read_text(encoding="utf-8"))
        for key in ["implementer", "reviewer", "review_scope", "review_time_utc"]:
            if not meta.get(key):
                findings.append(
                    {"severity": "error", "item": "review-meta-field", "detail": f"missing: {key}"}
                )
        if meta.get("implementer") == meta.get("reviewer"):
            findings.append(
                {
                    "severity": "error",
                    "item": "review-independence",
                    "detail": "implementer and reviewer must be different",
                }
            )
        if expected_agents:
            if meta.get("implementer") != expected_agents.get("implementer"):
                findings.append(
                    {
                        "severity": "error",
                        "item": "review-agent-binding",
                        "detail": "review_meta implementer != task.json agents.implementer",
                    }
                )
            if meta.get("reviewer") != expected_agents.get("reviewer"):
                findings.append(
                    {
                        "severity": "error",
                        "item": "review-agent-binding",
                        "detail": "review_meta reviewer != task.json agents.reviewer",
                    }
                )

    spec_report = task_dir / "evidence" / "spec_audit_report.json"
    if spec_report.is_file():
        spec_data = json.loads(spec_report.read_text(encoding="utf-8"))
        if not spec_data.get("ok", False):
            findings.append(
                {
                    "severity": "error",
                    "item": "spec-audit-blocking",
                    "detail": "spec audit not passing while review marked pass",
                }
            )

    errors = [f for f in findings if f["severity"] == "error"]
    return {
        "ok": len(errors) == 0,
        "type": "review-audit",
        "findings": findings,
        "summary": {
            "errors": len(errors),
            "warnings": len([f for f in findings if f["severity"] == "warn"]),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Review audit")
    parser.add_argument("--task-dir", default="", help="Task directory")
    args = parser.parse_args()

    task_dir = Path(args.task_dir) if args.task_dir else load_current_task()
    if task_dir is None:
        payload = {
            "ok": False,
            "type": "review-audit",
            "findings": [{"severity": "error", "item": "task-dir", "detail": "missing current task"}],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    payload = run(task_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
