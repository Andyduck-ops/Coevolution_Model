from __future__ import annotations

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def sample_params_dict() -> dict[str, float]:
    return {
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
        "n": 2.0,
        "v_R": 1.0,
        "v_P": 1.0,
        "chi_RR": 0.8,
        "chi_PP": 0.6,
        "chi_0": 0.1,
        "epsilon": 1.0,
        "k_BT": 1.0,
    }


@pytest.fixture
def sample_params_file(tmp_path: Path, sample_params_dict: dict[str, float]) -> Path:
    path = tmp_path / "params.yaml"
    path.write_text(yaml.safe_dump(sample_params_dict), encoding="utf-8")
    return path
