from __future__ import annotations

import pytest

from rna_llps.models.scalar_dynamics import compute_bn, compute_variance_terms, hill_activation


def test_compute_bn_power_rule() -> None:
    value = compute_bn(delta_0=2.0, e_scale=3.0, gamma=2.0, n_order=3)
    assert value == pytest.approx(48.0)


def test_compute_bn_negative_order_raises() -> None:
    with pytest.raises(ValueError):
        compute_bn(delta_0=1.0, e_scale=1.0, gamma=1.0, n_order=-1)


def test_variance_terms_use_vx_vy(sample_params_dict: dict[str, float]) -> None:
    sample_params_dict["V_x"] = 2.0
    sample_params_dict["V_y"] = 3.0
    terms = compute_variance_terms(r=0.5, p=0.5, params=sample_params_dict)
    assert terms["sigma_x"] > 0.0
    assert terms["sigma_y"] > 0.0
    assert terms["A"] > 0.0
    assert terms["lambda"] == pytest.approx(terms["sigma_x"] + terms["sigma_y"])


def test_hill_activation_is_bounded() -> None:
    out = hill_activation(signal=2.0, b_n=1.0, n_order=2)
    assert 0.0 <= out <= 1.0
