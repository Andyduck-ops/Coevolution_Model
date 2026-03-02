from __future__ import annotations

from pathlib import Path

import yaml


def test_solver_contract_has_required_sections() -> None:
    path = Path("configs/solver_contract.yaml")
    assert path.is_file()

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)

    for key in ["solver", "jacobian", "events", "stability", "acceptance"]:
        assert key in data


def test_solver_contract_primary_and_fallback_methods_are_set() -> None:
    data = yaml.safe_load(Path("configs/solver_contract.yaml").read_text(encoding="utf-8"))

    solver = data["solver"]
    assert solver["primary_method"] == "Radau"
    assert solver["fallback_method"] == "BDF"

    atol = solver["atol"]
    assert set(atol.keys()) == {"x", "y", "R", "P"}


def test_partition_coeff_uses_log_domain_contract() -> None:
    data = yaml.safe_load(Path("configs/solver_contract.yaml").read_text(encoding="utf-8"))

    partition = data["stability"]["partition_coeff"]
    assert partition["strategy"] == "log_domain"
    low, high = partition["clip_exp_argument"]
    assert low < 0 < high
