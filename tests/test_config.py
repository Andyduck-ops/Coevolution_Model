from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from rna_llps.config import load_params


@pytest.fixture
def valid_params(tmp_path: Path) -> Path:
    payload = {
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
    path = tmp_path / "params.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def test_load_params_success(valid_params: Path) -> None:
    params = load_params(valid_params)
    assert params["V_x"] == pytest.approx(1.0)
    assert params["k_BT"] == pytest.approx(1.0)


def test_load_params_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_params("not_exists.yaml")


def test_load_params_missing_key_raises(valid_params: Path) -> None:
    raw = yaml.safe_load(valid_params.read_text(encoding="utf-8"))
    raw.pop("k_BT")
    valid_params.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(KeyError):
        load_params(valid_params)
