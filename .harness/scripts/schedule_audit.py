#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit pipeline contract and task artifacts for stage dependency integrity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CURRENT_TASK = ROOT / ".harness" / ".current-task"
CONTRACT_PATH = ROOT / ".harness" / "spec" / "operations" / "pipeline-contract.yaml"


def load_current_task() -> Path | None:
    if not CURRENT_TASK.is_file():
        return None
    raw = CURRENT_TASK.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_dir() else None


def check_artifact(task_dir: Path, artifact: dict[str, Any]) -> tuple[bool, str]:
    rel = artifact["path"]
    min_chars = int(artifact.get("min_chars", 1))
    p = task_dir / rel
    if not p.is_file():
        return False, f"missing: {rel}"
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return False, f"unreadable: {rel}"
    if len(text.strip()) < min_chars:
        return False, f"too short (<{min_chars} chars): {rel}"
    return True, "ok"


def run(task_dir: Path, contract_path: Path = CONTRACT_PATH) -> dict[str, Any]:
    if not contract_path.is_file():
        return {
            "ok": False,
            "type": "schedule-audit",
            "findings": [{"severity": "error", "item": "pipeline-contract", "detail": "missing file"}],
        }

    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    stages = contract.get("stages", [])
    findings: list[dict[str, Any]] = []
    stage_pass: dict[str, bool] = {}
    stage_ids: list[str] = []

    if not isinstance(stages, list) or not stages:
        findings.append(
            {
                "severity": "error",
                "item": "pipeline-contract",
                "detail": "stages must be a non-empty list",
            }
        )
        return {
            "ok": False,
            "type": "schedule-audit",
            "findings": findings,
            "summary": {"errors": 1, "warnings": 0, "stages": {}},
        }

    for stage in stages:
        sid = stage.get("id")
        if sid:
            stage_ids.append(str(sid))

    for stage in stages:
        sid = stage.get("id")
        if not sid:
            continue
        requires = stage.get("requires", [])
        for dep in requires:
            if dep not in stage_ids:
                findings.append(
                    {
                        "severity": "error",
                        "item": f"stage-dependency:{sid}",
                        "detail": f"unknown dependency: {dep}",
                    }
                )

    for stage in stages:
        sid = stage.get("id")
        if not sid:
            continue
        optional = bool(stage.get("optional", False))
        requires = stage.get("requires", [])

        for dep in requires:
            if dep in stage_pass and not stage_pass[dep]:
                findings.append(
                    {
                        "severity": "error",
                        "item": f"stage-dependency:{sid}",
                        "detail": f"dependency not satisfied: {dep}",
                    }
                )

        artifacts = stage.get("required_artifacts", [])
        checks: list[bool] = []
        for artifact in artifacts:
            ok, detail = check_artifact(task_dir, artifact)
            checks.append(ok)
            if not ok:
                sev = "warn" if optional else "error"
                findings.append(
                    {
                        "severity": sev,
                        "item": f"artifact:{sid}",
                        "detail": detail,
                    }
                )

        if not artifacts:
            stage_pass[sid] = True
        elif optional:
            stage_pass[sid] = all(checks) or not any(checks)
        else:
            stage_pass[sid] = all(checks)

    parallel_groups = contract.get("parallel_groups", [])
    if not isinstance(parallel_groups, list):
        findings.append(
            {
                "severity": "error",
                "item": "parallel-groups",
                "detail": "parallel_groups must be a list",
            }
        )
    else:
        for idx, group in enumerate(parallel_groups):
            name = str(group.get("name", "")).strip()
            members = group.get("members", [])
            if not name:
                findings.append(
                    {
                        "severity": "error",
                        "item": "parallel-group-name",
                        "detail": f"group#{idx} missing name",
                    }
                )
            if not isinstance(members, list) or not members or not all(str(m).strip() for m in members):
                findings.append(
                    {
                        "severity": "error",
                        "item": "parallel-group-members",
                        "detail": f"group:{name or idx} members must be non-empty list[str]",
                    }
                )

    stop_conditions = contract.get("stop_conditions", [])
    if not isinstance(stop_conditions, list) or not stop_conditions:
        findings.append(
            {
                "severity": "error",
                "item": "stop-conditions",
                "detail": "stop_conditions must be a non-empty list",
            }
        )
    else:
        for idx, cond in enumerate(stop_conditions):
            cid = str(cond.get("id", "")).strip()
            rule = str(cond.get("rule", "")).strip()
            if not cid:
                findings.append(
                    {
                        "severity": "error",
                        "item": "stop-condition-id",
                        "detail": f"condition#{idx} missing id",
                    }
                )
            if not rule:
                findings.append(
                    {
                        "severity": "error",
                        "item": "stop-condition-rule",
                        "detail": f"condition:{cid or idx} missing rule",
                    }
                )

    errors = [f for f in findings if f["severity"] == "error"]
    return {
        "ok": len(errors) == 0,
        "type": "schedule-audit",
        "findings": findings,
        "summary": {
            "errors": len(errors),
            "warnings": len([f for f in findings if f["severity"] == "warn"]),
            "stages": stage_pass,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Schedule audit")
    parser.add_argument("--task-dir", default="", help="Task directory path")
    args = parser.parse_args()

    task_dir = Path(args.task_dir) if args.task_dir else load_current_task()
    if task_dir is None:
        payload = {
            "ok": False,
            "type": "schedule-audit",
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
