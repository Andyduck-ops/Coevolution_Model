"""Unified ODE wrappers with Jacobian, events and solver fallback."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy.integrate import OdeSolution, solve_ivp

from rna_llps.models.scalar_dynamics import compute_bn
from rna_llps.thermo.flory_huggins import chi_critical, chi_rp_eff, partition_coeff_logsafe

RHS = Callable[[float, np.ndarray], np.ndarray]


@dataclass(frozen=True)
class ODESolveSummary:
    """Summary of one ODE solve attempt."""

    success: bool
    message: str
    method_used: str
    fallback_used: bool
    nfev: int
    njev: int
    t: np.ndarray
    y: np.ndarray
    sol: OdeSolution | None


def full_system_rhs(t: float, y: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """RHS for 4-variable coupled RNA-peptide dynamics."""
    _ = t
    r, p, x_bar, y_bar = (float(v) for v in y)

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

    b_n = compute_bn(
        delta_0=float(params["delta_0"]),
        e_scale=float(params["E"]),
        gamma=gamma,
        n_order=float(params["n"]),
    )
    pi_p = partition_coeff_logsafe(
        x_bar=x_bar,
        y_bar=y_bar,
        epsilon=float(params["epsilon"]),
        k_bt=float(params["k_BT"]),
    )

    dr_dt = alpha * r * (1.0 - r / k_r) - gamma * x_bar * r
    dp_dt = beta * p * (1.0 - p / k_p) + kappa * y_bar * r - b_n * p / (1.0 + p)
    dp_dt += 0.05 * (pi_p - 1.0)

    dx_dt = mu_x * (v_x * r / (1.0 + r) - x_bar)
    dy_dt = mu_y * (v_y * p / (1.0 + p) - y_bar)

    return np.array([dr_dt, dp_dt, dx_dt, dy_dt], dtype=float)


def jac_full_system(t: float, y: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Analytic Jacobian for ``full_system_rhs``."""
    _ = t
    r, p, x_bar, y_bar = (float(v) for v in y)

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

    b_n = compute_bn(
        delta_0=float(params["delta_0"]),
        e_scale=float(params["E"]),
        gamma=gamma,
        n_order=float(params["n"]),
    )

    # d(dr)/d(...)
    j11 = alpha * (1.0 - 2.0 * r / k_r) - gamma * x_bar
    j12 = 0.0
    j13 = -gamma * r
    j14 = 0.0

    # d(dp)/d(...)
    j21 = kappa * y_bar
    j22 = beta * (1.0 - 2.0 * p / k_p) - b_n / (1.0 + p) ** 2
    j23 = 0.05 * float(params["epsilon"]) * y_bar / float(params["k_BT"])
    j24 = kappa * r + 0.05 * float(params["epsilon"]) * x_bar / float(params["k_BT"])

    # d(dx)/d(...)
    j31 = mu_x * v_x / (1.0 + r) ** 2
    j32 = 0.0
    j33 = -mu_x
    j34 = 0.0

    # d(dy)/d(...)
    j41 = 0.0
    j42 = mu_y * v_y / (1.0 + p) ** 2
    j43 = 0.0
    j44 = -mu_y

    return np.array(
        [
            [j11, j12, j13, j14],
            [j21, j22, j23, j24],
            [j31, j32, j33, j34],
            [j41, j42, j43, j44],
        ],
        dtype=float,
    )


def event_spinodal_crossing(t: float, y: np.ndarray, params: dict[str, float]) -> float:
    """Event function for spinodal crossing detection."""
    _ = t
    r = float(y[0])
    p = float(y[1])
    return chi_rp_eff(r, p, params) - chi_critical(params)


def event_quasi_steady(
    t: float,
    y: np.ndarray,
    params: dict[str, float],
    tol: float = 1e-8,
) -> float:
    """Event function for quasi-steady detection via RHS norm."""
    _ = t
    dydt = full_system_rhs(t, y, params)
    return float(np.linalg.norm(dydt) - tol)


def _make_events(
    params: dict[str, float],
    with_events: bool,
) -> list[Callable[[float, np.ndarray], float]] | None:
    if not with_events:
        return None

    def spinodal_event(t: float, y: np.ndarray) -> float:
        return event_spinodal_crossing(t, y, params)

    spinodal_event.terminal = False
    spinodal_event.direction = 0

    def steady_event(t: float, y: np.ndarray) -> float:
        return event_quasi_steady(t, y, params)

    steady_event.terminal = False
    steady_event.direction = -1

    def non_negative_event(t: float, y: np.ndarray) -> float:
        _ = t
        return float(np.min(y) + 1e-12)

    non_negative_event.terminal = True
    non_negative_event.direction = -1

    return [spinodal_event, steady_event, non_negative_event]


def solve_full_ode(
    params: dict[str, float],
    y0: np.ndarray | None = None,
    t_end: float = 40.0,
    n_points: int = 300,
    rtol: float = 1e-8,
    atol: np.ndarray | None = None,
    primary_method: str = "Radau",
    fallback_method: str = "BDF",
    with_events: bool = True,
) -> ODESolveSummary:
    """Solve full 4-variable ODE with Jacobian and fallback policy."""
    if y0 is None:
        y0 = np.array([0.2, 0.1, 0.05, 0.05], dtype=float)
    else:
        y0 = np.asarray(y0, dtype=float)

    if y0.shape != (4,):
        msg = "Initial state y0 must have shape (4,)."
        raise ValueError(msg)

    if atol is None:
        atol = np.array([1e-10, 1e-10, 1e-12, 1e-12], dtype=float)

    t_eval = np.linspace(0.0, float(t_end), int(n_points))
    events = _make_events(params, with_events=with_events)

    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        return full_system_rhs(t, y, params)

    def jac(t: float, y: np.ndarray) -> np.ndarray:
        return jac_full_system(t, y, params)

    primary = solve_ivp(
        fun=rhs,
        jac=jac,
        t_span=(0.0, float(t_end)),
        y0=y0,
        t_eval=t_eval,
        method=primary_method,
        rtol=rtol,
        atol=atol,
        dense_output=True,
        events=events,
    )

    if primary.success:
        return ODESolveSummary(
            success=True,
            message=str(primary.message),
            method_used=primary_method,
            fallback_used=False,
            nfev=int(primary.nfev),
            njev=int(primary.njev),
            t=primary.t,
            y=primary.y,
            sol=primary.sol,
        )

    fallback = solve_ivp(
        fun=rhs,
        jac=jac,
        t_span=(0.0, float(t_end)),
        y0=y0,
        t_eval=t_eval,
        method=fallback_method,
        rtol=rtol,
        atol=atol,
        dense_output=True,
        events=events,
    )

    return ODESolveSummary(
        success=bool(fallback.success),
        message=str(fallback.message),
        method_used=fallback_method if fallback.success else primary_method,
        fallback_used=True,
        nfev=int(fallback.nfev),
        njev=int(fallback.njev),
        t=fallback.t,
        y=fallback.y,
        sol=fallback.sol,
    )
