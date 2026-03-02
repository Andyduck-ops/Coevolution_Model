from __future__ import annotations

from pathlib import Path

import yaml

from rna_llps.pipeline import run_smoke


def test_run_smoke_generates_artifacts(tmp_path: Path) -> None:
    config = {
        "mu_x": 0.1,
        "mu_y": 0.1,
        "alpha": 1.0,
        "beta": 1.0,
        "kappa": 1.0,
        "K_R": 1.0,
        "K_P": 1.0,
        "V_x": 1.0,
        "V_y": 1.0,
        "gamma": 1.0,
        "delta_0": 1.0,
        "E": 1.0,
        "n": 1,
        "v_R": 1.0,
        "v_P": 1.0,
        "chi_RR": 0.0,
        "chi_PP": 0.0,
        "chi_0": 0.0,
        "epsilon": 1.0,
        "k_BT": 1.0,
    }

    config_path = tmp_path / "params.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    output_dir = tmp_path / "results"
    figure_dir = tmp_path / "figures"
    artifacts = run_smoke(
        config_path=config_path,
        output_dir=output_dir,
        figure_dir=figure_dir,
        t_end=5.0,
    )

    assert artifacts.npz_path.is_file()
    assert artifacts.figure_path.is_file()
    assert artifacts.summary_path.is_file()
