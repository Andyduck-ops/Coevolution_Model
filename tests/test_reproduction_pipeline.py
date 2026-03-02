from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)


def test_figure_scripts_and_repro_check(
    tmp_path: Path,
    sample_params_dict: dict[str, float],
) -> None:
    config_path = tmp_path / "params.yaml"
    config_path.write_text(yaml.safe_dump(sample_params_dict), encoding="utf-8")

    fig_dir = tmp_path / "paper_figs"
    out_report = tmp_path / "repro_report.json"

    commands = [
        [
            ".venv/bin/python",
            "scripts/fig1_stability.py",
            "--config",
            str(config_path),
            "--out",
            str(fig_dir),
        ],
        [
            ".venv/bin/python",
            "scripts/fig2_timecourse.py",
            "--config",
            str(config_path),
            "--out",
            str(fig_dir),
            "--t-end",
            "5",
        ],
        [
            ".venv/bin/python",
            "scripts/fig3_spinodal.py",
            "--config",
            str(config_path),
            "--out",
            str(fig_dir),
        ],
        [
            ".venv/bin/python",
            "scripts/fig4_post_segregation.py",
            "--config",
            str(config_path),
            "--out",
            str(fig_dir),
            "--t-end",
            "5",
        ],
        [
            ".venv/bin/python",
            "scripts/check_reproduction_metrics.py",
            "--fig-dir",
            str(fig_dir),
            "--out",
            str(out_report),
            "--strict",
        ],
    ]

    for cmd in commands:
        result = run_cmd(cmd)
        assert result.returncode == 0, result.stderr or result.stdout

    report = json.loads(out_report.read_text(encoding="utf-8"))
    assert report["passed"] is True
