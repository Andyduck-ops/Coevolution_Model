#!/usr/bin/env python3
"""Run rebuttal/ablation experiments (R1-R4) and emit structured report."""

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

STRESS_FACTORS = np.array([0.5, 0.8, 1.0, 1.2, 1.5, 2.0], dtype=float)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def with_stress(
    base: dict[str, Any],
    factor: float,
    enable_stress: bool = True,
) -> dict[str, float]:
    params = dict(base)
    if enable_stress:
        params["E"] = float(base["E"]) * float(factor)
    return params


def x_coupling(params: dict[str, float], y_final: np.ndarray) -> float:
    return float(params["gamma"] * params["K_P"] * float(y_final[2]) * float(y_final[3]))


def t95(t: np.ndarray, series: np.ndarray) -> float:
    target = float(series[-1])
    tol = 0.05 * max(abs(target), abs(float(series[0]) - target), 1e-12)
    idx = np.where(np.abs(series - target) <= tol)[0]
    if idx.size == 0:
        return float(t[-1])
    return float(t[int(idx[0])])


def relative_span(values: np.ndarray) -> float:
    mean_abs = max(float(np.mean(np.abs(values))), 1e-12)
    return float((float(np.max(values)) - float(np.min(values))) / mean_abs)


def map_pre_to_post_initial(
    pre_terminal: np.ndarray,
    params: dict[str, float] | None = None,
) -> np.ndarray:
    """Map 4D pre-segregation terminal state to 6D post-segregation initial state."""
    r, p, x_bar, y_bar = (float(v) for v in pre_terminal)
    epsilon = float(params["epsilon"]) if params is not None else 0.0
    x_floor = 1e-6 * (1.0 + 2.0 * max(epsilon, 0.0))
    x_total = max(float(x_bar * y_bar), x_floor)
    return np.array(
        [
            0.45 * r,
            0.55 * r,
            0.40 * p,
            0.60 * p,
            0.35 * x_total,
            0.65 * x_total,
        ],
        dtype=float,
    )


def x_series_across_stress(
    base_params: dict[str, float],
    enable_stress: bool = True,
) -> tuple[np.ndarray, np.ndarray, str | None]:
    x_vals: list[float] = []
    for sf in STRESS_FACTORS:
        params = with_stress(base_params, float(sf), enable_stress=enable_stress)
        res = solve_full_ode(params=params, t_end=40.0)
        if not res.success:
            return np.array([]), np.array([]), res.message
        x_vals.append(x_coupling(params, res.y[:, -1]))
    return STRESS_FACTORS.copy(), np.array(x_vals, dtype=float), None


