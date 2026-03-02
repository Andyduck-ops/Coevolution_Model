from __future__ import annotations

import math

import pytest

from rna_llps.thermo.flory_huggins import (
    chi_critical,
    chi_rp_eff,
    partition_coeff_logsafe,
    two_phase_auxiliary_chain,
)


def test_partition_coeff_logsafe_clips_large_exponent() -> None:
    value = partition_coeff_logsafe(
        x_bar=1e6,
        y_bar=1e6,
        epsilon=1.0,
        k_bt=1.0,
        clip_min=-10.0,
        clip_max=10.0,
    )
    assert value == pytest.approx(math.exp(10.0))


def test_partition_coeff_requires_positive_kbt() -> None:
    with pytest.raises(ValueError):
        partition_coeff_logsafe(x_bar=1.0, y_bar=1.0, epsilon=1.0, k_bt=0.0)


def test_chi_effective_and_critical(sample_params_dict: dict[str, float]) -> None:
    chi_eff = chi_rp_eff(0.4, 0.3, sample_params_dict)
    chi_c = chi_critical(sample_params_dict)
    assert chi_eff > 0.0
    assert chi_c > 0.0


def test_two_phase_auxiliary_chain_outputs_consistent(sample_params_dict: dict[str, float]) -> None:
    aux = two_phase_auxiliary_chain(
        r=0.4,
        p=0.3,
        x_bar=0.2,
        y_bar=0.1,
        params=sample_params_dict,
    )
    assert 0.0 <= aux.theta_r <= 1.0
    assert aux.w_i + aux.w_ii == pytest.approx(1.0)
    assert aux.p_eff >= 0.0
