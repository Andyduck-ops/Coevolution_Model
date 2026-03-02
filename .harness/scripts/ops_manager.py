#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Harness ops manager: health checks + spec audit."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / ".harness"
CURRENT_TASK_FILE = HARNESS_DIR / ".current-task"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    severity: str = "error"


def _load_current_task() -> Path | None:
    if not CURRENT_TASK_FILE.is_file():
        return None
    path = CURRENT_TASK_FILE.read_text(encoding="utf-8").strip()
    if not path:
        return None
    p = Path(path)
    return p if p.exists() else None


def _write_report(task_dir: Path | None, filename: str, data: dict[str, Any]) -> None:
    if not task_dir:
        return
    evidence_dir = task_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / filename).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_health() -> tuple[bool, dict[str, Any]]:
    checks: list[CheckResult] = []

    checks.append(
        CheckResult(
            name="hooks-config-codex",
            ok=(ROOT / ".codex" / "config.toml").is_file(),
            detail=".codex/config.toml must exist for codex hook runtime",
        )
    )

    for name in [
        "session-start.py",
        "inject-context.py",
        "track-staleness.py",
        "quality-gate.py",
    ]:
        checks.append(
            CheckResult(
                name=f"hook-file:{name}",
                ok=(HARNESS_DIR / "hooks" / name).is_file(),
                detail=f".harness/hooks/{name}",
            )
        )

    task_dir = _load_current_task()
    checks.append(
        CheckResult(
            name="current-task",
            ok=task_dir is not None,
            detail=".harness/.current-task should point to active task directory",
        )
    )

    checks.append(
        CheckResult(
            name="venv-python",
            ok=(ROOT / ".venv" / "bin" / "python").is_file(),
            detail=".venv/bin/python is required for local ops pipeline",
        )
    )

    workflow = HARNESS_DIR / "workflow.md"
    verify_count = 0
    if workflow.is_file():
        text = workflow.read_text(encoding="utf-8")
        for key in ["- **Test**:", "- **Lint**:", "- **Build**:", "- **E2E Smoke**:"]:
            if key in text:
                verify_count += 1
    checks.append(
        CheckResult(
            name="workflow-verify-commands",
            ok=verify_count >= 4,
            detail=f"detected {verify_count}/4 verification commands",
        )
    )

    ok = all(item.ok for item in checks)
    payload = {
        "ok": ok,
        "type": "health",
        "checks": [item.__dict__ for item in checks],
    }
    _write_report(task_dir, "ops_health_report.json", payload)
    return ok, payload


def _contains_all(text: str, items: list[str]) -> list[str]:
    missing = []
    for item in items:
        if item not in text:
            missing.append(item)
    return missing


def run_spec_audit() -> tuple[bool, dict[str, Any]]:
    task_dir = _load_current_task()
    findings: list[dict[str, Any]] = []

    eq_file = ROOT / ".trellis/spec/guides/equations-reference.md"
    tech_file = ROOT / ".trellis/spec/backend/tech-stack.md"
    num_file = ROOT / ".trellis/spec/backend/numerical-computing.md"
    viz_file = ROOT / ".trellis/spec/backend/visualization.md"

    if not eq_file.is_file():
        findings.append({"severity": "error", "item": "equations-reference", "missing": "file"})
    else:
        eq_text = eq_file.read_text(encoding="utf-8")
        required = [
            "V_x",
            "V_y",
            "v_R",
            "v_P",
            "chi_RR",
            "chi_PP",
            "chi_0",
            "epsilon",
            "k_BT",
            "Θ_R",
            "W^I",
            "W^II",
            "P_eff",
            "A_eff",
            "X_loc",
            "B_n",
            "Π_P",
        ]
        missing = _contains_all(eq_text, required)
        if missing:
            findings.append(
                {
                    "severity": "error",
                    "item": "equations-reference-p0-p1",
                    "missing": missing,
                }
            )

    if not tech_file.is_file():
        findings.append({"severity": "error", "item": "tech-stack", "missing": "file"})
    else:
        txt = tech_file.read_text(encoding="utf-8")
        pinned = ["numpy>=", "scipy>=", "matplotlib>=", "pyyaml>=", "tqdm>="]
        missing = [p for p in pinned if p not in txt]
        if missing:
            findings.append(
                {"severity": "error", "item": "dependency-pinning", "missing": missing}
            )

    if num_file.is_file():
        txt = num_file.read_text(encoding="utf-8")
        for marker in ["Jacobian", "atol", "事件"]:
            if marker not in txt:
                findings.append(
                    {
                        "severity": "warn",
                        "item": "numerical-computing-detail",
                        "missing": marker,
                    }
                )
    else:
        findings.append({"severity": "error", "item": "numerical-computing", "missing": "file"})

    if viz_file.is_file():
        txt = viz_file.read_text(encoding="utf-8")
        wrappers = [
            "solve_full_ode()",
            "critical_stress()",
            "compute_spinodal()",
            "solve_post_segregation()",
        ]
        missing = _contains_all(txt, wrappers)
        if missing:
            findings.append(
                {"severity": "warn", "item": "figure-wrapper-functions", "missing": missing}
            )
    else:
        findings.append({"severity": "error", "item": "visualization", "missing": "file"})

    errors = [f for f in findings if f["severity"] == "error"]
    ok = len(errors) == 0
    payload = {
        "ok": ok,
        "type": "spec-audit",
        "findings": findings,
        "summary": {
            "errors": len(errors),
            "warnings": len([f for f in findings if f["severity"] == "warn"]),
        },
    }

    _write_report(task_dir, "spec_audit_report.json", payload)
    return ok, payload


def print_pretty(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Harness ops manager")
    parser.add_argument("command", choices=["health", "spec-audit", "full-check"])
    parser.add_argument("--strict", action="store_true", help="Non-zero exit when check fails")
    args = parser.parse_args()

    if args.command == "health":
        ok, payload = run_health()
        print_pretty(payload)
        if args.strict and not ok:
            raise SystemExit(1)
        return

    if args.command == "spec-audit":
        ok, payload = run_spec_audit()
        print_pretty(payload)
        if args.strict and not ok:
            raise SystemExit(1)
        return

    health_ok, health_payload = run_health()
    audit_ok, audit_payload = run_spec_audit()
    payload = {
        "ok": health_ok and audit_ok,
        "type": "full-check",
        "health": health_payload,
        "spec_audit": audit_payload,
    }
    print_pretty(payload)
    if args.strict and not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
