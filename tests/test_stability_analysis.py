from __future__ import annotations

import numpy as np

from rna_llps.analysis.stability import compute_spinodal, critical_stress


def test_critical_stress_exists(sample_params_dict: dict[str, float]) -> None:
    value = critical_stress(sample_params_dict, r=0.3, p=0.2)
    assert np.isfinite(value)


def test_compute_spinodal_exists(sample_params_dict: dict[str, float]) -> None:
    result = compute_spinodal(sample_params_dict, n_grid=20)
    assert result["r_grid"].shape == (20, 20)
    assert result["p_grid"].shape == (20, 20)
    assert result["spinodal_mask"].shape == (20, 20)
    assert result["spinodal_mask"].dtype == np.bool_
