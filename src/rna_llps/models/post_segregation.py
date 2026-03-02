"""Post-segregation two-phase ODE wrapper and helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from rna_llps.thermo.flory_huggins import two_phase_auxiliary_chain


@dataclass(frozen=True)
class PostSegregationSummary:
    """Numerical summary for post-segregation solve."""

    success: bool
    message: str
    method_used: str
    t: np.ndarray
    y: np.ndarray


def post_segregation_rhs(t: float, y: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """RHS for a minimal 2-phase post-segregation relaxation system.

    State vector: ``[R_I, R_II, P_I, P_II, X_I, X_II]``.
    """
    _ = t
    r_i, r_ii, p_i, p_ii, x_i, x_ii = (float(v) for v in y)

    r_tot = max(r_i + r_ii, 1e-12)
    p_tot = max(p_i + p_ii, 1e-12)
    aux = two_phase_auxiliary_chain(
        r=r_tot,
        p=p_tot,
        x_bar=0.5 * (x_i + x_ii),
        y_bar=0.5 * (p_i + p_ii),
        params=params,
    )

    tau_r = 0.2
    tau_p = 0.2
    tau_x = 0.15

    dr_i = (aux.w_i * r_tot - r_i) / tau_r
    dr_ii = (aux.w_ii * r_tot - r_ii) / tau_r

    p_target_i = aux.w_i * p_tot * aux.pi_p
    p_target_ii = aux.w_ii * p_tot / max(aux.pi_p, 1e-12)
    dp_i = (p_target_i - p_i) / tau_p
    dp_ii = (p_target_ii - p_ii) / tau_p

    dx_i = (aux.x_loc_i - x_i) / tau_x
    dx_ii = (aux.x_loc_ii - x_ii) / tau_x

    return np.array([dr_i, dr_ii, dp_i, dp_ii, dx_i, dx_ii], dtype=float)


def solve_post_segregation(
    params: dict[str, float],
    y0: np.ndarray | None = None,
    t_end: float = 30.0,
    n_points: int = 250,
    primary_method: str = "Radau",
    fallback_method: str = "BDF",
) -> PostSegregationSummary:
    """Solve post-segregation dynamics with solver fallback."""
    if y0 is None:
        y0 = np.array([0.08, 0.12, 0.04, 0.06, 0.03, 0.03], dtype=float)
    else:
        y0 = np.asarray(y0, dtype=float)

    if y0.shape != (6,):
        msg = "Initial state y0 must have shape (6,)."
        raise ValueError(msg)

    t_eval = np.linspace(0.0, float(t_end), int(n_points))

    primary = solve_ivp(
        fun=lambda t, y: post_segregation_rhs(t, y, params),
        t_span=(0.0, float(t_end)),
        y0=y0,
        t_eval=t_eval,
        method=primary_method,
        rtol=1e-8,
        atol=np.array([1e-10, 1e-10, 1e-10, 1e-10, 1e-12, 1e-12], dtype=float),
    )

    if primary.success:
        return PostSegregationSummary(
            success=True,
            message=str(primary.message),
            method_used=primary_method,
            t=primary.t,
            y=primary.y,
        )

    fallback = solve_ivp(
        fun=lambda t, y: post_segregation_rhs(t, y, params),
        t_span=(0.0, float(t_end)),
        y0=y0,
        t_eval=t_eval,
        method=fallback_method,
        rtol=1e-8,
        atol=np.array([1e-10, 1e-10, 1e-10, 1e-10, 1e-12, 1e-12], dtype=float),
    )

    return PostSegregationSummary(
        success=bool(fallback.success),
        message=str(fallback.message),
        method_used=fallback_method if fallback.success else primary_method,
        t=fallback.t,
        y=fallback.y,
    )
