#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit workflow commands against command-permission map."""

from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".harness" / "workflow.md"
PERM_MAP = ROOT / ".harness" / "spec" / "operations" / "command-permission-map.yaml"


def extract_commands_from_workflow() -> list[str]:
    if not WORKFLOW.is_file():
        return []
    pattern = re.compile(r"`([^`]+)`")
    commands: list[str] = []
    for line in WORKFLOW.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- **"):
            m = pattern.search(line)
            if m:
                commands.append(m.group(1).strip())
    return commands


def main() -> None:
    findings: list[dict] = []
    if not PERM_MAP.is_file():
        findings.append({"severity": "error", "item": "permission-map", "detail": "missing yaml"})
        payload = {"ok": False, "type": "permission-audit", "findings": findings}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    mapping = yaml.safe_load(PERM_MAP.read_text(encoding="utf-8")) or {}
    perms: dict = mapping.get("permissions", {})
    allowed: list[str] = []
    for level, cmds in perms.items():
        if level in {"L1", "L2", "L3", "L4"} and isinstance(cmds, list):
            allowed.extend(cmds)

    commands = extract_commands_from_workflow()
    for cmd in commands:
        if not any(fnmatch.fnmatch(cmd, pat) for pat in allowed):
            findings.append(
                {
                    "severity": "error",
                    "item": "unmapped-command",
                    "detail": cmd,
                }
            )

    payload = {
        "ok": len(findings) == 0,
        "type": "permission-audit",
        "findings": findings,
        "summary": {"workflow_commands": commands},
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
