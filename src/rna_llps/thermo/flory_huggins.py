"""Flory-Huggins inspired thermodynamic utilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TwoPhaseAuxiliary:
    """Container for two-phase auxiliary-chain outputs."""

    theta_r: float
    w_i: float
    w_ii: float
    pi_p: float
    p_eff: float
    a_eff: float
    x_loc_i: float
    x_loc_ii: float


def partition_coeff_logsafe(
    x_bar: float,
    y_bar: float,
    epsilon: float,
    k_bt: float,
    clip_min: float = -60.0,
    clip_max: float = 60.0,
) -> float:
    """Compute partition coefficient with overflow-safe exponential.

    Args:
        x_bar: Mean feature x.
        y_bar: Mean feature y.
        epsilon: Coupling energy scale.
        k_bt: Thermal energy.
        clip_min: Lower clipping bound in log-domain.
        clip_max: Upper clipping bound in log-domain.

    Returns:
        Stable estimate of ``Pi_P = exp(epsilon*x_bar*y_bar/k_BT)``.
    """
    if k_bt <= 0.0:
        msg = "k_BT must be positive for partition coefficient."
        raise ValueError(msg)

    log_pi = epsilon * x_bar * y_bar / k_bt
    log_pi = float(np.clip(log_pi, clip_min, clip_max))
    return float(np.exp(log_pi))


def chi_rp_eff(x_bar: float, y_bar: float, params: dict[str, float]) -> float:
    """Effective interaction parameter for RNA-peptide mixture.

    Paper-consistent form:
    ``chi_eff = chi_0 + (epsilon / k_BT) * x_bar * y_bar``.
    """
    chi_0 = float(params["chi_0"])
    epsilon = float(params["epsilon"])
    k_bt = float(params["k_BT"])
    if k_bt <= 0.0:
        msg = "k_BT must be positive for chi_rp_eff."
        raise ValueError(msg)
    return float(chi_0 + (epsilon / k_bt) * float(x_bar) * float(y_bar))


def chi_critical(params: dict[str, float]) -> float:
    """Critical effective interaction threshold used for spinodal events.

    Paper-consistent form:
    ``chi_c = sqrt((1/phi_R - chi_RR) * (1/phi_P - chi_PP))`` with
    ``phi_R=v_R*K_R`` and ``phi_P=v_P*K_P``.
    """
    v_r = float(params["v_R"])
    v_p = float(params["v_P"])
    k_r = float(params["K_R"])
    k_p = float(params["K_P"])
    chi_rr = float(params["chi_RR"])
    chi_pp = float(params["chi_PP"])

    phi_r = max(v_r * k_r, 1e-12)
    phi_p = max(v_p * k_p, 1e-12)
    radicand = (1.0 / phi_r - chi_rr) * (1.0 / phi_p - chi_pp)
    return float(np.sqrt(max(radicand, 0.0)))


def theta_r(r: float, p: float, params: dict[str, float]) -> float:
    """Phase partition factor for RNA species."""
    v_r = float(params["v_R"])
    v_p = float(params["v_P"])
    denom = max(v_r * max(r, 0.0) + v_p * max(p, 0.0), 1e-12)
    return float(np.clip(v_r * max(r, 0.0) / denom, 0.0, 1.0))


def phase_weights(theta_value: float) -> tuple[float, float]:
    """Compute phase-I / phase-II weights from partition factor."""
    w_i = float(np.clip(theta_value, 0.0, 1.0))
    w_ii = float(1.0 - w_i)
    return w_i, w_ii


def two_phase_auxiliary_chain(
    r: float,
    p: float,
    x_bar: float,
    y_bar: float,
    params: dict[str, float],
    clip_min: float = -60.0,
    clip_max: float = 60.0,
) -> TwoPhaseAuxiliary:
    """Evaluate the auxiliary chain ``Θ_R -> W^I/W^II -> P_eff -> A_eff -> X_loc``."""
    theta_value = theta_r(r, p, params)
    w_i, w_ii = phase_weights(theta_value)

    pi_p = partition_coeff_logsafe(
        x_bar=x_bar,
        y_bar=y_bar,
        epsilon=float(params["epsilon"]),
        k_bt=float(params["k_BT"]),
        clip_min=clip_min,
        clip_max=clip_max,
    )

    p_eff = float(max(p, 0.0) * (w_i + w_ii * pi_p))
    a_eff = float(float(params["alpha"]) * max(r, 0.0) / (1.0 + p_eff))

    x_loc_i = float(a_eff * w_i)
    x_loc_ii = float(a_eff * w_ii)

    return TwoPhaseAuxiliary(
        theta_r=theta_value,
        w_i=w_i,
        w_ii=w_ii,
        pi_p=pi_p,
        p_eff=p_eff,
        a_eff=a_eff,
        x_loc_i=x_loc_i,
        x_loc_ii=x_loc_ii,
    )
