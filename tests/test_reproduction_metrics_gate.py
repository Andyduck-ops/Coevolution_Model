from __future__ import annotations

import json
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["fig1_stability", "fig2_timecourse", "fig3_spinodal", "fig4_post_segregation"]


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)


def write_png(path: Path, seed: int) -> None:
    rng = np.random.default_rng(seed)
    img = rng.random((64, 64))
    plt.imsave(path, img, cmap="viridis")


def prepare_generated_figures(fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    for i, stem in enumerate(REQUIRED):
        write_png(fig_dir / f"{stem}.png", seed=i + 7)
        (fig_dir / f"{stem}.pdf").write_text("placeholder", encoding="utf-8")


def write_metrics_config(path: Path) -> None:
    payload = {
        "required_figures": REQUIRED,
        "reference_mapping": {
            "fig1_stability": "fig1.png",
            "fig2_timecourse": "fig2.png",
            "fig3_spinodal": "fig3.png",
            "fig4_post_segregation": "fig4.png",
        },
        "fidelity": {"composite_threshold": 0.70},
    }
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_completeness_strict_passes_without_fidelity(tmp_path: Path) -> None:
    fig_dir = tmp_path / "figs"
    out_report = tmp_path / "repro_report.json"
    config = tmp_path / "metrics.yaml"

    prepare_generated_figures(fig_dir)
    write_metrics_config(config)

    result = run_cmd(
        [
            ".venv/bin/python",
            "scripts/check_reproduction_metrics.py",
            "--fig-dir",
            str(fig_dir),
            "--out",
            str(out_report),
            "--metrics-config",
            str(config),
            "--strict",
        ]
    )
    assert result.returncode == 0, result.stderr or result.stdout

    report = json.loads(out_report.read_text(encoding="utf-8"))
    assert report["passed"] is True


def test_require_fidelity_passes_for_identical_references(tmp_path: Path) -> None:
    fig_dir = tmp_path / "figs"
    ref_dir = tmp_path / "refs"
    out_report = tmp_path / "repro_report.json"
    config = tmp_path / "metrics.yaml"

    prepare_generated_figures(fig_dir)
    ref_dir.mkdir(parents=True, exist_ok=True)
    write_metrics_config(config)

    mapping = {
        "fig1_stability": "fig1.png",
        "fig2_timecourse": "fig2.png",
        "fig3_spinodal": "fig3.png",
        "fig4_post_segregation": "fig4.png",
    }
    for stem, ref_name in mapping.items():
        source = fig_dir / f"{stem}.png"
        (ref_dir / ref_name).write_bytes(source.read_bytes())

    result = run_cmd(
        [
            ".venv/bin/python",
            "scripts/check_reproduction_metrics.py",
            "--fig-dir",
            str(fig_dir),
            "--out",
            str(out_report),
            "--metrics-config",
            str(config),
            "--reference-dir",
            str(ref_dir),
            "--strict",
            "--require-fidelity",
        ]
    )
    assert result.returncode == 0, result.stderr or result.stdout

    report = json.loads(out_report.read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["fidelity"]["pass"] is True


def test_require_fidelity_fails_when_reference_missing(tmp_path: Path) -> None:
    fig_dir = tmp_path / "figs"
    ref_dir = tmp_path / "refs"
    out_report = tmp_path / "repro_report.json"
    config = tmp_path / "metrics.yaml"

    prepare_generated_figures(fig_dir)
    ref_dir.mkdir(parents=True, exist_ok=True)
    write_metrics_config(config)

    result = run_cmd(
        [
            ".venv/bin/python",
            "scripts/check_reproduction_metrics.py",
            "--fig-dir",
            str(fig_dir),
            "--out",
            str(out_report),
            "--metrics-config",
            str(config),
            "--reference-dir",
            str(ref_dir),
            "--strict",
            "--require-fidelity",
        ]
    )
    assert result.returncode != 0
