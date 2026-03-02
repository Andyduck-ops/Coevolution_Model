from __future__ import annotations

import numpy as np

from rna_llps.models import rhs_minimal_system


def test_rhs_shape() -> None:
    params = {
        "alpha": 1.0,
        "beta": 1.0,
        "kappa": 1.0,
        "mu_x": 0.1,
        "mu_y": 0.1,
        "K_R": 1.0,
        "K_P": 1.0,
        "V_x": 1.0,
        "V_y": 1.0,
        "gamma": 1.0,
    }
    y = [0.2, 0.1, 0.05, 0.05]
    rhs = rhs_minimal_system(0.0, y, params)

    assert rhs.shape == (4,)
    assert np.isfinite(rhs).all()
