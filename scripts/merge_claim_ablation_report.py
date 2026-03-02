#!/usr/bin/env python3
"""Merge claim + ablation + figure-fidelity reports into one validation report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"pass": False, "missing": True, "path": str(path)}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"pass": False, "invalid_json": True, "path": str(path)}
    if not isinstance(payload, dict):
        return {"pass": False, "invalid_type": True, "path": str(path)}
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge paper validation reports")
    parser.add_argument("--claim", default="results/repro/claim_report.json")
    parser.add_argument("--ablation", default="results/repro/ablation_report.json")
    parser.add_argument("--repro", default="results/repro/repro_report.json")
    parser.add_argument("--out", default="results/repro/paper_validation_report.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    claim = load_json(Path(args.claim))
    ablation = load_json(Path(args.ablation))
    repro = load_json(Path(args.repro))

    gates = {
        "claim_gate": bool(claim.get("pass", False)),
        "ablation_gate": bool(ablation.get("pass", False)),
        "repro_gate": bool(repro.get("passed", False) or repro.get("pass", False)),
    }
    overall_pass = all(gates.values())

    failed_gates = [name for name, passed in gates.items() if not passed]

    report = {
        "type": "paper-validation-report",
        "checked_at_utc": utc_now_iso(),
        "gates": gates,
        "overall_pass": overall_pass,
        "failed_gates": failed_gates,
        "claim_summary": claim.get("summary", {}),
        "ablation_summary": ablation.get("summary", {}),
        "repro_summary": {
            "passed": bool(repro.get("passed", False) or repro.get("pass", False)),
            "fidelity": repro.get("fidelity", {}),
        },
        "inputs": {
            "claim": args.claim,
            "ablation": args.ablation,
            "repro": args.repro,
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict and not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
