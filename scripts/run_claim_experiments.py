#!/usr/bin/env python3
"""Run paper-claim experiments (E1-E5) and emit structured report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

from rna_llps.config import load_params
from rna_llps.models.post_segregation import solve_post_segregation
from rna_llps.solvers.ode_wrappers import solve_full_ode
from rna_llps.thermo.flory_huggins import chi_critical, chi_rp_eff

STRESS_FACTORS = np.array([0.5, 0.8, 1.0, 1.2, 1.5, 2.0], dtype=float)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_params(base: dict[str, Any], stress_factor: float) -> dict[str, float]:
    params = dict(base)
    params["E"] = float(base["E"]) * float(stress_factor)
    return params


def x_coupling(params: dict[str, float], y_final: np.ndarray) -> float:
    x_bar = float(y_final[2])
    y_bar = float(y_final[3])
    return float(params["gamma"] * params["K_P"] * x_bar * y_bar)


def t95(t: np.ndarray, series: np.ndarray) -> float:
    target = float(series[-1])
    threshold = 0.95 * target
    idx = np.where(series >= threshold)[0]
    if idx.size == 0:
        return float(t[-1])
    return float(t[int(idx[0])])


def run_e1_monotonic_x(base_params: dict[str, float]) -> dict[str, Any]:
    xs: list[float] = []
    for sf in STRESS_FACTORS:
        params = make_params(base_params, float(sf))
        res = solve_full_ode(params=params, t_end=40.0)
        if not res.success:
            return {
                "id": "E1_monotonic_X_vs_stress",
                "pass": False,
                "error": f"ode solve failed at stress_factor={sf}: {res.message}",
            }
        xs.append(x_coupling(params, res.y[:, -1]))

    rho, pval = spearmanr(STRESS_FACTORS, np.array(xs))
    if np.isnan(rho):
        rho = 0.0
    if np.isnan(pval):
        pval = 1.0
    passed = bool((rho > 0.0) and (pval < 0.05))
    return {
        "id": "E1_monotonic_X_vs_stress",
        "pass": passed,
        "metrics": {
            "stress_factors": STRESS_FACTORS.tolist(),
            "x_star": xs,
            "spearman_rho_X_B": float(rho),
            "p_value": float(pval),
        },
        "rule": "spearman_rho_X_B > 0 and p_value < 0.05",
    }


def hysteresis_curve(
    base_params: dict[str, float],
    ascending: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    factors = STRESS_FACTORS if ascending else STRESS_FACTORS[::-1]
    y0: np.ndarray | None = None
    xs: list[float] = []
    for sf in factors:
        params = make_params(base_params, float(sf))
        res = solve_full_ode(params=params, y0=y0, t_end=30.0)
        if not res.success:
            raise RuntimeError(f"hysteresis solve failed at stress_factor={sf}: {res.message}")
        y0 = res.y[:, -1]
        xs.append(x_coupling(params, y0))
    return factors, np.array(xs, dtype=float)


def run_e2_stability_hysteresis(base_params: dict[str, float]) -> dict[str, Any]:
    stress = 1.5
    params = make_params(base_params, stress)
    inits = [
        np.array([0.05, 0.05, 0.01, 0.01], dtype=float),
        np.array([0.20, 0.10, 0.05, 0.05], dtype=float),
        np.array([0.80, 0.60, 0.20, 0.20], dtype=float),
    ]

    terminals: list[float] = []
    for y0 in inits:
        res = solve_full_ode(params=params, y0=y0, t_end=40.0)
        if not res.success:
            return {
                "id": "E2_global_stability_no_hysteresis",
                "pass": False,
                "error": f"ode solve failed for init {y0.tolist()}: {res.message}",
            }
        terminals.append(x_coupling(params, res.y[:, -1]))

    terminal_variance = float(np.var(terminals))

    try:
        asc_f, asc_x = hysteresis_curve(base_params, ascending=True)
        desc_f, desc_x = hysteresis_curve(base_params, ascending=False)
    except RuntimeError as exc:
        return {
            "id": "E2_global_stability_no_hysteresis",
            "pass": False,
            "error": str(exc),
        }

    desc_reindexed = desc_x[::-1]
    hysteresis_area = float(np.trapz(np.abs(asc_x - desc_reindexed), asc_f))

    passed = bool((terminal_variance < 1e-6) and (hysteresis_area < 1e-3))
    return {
        "id": "E2_global_stability_no_hysteresis",
        "pass": passed,
        "metrics": {
            "terminal_x": terminals,
            "terminal_variance": terminal_variance,
            "hysteresis_area": hysteresis_area,
        },
        "rule": "terminal_variance < 1e-6 and hysteresis_area < 1e-3",
    }


def run_e3_decoupling(base_params: dict[str, float]) -> dict[str, Any]:
    x_star: list[float] = []
    r_star: list[float] = []
    p_star: list[float] = []

    for sf in STRESS_FACTORS:
        params = make_params(base_params, float(sf))
        res = solve_full_ode(params=params, t_end=40.0)
        if not res.success:
            return {
                "id": "E3_growth_function_decoupling",
                "pass": False,
                "error": f"ode solve failed at stress_factor={sf}: {res.message}",
            }
        y_end = res.y[:, -1]
        r_star.append(float(y_end[0]))
        p_star.append(float(y_end[1]))
        x_star.append(x_coupling(params, y_end))

    delta_x = float(max(x_star) - min(x_star))
    rp_total = np.array(r_star) + np.array(p_star)
    rp_rel_span = float((rp_total.max() - rp_total.min()) / max(np.mean(rp_total), 1e-12))

    passed = bool((delta_x > 0.0) and (rp_rel_span < 0.15))
    return {
        "id": "E3_growth_function_decoupling",
        "pass": passed,
        "metrics": {
            "x_star": x_star,
            "r_star": r_star,
            "p_star": p_star,
            "delta_X": delta_x,
            "rp_rel_span": rp_rel_span,
        },
        "rule": "delta_X > 0 and rp_rel_span < 0.15",
    }


def run_e4_spinodal_crossing(base_params: dict[str, float]) -> dict[str, Any]:
    diff_values: list[float] = []
    chi_eff_values: list[float] = []
    chi_c_values: list[float] = []

    for sf in STRESS_FACTORS:
        params = make_params(base_params, float(sf))
        res = solve_full_ode(params=params, t_end=40.0)
        if not res.success:
            return {
                "id": "E4_spinodal_crossing",
                "pass": False,
                "error": f"ode solve failed at stress_factor={sf}: {res.message}",
            }

        r, p = float(res.y[0, -1]), float(res.y[1, -1])
        chi_eff = float(chi_rp_eff(r, p, params))
        chi_c = float(chi_critical(params))
        diff = chi_eff - chi_c

        chi_eff_values.append(chi_eff)
        chi_c_values.append(chi_c)
        diff_values.append(diff)

    signs = np.sign(np.array(diff_values))
    crossing_count = 0
    for i in range(len(signs) - 1):
        if signs[i] == 0:
            crossing_count += 1
        elif signs[i] * signs[i + 1] < 0:
            crossing_count += 1

    passed = bool(crossing_count == 1)
    return {
        "id": "E4_spinodal_crossing",
        "pass": passed,
        "metrics": {
            "stress_factors": STRESS_FACTORS.tolist(),
            "chi_eff": chi_eff_values,
            "chi_critical": chi_c_values,
            "chi_diff": diff_values,
            "crossing_count": int(crossing_count),
        },
        "rule": "crossing_count == 1",
    }


def run_e5_post_seg_acceleration(base_params: dict[str, float]) -> dict[str, Any]:
    stress = 1.5
    params = make_params(base_params, stress)

    pre = solve_full_ode(params=params, t_end=40.0)
    if not pre.success:
        return {
            "id": "E5_post_seg_acceleration",
            "pass": False,
            "error": f"pre solve failed: {pre.message}",
        }

    x_pre = params["gamma"] * params["K_P"] * pre.y[2] * pre.y[3]
    t95_pre = t95(pre.t, x_pre)

    post = solve_post_segregation(params=params, t_end=30.0)
    if not post.success:
        return {
            "id": "E5_post_seg_acceleration",
            "pass": False,
            "error": f"post solve failed: {post.message}",
        }

    x_post = post.y[4] + post.y[5]
    t95_post = t95(post.t, x_post)
    passed = bool(t95_post < t95_pre)

    return {
        "id": "E5_post_seg_acceleration",
        "pass": passed,
        "metrics": {
            "t95_pre": float(t95_pre),
            "t95_post": float(t95_post),
            "acceleration_gain": float(t95_pre - t95_post),
        },
        "rule": "t95_post < t95_pre",
    }


def run_all_claims(base_params: dict[str, float]) -> dict[str, Any]:
    experiments = [
        run_e1_monotonic_x(base_params),
        run_e2_stability_hysteresis(base_params),
        run_e3_decoupling(base_params),
        run_e4_spinodal_crossing(base_params),
        run_e5_post_seg_acceleration(base_params),
    ]

    failed = [item["id"] for item in experiments if not item.get("pass", False)]
    return {
        "type": "claim-experiments",
        "checked_at_utc": utc_now_iso(),
        "experiments": experiments,
        "summary": {
            "total": len(experiments),
            "passed": len(experiments) - len(failed),
            "failed": len(failed),
            "failed_ids": failed,
        },
        "pass": len(failed) == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run paper-claim experiments")
    parser.add_argument("--config", default="configs/default_params.yaml")
    parser.add_argument("--out", default="results/repro/claim_report.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    base_params = load_params(args.config)
    report = run_all_claims(base_params)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict and not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
