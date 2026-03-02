"""Minimal 4-variable ODE system for smoke validation."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

State = Sequence[float]


def rhs_minimal_system(t: float, y: State, params: dict[str, float]) -> np.ndarray:
    """Compute derivatives for a minimal RNA-peptide coupled system.

    This is a scaffold model for E2E infrastructure validation, not the final paper model.

    Args:
        t: Time point.
        y: State vector ``[R, P, x_bar, y_bar]``.
        params: Parameter dictionary loaded from config.

    Returns:
        Derivative vector with shape (4,).
    """
    _ = t  # Time-independent RHS in this scaffold.
    r, p, x_bar, y_bar = y

    alpha = float(params["alpha"])
    beta = float(params["beta"])
    kappa = float(params["kappa"])
    mu_x = float(params["mu_x"])
    mu_y = float(params["mu_y"])
    k_r = float(params["K_R"])
    k_p = float(params["K_P"])
    v_x = float(params["V_x"])
    v_y = float(params["V_y"])
    gamma = float(params["gamma"])

    dr_dt = alpha * r * (1.0 - r / k_r) - gamma * x_bar * r
    dp_dt = beta * p * (1.0 - p / k_p) + kappa * y_bar * r
    dx_dt = mu_x * (v_x * r / (1.0 + r) - x_bar)
    dy_dt = mu_y * (v_y * p / (1.0 + p) - y_bar)

    return np.array([dr_dt, dp_dt, dx_dt, dy_dt], dtype=float)