def hysteresis_curves(
    base_params: dict[str, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str | None]:
    def run_curve(ascending: bool) -> tuple[np.ndarray, np.ndarray, str | None]:
        factors = STRESS_FACTORS if ascending else STRESS_FACTORS[::-1]
        y0: np.ndarray | None = None
        x_vals: list[float] = []
        for sf in factors:
            params = with_stress(base_params, float(sf), enable_stress=True)
            res = solve_full_ode(params=params, y0=y0, t_end=30.0)
            if not res.success:
                return np.array([]), np.array([]), res.message
            y0 = res.y[:, -1]
            x_vals.append(x_coupling(params, y0))
        return factors, np.array(x_vals, dtype=float), None

    asc_f, asc_x, err = run_curve(True)
    if err:
        return np.array([]), np.array([]), np.array([]), err
    _, desc_x, err = run_curve(False)
    if err:
        return np.array([]), np.array([]), np.array([]), err

    return asc_f, asc_x, desc_x[::-1], None


def hysteresis_stats(base_params: dict[str, float]) -> tuple[dict[str, float], str | None]:
    factors, asc_x, desc_x, err = hysteresis_curves(base_params)
    if err:
        return {}, err

    area = float(np.trapz(np.abs(asc_x - desc_x), factors))
    denom = float(np.trapz((np.abs(asc_x) + np.abs(desc_x)) / 2.0, factors))
    index = area / max(denom, 1e-12)
    return {
        "area": area,
        "index": float(index),
        "median_signal": float(np.median(np.abs((asc_x + desc_x) / 2.0))),
    }, None


def run_r1_remove_mutualism(base_params: dict[str, float]) -> dict[str, Any]:
    stress = 1.5
    base = with_stress(base_params, stress)
    baseline = solve_full_ode(base, t_end=40.0)
    if not baseline.success:
        return {"id": "R1_remove_mutualism", "pass": False, "error": baseline.message}

    x_base = x_coupling(base, baseline.y[:, -1])

    ablated = dict(base)
    ablated["beta"] = 0.0
    ablated["kappa"] = 0.0
    ab = solve_full_ode(ablated, t_end=40.0)
    if not ab.success:
        return {"id": "R1_remove_mutualism", "pass": False, "error": ab.message}

    x_ab = x_coupling(ablated, ab.y[:, -1])
    ratio = float(x_ab / max(x_base, 1e-12))
    # In paper-aligned low-coupling regimes, a ≥5% drop is treated as meaningful.
    passed = bool(ratio < 0.95)

    return {
        "id": "R1_remove_mutualism",
        "pass": passed,
        "metrics": {
            "x_baseline": float(x_base),
            "x_ablated": float(x_ab),
            "ratio": ratio,
        },
        "rule": "x_ablated / x_baseline < 0.95",
    }


def run_r2_weaken_stress_selection(base_params: dict[str, float]) -> dict[str, Any]:
    sf_b, x_b, err = x_series_across_stress(base_params, enable_stress=True)
    if err:
        return {"id": "R2_weaken_stress_selection", "pass": False, "error": err}

    sf_a, x_a, err = x_series_across_stress(base_params, enable_stress=False)
    if err:
        return {"id": "R2_weaken_stress_selection", "pass": False, "error": err}

    baseline_scale = max(float(np.mean(np.abs(x_b))), 1e-18)
    ablated_scale = max(float(np.mean(np.abs(x_a))), 1e-18)

    if float(np.std(x_b)) <= 1e-6 * baseline_scale:
        rho_b, p_b = 0.0, 1.0
    else:
        rho_b, p_b = spearmanr(sf_b, x_b)

    if float(np.std(x_a)) <= 1e-6 * ablated_scale:
        rho_a, p_a = 0.0, 1.0
    else:
        rho_a, p_a = spearmanr(sf_a, x_a)
    if np.isnan(rho_b):
        rho_b = 0.0
    if np.isnan(rho_a):
        rho_a = 0.0
    if np.isnan(p_b):
        p_b = 1.0
    if np.isnan(p_a):
        p_a = 1.0

    span_b = relative_span(x_b)
    span_a = relative_span(x_a)

    passed = bool(
        (abs(rho_b) >= 0.8)
        and (p_b < 0.05)
        and ((abs(rho_a) <= 0.3) or (p_a >= 0.1))
        and (span_a <= 0.4 * span_b)
    )

    return {
        "id": "R2_weaken_stress_selection",
        "pass": passed,
        "metrics": {
            "baseline_rho": float(rho_b),
            "baseline_p": float(p_b),
            "ablated_rho": float(rho_a),
            "ablated_p": float(p_a),
            "baseline_span": span_b,
            "ablated_span": span_a,
            "x_baseline": x_b.tolist(),
            "x_ablated": x_a.tolist(),
        },
        "rule": (
            "abs(baseline_rho)>=0.8 & baseline_p<0.05 & "
            "(abs(ablated_rho)<=0.3 or ablated_p>=0.1) & "
            "ablated_span<=0.4*baseline_span"
        ),
    }


def run_r3_flat_partition(base_params: dict[str, float]) -> dict[str, Any]:
    stress = 1.5
    base = with_stress(base_params, stress)

    pre = solve_full_ode(base, t_end=40.0)
    post = solve_post_segregation(
        base,
        y0=map_pre_to_post_initial(pre.y[:, -1], base),
        t_end=30.0,
    )
    if (not pre.success) or (not post.success):
        return {
            "id": "R3_flat_partition",
            "pass": False,
            "error": f"baseline solve failed: pre={pre.message}, post={post.message}",
        }

    pre_t95 = t95(pre.t, base["gamma"] * base["K_P"] * pre.y[2] * pre.y[3])
    post_t95 = t95(post.t, post.y[4] + post.y[5])
    accel_base = float(1.0 - post_t95 / max(pre_t95, 1e-12))

    flat = dict(base)
    flat["epsilon"] = 0.0

    pre_flat = solve_full_ode(flat, t_end=40.0)
    post_flat = solve_post_segregation(
        flat,
        y0=map_pre_to_post_initial(pre_flat.y[:, -1], flat),
        t_end=30.0,
    )
    if (not pre_flat.success) or (not post_flat.success):
        return {
            "id": "R3_flat_partition",
            "pass": False,
            "error": (
                f"flat-partition solve failed: pre={pre_flat.message}, post={post_flat.message}"
            ),
        }

    pre_t95_flat = t95(pre_flat.t, flat["gamma"] * flat["K_P"] * pre_flat.y[2] * pre_flat.y[3])
    post_t95_flat = t95(post_flat.t, post_flat.y[4] + post_flat.y[5])
    accel_flat = float(1.0 - post_t95_flat / max(pre_t95_flat, 1e-12))

    passed = bool(
        (accel_base >= 0.2)
        and ((accel_flat <= 0.1) or (accel_flat <= 0.5 * accel_base))
        and (post_t95_flat >= 0.8 * pre_t95_flat)
    )

    return {
        "id": "R3_flat_partition",
        "pass": passed,
        "metrics": {
            "accel_baseline": accel_base,
            "accel_flat": accel_flat,
            "pre_t95": float(pre_t95),
            "post_t95": float(post_t95),
            "pre_t95_flat": float(pre_t95_flat),
            "post_t95_flat": float(post_t95_flat),
        },
        "rule": "accel_baseline>=0.2 and accel_flat reduced with t95_post_flat close to pre",
    }


def run_r4_alt_nonlinearity(base_params: dict[str, float]) -> dict[str, Any]:
    base_stats, err = hysteresis_stats(base_params)
    if err:
        return {"id": "R4_alternative_nonlinearity", "pass": False, "error": err}

    alt = dict(base_params)
    alt["n"] = 4.0

    alt_stats, err = hysteresis_stats(alt)
    if err:
        return {"id": "R4_alternative_nonlinearity", "pass": False, "error": err}

    if base_stats["index"] <= 0.05:
        passed = bool(
            (alt_stats["index"] >= 0.15)
            and (alt_stats["index"] - base_stats["index"] >= 0.05)
            and (alt_stats["median_signal"] >= 0.3 * base_stats["median_signal"])
        )
        rule = "baseline near-no-hysteresis -> alternative should induce strong hysteresis"
    else:
        passed = bool(
            (alt_stats["index"] >= 0.8 * base_stats["index"])
            and (alt_stats["median_signal"] >= 0.3 * base_stats["median_signal"])
        )
        rule = "baseline already hysteretic -> alternative should preserve comparable hysteresis"

    return {
        "id": "R4_alternative_nonlinearity",
        "pass": passed,
        "metrics": {
            "hysteresis_area_baseline": base_stats["area"],
            "hysteresis_area_alternative": alt_stats["area"],
            "hysteresis_index_baseline": base_stats["index"],
            "hysteresis_index_alternative": alt_stats["index"],
            "median_signal_baseline": base_stats["median_signal"],
            "median_signal_alternative": alt_stats["median_signal"],
        },
        "rule": rule,
    }


def run_all_ablations(base_params: dict[str, float]) -> dict[str, Any]:
    experiments = [
        run_r1_remove_mutualism(base_params),
        run_r2_weaken_stress_selection(base_params),
        run_r3_flat_partition(base_params),
        run_r4_alt_nonlinearity(base_params),
    ]

    failed = [item["id"] for item in experiments if not item.get("pass", False)]
    return {
        "type": "ablation-experiments",
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
    parser = argparse.ArgumentParser(description="Run ablation experiments")
    parser.add_argument("--config", default="configs/default_params.yaml")
    parser.add_argument("--out", default="results/repro/ablation_report.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    base_params = load_params(args.config)
    report = run_all_ablations(base_params)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict and not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
