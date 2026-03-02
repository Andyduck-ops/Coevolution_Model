"""Unified ODE wrappers with Jacobian, events and solver fallback."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy.integrate import OdeSolution, solve_ivp

from rna_llps.thermo.flory_huggins import chi_critical, chi_rp_eff

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
    """RHS for 4-variable coupled RNA-peptide dynamics.

    Paper-aligned system:
    ``[R, P, x_bar, y_bar]`` with stress-coupling
    ``S = x_bar * P * y_bar``.
    """
    _ = t
    r, p, x_bar, y_bar = (float(v) for v in y)

    alpha = float(params["alpha"])
    beta = float(params["beta"])
    kappa = float(params["kappa"])
    k_0 = float(params["k_0"])
    mu = float(params["mu"])
    mu_x = float(params["mu_x"])
    mu_y = float(params["mu_y"])
    k_r = float(params["K_R"])
    k_p = float(params["K_P"])
    v_x = float(params["V_x"])
    v_y = float(params["V_y"])
    gamma = float(params["gamma"])
    delta = float(params["delta_0"]) * float(params["E"])
    n_order = float(params["n"])

    s_raw = x_bar * p * y_bar
    s_coupling = float(np.clip(s_raw, -1e6, 1e6))
    s = max(s_coupling, 0.0)
    s_safe = max(s, 1e-12)
    s_clip = min(s_safe, 1e6)
    gs_clip = max(gamma * s_clip, 0.0)
    gs_n = gs_clip**n_order
    stress_den = 1.0 + gs_n
    stress_decay = delta / stress_den

    dr_dt = alpha * r * (1.0 + beta * s_coupling) * (1.0 - r / k_r) - stress_decay * r
    dp_dt = (k_0 * r + kappa * r * s_coupling) * (1.0 - p / k_p) - mu * p

    stress_gradient = (
        n_order
        * delta
        * (gamma**n_order)
        * (s_clip ** (n_order - 1.0))
        / ((1.0 + gs_n) ** 2)
    )

    dx_dt = v_x * p * y_bar * (alpha * beta + stress_gradient) - mu_x * x_bar
    dy_dt = kappa * v_y * r * x_bar - mu_y * y_bar

    return np.array([dr_dt, dp_dt, dx_dt, dy_dt], dtype=float)


def jac_full_system(t: float, y: np.ndarray, params: dict[str, float]) -> np.ndarray:
    """Numerical Jacobian for ``full_system_rhs`` (central finite difference)."""
    _ = t
    state = np.asarray(y, dtype=float)
    jac = np.zeros((4, 4), dtype=float)

    for i in range(state.size):
        h = 1e-7 * max(1.0, abs(state[i]))
        y_plus = state.copy()
        y_minus = state.copy()
        y_plus[i] += h
        y_minus[i] -= h
        f_plus = full_system_rhs(0.0, y_plus, params)
        f_minus = full_system_rhs(0.0, y_minus, params)
        jac[:, i] = (f_plus - f_minus) / (2.0 * h)

    # Keep finite Jacobian even in edge cases.
    if not np.isfinite(jac).all():
        return np.nan_to_num(jac, nan=0.0, posinf=0.0, neginf=0.0)
    return jac


def event_spinodal_crossing(t: float, y: np.ndarray, params: dict[str, float]) -> float:
    """Event function for spinodal crossing detection."""
    _ = t
    x_bar = float(y[2])
    y_bar = float(y[3])
    return chi_rp_eff(x_bar, y_bar, params) - chi_critical(params)


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
