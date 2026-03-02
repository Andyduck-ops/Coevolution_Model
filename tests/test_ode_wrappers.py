from __future__ import annotations

import numpy as np

from rna_llps.solvers.ode_wrappers import (
    event_quasi_steady,
    event_spinodal_crossing,
    jac_full_system,
    solve_full_ode,
)


def test_jacobian_shape(sample_params_dict: dict[str, float]) -> None:
    y = np.array([0.2, 0.1, 0.05, 0.05], dtype=float)
    jac = jac_full_system(0.0, y, sample_params_dict)
    assert jac.shape == (4, 4)
    assert np.isfinite(jac).all()


def test_events_return_scalar(sample_params_dict: dict[str, float]) -> None:
    y = np.array([0.2, 0.1, 0.05, 0.05], dtype=float)
    assert isinstance(event_spinodal_crossing(0.0, y, sample_params_dict), float)
    assert isinstance(event_quasi_steady(0.0, y, sample_params_dict), float)


def test_solve_full_ode_runs(sample_params_dict: dict[str, float]) -> None:
    result = solve_full_ode(sample_params_dict, t_end=3.0, n_points=50)
    assert result.success is True
    assert result.t.size == 50
    assert result.y.shape == (4, 50)
