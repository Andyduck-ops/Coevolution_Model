"""Critical-stress and spinodal analysis helpers."""

from __future__ import annotations

import numpy as np

from rna_llps.models.scalar_dynamics import compute_bn
from rna_llps.thermo.flory_huggins import chi_critical, chi_rp_eff


def critical_stress(params: dict[str, float], r: float = 0.2, p: float = 0.1) -> float:
    """Compute a critical stress proxy based on B_n and chi-thresholds.

    Notes:
        The function keeps legacy argument names ``r`` and ``p`` for API
        compatibility. In the current paper-aligned thermo mapping they are
        interpreted as trait placeholders ``x_bar`` and ``y_bar``.
    """
    b_n = compute_bn(
        delta_0=float(params["delta_0"]),
        e_scale=float(params["E"]),
        gamma=float(params["gamma"]),
        n_order=float(params["n"]),
    )
    chi_ratio = chi_critical(params) / max(chi_rp_eff(r, p, params), 1e-12)
    return float(b_n * chi_ratio)


def compute_spinodal(
    params: dict[str, float],
    r_range: tuple[float, float] = (0.0, 1.0),
    p_range: tuple[float, float] = (0.0, 1.0),
    n_grid: int = 40,
) -> dict[str, np.ndarray | float]:
    """Compute spinodal mask over grid where chi_eff >= chi_critical."""
    r_values = np.linspace(float(r_range[0]), float(r_range[1]), int(n_grid))
    p_values = np.linspace(float(p_range[0]), float(p_range[1]), int(n_grid))
    rr, pp = np.meshgrid(r_values, p_values, indexing="ij")

    chi_eff = np.zeros_like(rr, dtype=float)
    for i in range(rr.shape[0]):
        for j in range(rr.shape[1]):
            chi_eff[i, j] = chi_rp_eff(float(rr[i, j]), float(pp[i, j]), params)

    chi_c = chi_critical(params)
    mask = chi_eff >= chi_c

    return {
        "r_grid": rr,
        "p_grid": pp,
        "chi_eff": chi_eff,
        "chi_critical": float(chi_c),
        "spinodal_mask": mask,
    }
