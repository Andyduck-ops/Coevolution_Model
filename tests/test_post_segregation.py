from __future__ import annotations

import numpy as np
import pytest

from rna_llps.models.post_segregation import post_segregation_rhs, solve_post_segregation


def test_post_segregation_rhs_shape(sample_params_dict: dict[str, float]) -> None:
    y = np.array([0.08, 0.12, 0.04, 0.06, 0.03, 0.03], dtype=float)
    rhs = post_segregation_rhs(0.0, y, sample_params_dict)
    assert rhs.shape == (6,)


def test_solve_post_segregation_runs(sample_params_dict: dict[str, float]) -> None:
    result = solve_post_segregation(sample_params_dict, t_end=2.0, n_points=40)
    assert result.success is True
    assert result.y.shape == (6, 40)


def test_solve_post_segregation_requires_shape_6(sample_params_dict: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        solve_post_segregation(sample_params_dict, y0=np.zeros(4), t_end=1.0)
