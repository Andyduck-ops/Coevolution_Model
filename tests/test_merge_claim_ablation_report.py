from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)


def test_merge_report_pass(tmp_path: Path) -> None:
    claim = tmp_path / "claim.json"
    ablation = tmp_path / "ablation.json"
    repro = tmp_path / "repro.json"
    out = tmp_path / "merged.json"

    claim.write_text(json.dumps({"pass": True, "summary": {"failed": 0}}), encoding="utf-8")
    ablation.write_text(json.dumps({"pass": True, "summary": {"failed": 0}}), encoding="utf-8")
    repro.write_text(json.dumps({"passed": True, "fidelity": {"pass": True}}), encoding="utf-8")

    result = run_cmd(
        [
            ".venv/bin/python",
            "scripts/merge_claim_ablation_report.py",
            "--claim",
            str(claim),
            "--ablation",
            str(ablation),
            "--repro",
            str(repro),
            "--out",
            str(out),
            "--strict",
        ]
    )
    assert result.returncode == 0, result.stderr or result.stdout

    merged = json.loads(out.read_text(encoding="utf-8"))
    assert merged["overall_pass"] is True


def test_merge_report_fail_strict(tmp_path: Path) -> None:
    claim = tmp_path / "claim.json"
    ablation = tmp_path / "ablation.json"
    repro = tmp_path / "repro.json"
    out = tmp_path / "merged.json"

    claim.write_text(json.dumps({"pass": False, "summary": {"failed": 1}}), encoding="utf-8")
    ablation.write_text(json.dumps({"pass": True, "summary": {"failed": 0}}), encoding="utf-8")
    repro.write_text(json.dumps({"passed": True, "fidelity": {"pass": True}}), encoding="utf-8")

    result = run_cmd(
        [
            ".venv/bin/python",
            "scripts/merge_claim_ablation_report.py",
            "--claim",
            str(claim),
            "--ablation",
            str(ablation),
            "--repro",
            str(repro),
            "--out",
            str(out),
            "--strict",
        ]
    )
    assert result.returncode != 0
