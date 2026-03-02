"""Scalar auxiliary dynamics helpers for RNA-LLPS model."""

from __future__ import annotations

import numpy as np


def compute_bn(delta_0: float, e_scale: float, gamma: float, n_order: int | float) -> float:
    """Compute ``B_n = delta_0 * E * gamma^n`` with explicit exponent handling."""
    n_float = float(n_order)
    if n_float < 0.0:
        msg = "Hill order n must be non-negative."
        raise ValueError(msg)
    return float(delta_0 * e_scale * (gamma**n_float))


def compute_variance_terms(r: float, p: float, params: dict[str, float]) -> dict[str, float]:
    """Compute variance-derived helper terms from ``V_x`` and ``V_y``."""
    v_x = float(params["V_x"])
    v_y = float(params["V_y"])

    sigma_x = float(v_x * max(r, 0.0) / (1.0 + max(r, 0.0)))
    sigma_y = float(v_y * max(p, 0.0) / (1.0 + max(p, 0.0)))

    amplitude = float(np.sqrt(max(sigma_x * sigma_y, 0.0)))
    lambda_eff = float(sigma_x + sigma_y)

    return {
        "sigma_x": sigma_x,
        "sigma_y": sigma_y,
        "A": amplitude,
        "lambda": lambda_eff,
    }


def hill_activation(signal: float, b_n: float, n_order: int | float) -> float:
    """Stable Hill-like activation factor used in scalar coupling terms."""
    n_float = float(n_order)
    if n_float <= 0.0:
        msg = "Hill order n must be positive in hill_activation."
        raise ValueError(msg)

    signal_pos = max(signal, 0.0)
    numerator = signal_pos**n_float
    denominator = b_n + numerator
    if denominator <= 0.0:
        return 0.0
    return float(numerator / denominator)
