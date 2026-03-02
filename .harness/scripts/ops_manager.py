#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Harness ops manager: health/spec plus governance audits."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / ".harness"
CURRENT_TASK_FILE = HARNESS_DIR / ".current-task"
SCRIPTS_DIR = HARNESS_DIR / "scripts"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    severity: str = "error"


def _load_current_task() -> Path | None:
    if not CURRENT_TASK_FILE.is_file():
        return None
    raw = CURRENT_TASK_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    p = Path(raw)
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


def _contains_all(text: str, items: list[str]) -> list[str]:
    return [item for item in items if item not in text]


def run_health() -> tuple[bool, dict[str, Any]]:
    checks: list[CheckResult] = []

    checks.append(
        CheckResult(
            name="hooks-config-codex",
            ok=(ROOT / ".codex" / "config.toml").is_file(),
            detail=".codex/config.toml must exist for codex hook runtime",
        )
    )

    for name in ["session-start.py", "inject-context.py", "track-staleness.py", "quality-gate.py"]:
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
        expected_keys = [
            "- **Test**:",
            "- **Lint**:",
            "- **Build**:",
            "- **E2E Smoke**:",
            "- **Hook Replay**:",
            "- **Ops Full Check**:",
            "- **Governance Check**:",
        ]
        for key in expected_keys:
            if key in text:
                verify_count += 1
    checks.append(
        CheckResult(
            name="workflow-verify-commands",
            ok=verify_count >= 7,
            detail=f"detected {verify_count}/7 verification commands",
        )
    )

    ok = all(item.ok for item in checks)
    payload = {"ok": ok, "type": "health", "checks": [item.__dict__ for item in checks]}
    _write_report(task_dir, "ops_health_report.json", payload)
    return ok, payload


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
            findings.append({"severity": "error", "item": "equations-reference-p0-p1", "missing": missing})

    if not tech_file.is_file():
        findings.append({"severity": "error", "item": "tech-stack", "missing": "file"})
    else:
        txt = tech_file.read_text(encoding="utf-8")
        pinned = ["numpy>=", "scipy>=", "matplotlib>=", "pyyaml>=", "tqdm>="]
        missing = [p for p in pinned if p not in txt]
        if missing:
            findings.append({"severity": "error", "item": "dependency-pinning", "missing": missing})

    if num_file.is_file():
        txt = num_file.read_text(encoding="utf-8")
        for marker in ["Jacobian", "atol", "事件"]:
            if marker not in txt:
                findings.append({"severity": "warn", "item": "numerical-computing-detail", "missing": marker})
    else:
        findings.append({"severity": "error", "item": "numerical-computing", "missing": "file"})

    if viz_file.is_file():
        txt = viz_file.read_text(encoding="utf-8")
        wrappers = ["solve_full_ode()", "critical_stress()", "compute_spinodal()", "solve_post_segregation()"]
        missing = _contains_all(txt, wrappers)
        if missing:
            findings.append({"severity": "warn", "item": "figure-wrapper-functions", "missing": missing})
    else:
        findings.append({"severity": "error", "item": "visualization", "missing": "file"})

    errors = [f for f in findings if f["severity"] == "error"]
    payload = {
        "ok": len(errors) == 0,
        "type": "spec-audit",
        "findings": findings,
        "summary": {"errors": len(errors), "warnings": len([f for f in findings if f["severity"] == "warn"])}
    }
    _write_report(task_dir, "spec_audit_report.json", payload)
    return payload["ok"], payload


def _run_json_script(script_name: str, task_dir: Path | None, report_name: str) -> tuple[bool, dict[str, Any]]:
    script = SCRIPTS_DIR / script_name
    if not script.is_file():
        payload = {
            "ok": False,
            "type": script_name.replace(".py", ""),
            "findings": [{"severity": "error", "item": "script", "detail": f"missing {script_name}"}],
        }
        return False, payload

    cmd = [str((ROOT / ".venv" / "bin" / "python").resolve() if (ROOT / ".venv" / "bin" / "python").is_file() else Path(sys.executable)), str(script)]
    if task_dir and script_name in {"schedule_audit.py", "review_audit.py", "task_watch.py"}:
        cmd += ["--task-dir", str(task_dir)]

    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    try:
        payload = json.loads(proc.stdout.strip() or "{}")
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "type": script_name.replace(".py", ""),
            "findings": [{"severity": "error", "item": "stdout-json", "detail": proc.stdout[-500:]}],
        }

    ok = bool(payload.get("ok", False)) and proc.returncode == 0
    if not payload.get("ok", False):
        ok = False

    if task_dir:
        _write_report(task_dir, report_name, payload)

    return ok, payload


def print_pretty(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Harness ops manager")
    parser.add_argument(
        "command",
        choices=[
            "health",
            "spec-audit",
            "schedule-audit",
            "review-audit",
            "stale-gate",
            "permission-audit",
            "agent-audit",
            "full-check",
            "governance-check",
        ],
    )
    parser.add_argument("--strict", action="store_true", help="Non-zero exit when check fails")
    args = parser.parse_args()

    task_dir = _load_current_task()

    if args.command == "health":
        ok, payload = run_health()
    elif args.command == "spec-audit":
        ok, payload = run_spec_audit()
    elif args.command == "schedule-audit":
        ok, payload = _run_json_script("schedule_audit.py", task_dir, "schedule_audit_report.json")
    elif args.command == "review-audit":
        ok, payload = _run_json_script("review_audit.py", task_dir, "review_audit_report.json")
    elif args.command == "stale-gate":
        ok, payload = _run_json_script("stale_gate.py", task_dir, "stale_gate_report.json")
    elif args.command == "permission-audit":
        ok, payload = _run_json_script("permission_audit.py", task_dir, "permission_audit_report.json")
    elif args.command == "agent-audit":
        ok, payload = _run_json_script("task_watch.py", task_dir, "agent_watch_report.json")
    elif args.command == "full-check":
        h_ok, h = run_health()
        s_ok, s = run_spec_audit()
        payload = {"ok": h_ok and s_ok, "type": "full-check", "health": h, "spec_audit": s}
        ok = payload["ok"]
    else:
        h_ok, h = run_health()
        s_ok, s = run_spec_audit()
        sc_ok, sc = _run_json_script("schedule_audit.py", task_dir, "schedule_audit_report.json")
        rv_ok, rv = _run_json_script("review_audit.py", task_dir, "review_audit_report.json")
        st_ok, st = _run_json_script("stale_gate.py", task_dir, "stale_gate_report.json")
        pm_ok, pm = _run_json_script("permission_audit.py", task_dir, "permission_audit_report.json")
        ag_ok, ag = _run_json_script("task_watch.py", task_dir, "agent_watch_report.json")
        payload = {
            "ok": all([h_ok, s_ok, sc_ok, rv_ok, st_ok, pm_ok, ag_ok]),
            "type": "governance-check",
            "health": h,
            "spec_audit": s,
            "schedule_audit": sc,
            "review_audit": rv,
            "stale_gate": st,
            "permission_audit": pm,
            "agent_audit": ag,
        }
        ok = payload["ok"]

    print_pretty(payload)
    if args.strict and not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
