#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate on stale knowledge records."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STALE_FILE = ROOT / ".harness" / ".stale-knowledge.json"


def main() -> None:
    findings: list[dict] = []
    if STALE_FILE.is_file():
        try:
            stale = json.loads(STALE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            stale = [{"file": "invalid-json"}]
        if stale:
            findings.append(
                {
                    "severity": "error",
                    "item": "stale-knowledge",
                    "detail": f"{len(stale)} stale entries detected",
                    "entries": stale,
                }
            )

    payload = {
        "ok": len(findings) == 0,
        "type": "stale-gate",
        "findings": findings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
