#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local task watcher with action-state output (adapted from babysit-pr style)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURRENT_TASK = ROOT / ".harness" / ".current-task"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_task_dir(raw: str | None) -> Path:
    if raw:
        return Path(raw)
    if CURRENT_TASK.is_file():
        return Path(CURRENT_TASK.read_text(encoding="utf-8").strip())
    raise FileNotFoundError("No task dir provided and .harness/.current-task missing")


def load_json(path: Path, default: dict | list):
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def build_snapshot(task_dir: Path) -> dict:
    evidence = task_dir / "evidence"
    outputs = task_dir / "agent-outputs"

    spec = load_json(evidence / "spec_audit_report.json", {"ok": False})
    health = load_json(evidence / "ops_health_report.json", {"ok": False})
    review = load_json(evidence / "review_audit_report.json", {"ok": False})
    schedule = load_json(evidence / "schedule_audit_report.json", {"ok": False})

    check_result = outputs / "check-result.md"
    check_pass = False
    if check_result.is_file():
        text = check_result.read_text(encoding="utf-8")
        check_pass = "- [x] 通过" in text

    snapshot = {
        "task_dir": str(task_dir),
        "time_utc": now_iso(),
        "health_ok": bool(health.get("ok", False)),
        "spec_ok": bool(spec.get("ok", False)),
        "review_ok": bool(review.get("ok", False)),
        "schedule_ok": bool(schedule.get("ok", False)),
        "check_pass": check_pass,
    }

    actions: list[str] = []
    if not snapshot["health_ok"]:
        actions.append("run_health")
    if not snapshot["spec_ok"]:
        actions.append("run_spec_audit")
    if not snapshot["schedule_ok"]:
        actions.append("run_schedule_audit")
    if not snapshot["review_ok"]:
        actions.append("run_review_audit")

    if all(snapshot[k] for k in ["health_ok", "spec_ok", "schedule_ok", "review_ok", "check_pass"]):
        actions.append("stop_ready")
    else:
        actions.append("continue_watch")

    ok = all(snapshot[k] for k in ["health_ok", "spec_ok", "schedule_ok", "review_ok", "check_pass"])
    findings: list[dict] = []
    if not ok:
        for key, item in [
            ("health_ok", "health"),
            ("spec_ok", "spec-audit"),
            ("schedule_ok", "schedule-audit"),
            ("review_ok", "review-audit"),
            ("check_pass", "check-result"),
        ]:
            if not snapshot[key]:
                findings.append({"severity": "error", "item": item, "detail": "not-ready"})

    return {
        "ok": ok,
        "type": "agent-audit",
        "snapshot": snapshot,
        "actions": actions,
        "findings": findings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Task watcher")
    parser.add_argument("--task-dir", default="", help="task directory")
    args = parser.parse_args()

    task_dir = load_task_dir(args.task_dir or None)
    payload = build_snapshot(task_dir)
    state_file = task_dir / ".watch_state.json"
    state_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
