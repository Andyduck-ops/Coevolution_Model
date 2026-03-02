#!/usr/bin/env python3
"""Check reproduction artifacts with optional reference-fidelity scoring."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

DEFAULT_REQUIRED = [
    "fig1_stability",
    "fig2_timecourse",
    "fig3_spinodal",
    "fig4_post_segregation",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def auto_detect_reference_dir() -> Path | None:
    candidates = sorted(Path(".").glob("COPY1__*"))
    for item in candidates:
        if item.is_dir():
            return item
    return None


def load_metrics_config(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def resize_nearest(image: np.ndarray, target_hw: tuple[int, int]) -> np.ndarray:
    h, w = image.shape
    th, tw = target_hw
    row_idx = np.linspace(0, h - 1, th).astype(int)
    col_idx = np.linspace(0, w - 1, tw).astype(int)
    return image[np.ix_(row_idx, col_idx)]


def load_gray_image(path: Path, target_hw: tuple[int, int] = (256, 256)) -> np.ndarray:
    image = plt.imread(path)
    if image.ndim == 3:
        rgb = image[..., :3]
        image = 0.2989 * rgb[..., 0] + 0.5870 * rgb[..., 1] + 0.1140 * rgb[..., 2]

    image = image.astype(float)
    if image.max() > 1.0:
        image /= 255.0

    image = resize_nearest(image, target_hw)
    image = np.clip(image, 0.0, 1.0)
    return image


def image_similarity_metrics(generated: Path, reference: Path) -> dict[str, float]:
    g = load_gray_image(generated)
    r = load_gray_image(reference)

    mae = float(np.mean(np.abs(g - r)))
    mae_score = float(max(0.0, 1.0 - mae))

    g_flat = g.reshape(-1)
    r_flat = r.reshape(-1)
    g_std = float(np.std(g_flat))
    r_std = float(np.std(r_flat))

    if g_std < 1e-12 or r_std < 1e-12:
        corr = 1.0 if mae < 1e-6 else 0.0
    else:
        corr = float(np.corrcoef(g_flat, r_flat)[0, 1])
        corr = max(-1.0, min(1.0, corr))

    corr_score = 0.5 * (corr + 1.0)
    composite = 0.5 * (mae_score + corr_score)

    return {
        "mae": mae,
        "mae_score": mae_score,
        "corr": corr,
        "corr_score": corr_score,
        "composite": composite,
    }


def check_artifacts(fig_dir: Path, required_figures: list[str]) -> tuple[list[str], dict[str, int]]:
    missing: list[str] = []
    sizes: dict[str, int] = {}

    for stem in required_figures:
        for ext in ["png", "pdf"]:
            f = fig_dir / f"{stem}.{ext}"
            if not f.is_file():
                missing.append(str(f))
            else:
                sizes[str(f)] = f.stat().st_size

    return missing, sizes


def resolve_reference_mapping(config: dict, required_figures: list[str]) -> dict[str, str]:
    mapping = config.get("reference_mapping", {})
    if not isinstance(mapping, dict):
        mapping = {}

    resolved: dict[str, str] = {}
    for stem in required_figures:
        resolved[stem] = str(mapping.get(stem, f"{stem}.png"))
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Check reproduction metrics")
    parser.add_argument("--fig-dir", default="figures/paper")
    parser.add_argument("--out", default="results/repro/repro_report.json")
    parser.add_argument("--metrics-config", default="configs/repro_metrics.yaml")
    parser.add_argument("--reference-dir", default="")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-fidelity", action="store_true")
    args = parser.parse_args()

    fig_dir = Path(args.fig_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    config = load_metrics_config(Path(args.metrics_config))
    required_figures = list(config.get("required_figures", DEFAULT_REQUIRED))
    reference_mapping = resolve_reference_mapping(config, required_figures)

    threshold = float(config.get("fidelity", {}).get("composite_threshold", 0.75))

    missing, sizes = check_artifacts(fig_dir, required_figures)

    reference_dir = Path(args.reference_dir) if args.reference_dir else auto_detect_reference_dir()
    fidelity_details: dict[str, dict] = {}
    fidelity_missing: list[str] = []
    fidelity_pass = True

    if reference_dir is not None:
        for stem in required_figures:
            gen_file = fig_dir / f"{stem}.png"
            ref_file = reference_dir / reference_mapping[stem]

            if not gen_file.is_file() or not ref_file.is_file():
                fidelity_missing.append(str(ref_file))
                continue

            metrics = image_similarity_metrics(gen_file, ref_file)
            metrics["threshold"] = threshold
            metrics["pass"] = bool(metrics["composite"] >= threshold)
            fidelity_details[stem] = metrics

            if not metrics["pass"]:
                fidelity_pass = False
    else:
        fidelity_missing = ["reference_dir_not_found"]

    completeness_pass = len(missing) == 0
    if args.require_fidelity:
        fidelity_ready = len(fidelity_missing) == 0
        passed = completeness_pass and fidelity_ready and fidelity_pass
    else:
        passed = completeness_pass

    report = {
        "passed": passed,
        "checked_at_utc": utc_now_iso(),
        "figure_dir": str(fig_dir),
        "required_count": len(required_figures) * 2,
        "missing": missing,
        "artifact_sizes": sizes,
        "fidelity": {
            "enabled": args.require_fidelity,
            "reference_dir": str(reference_dir) if reference_dir else "",
            "threshold": threshold,
            "details": fidelity_details,
            "missing_reference": fidelity_missing,
            "pass": fidelity_pass if len(fidelity_missing) == 0 else False,
        },
        "notes": [
            "Completeness gate validates required PNG/PDF artifacts.",
            "Fidelity gate compares generated PNG vs reference PNG with composite score.",
        ],
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict and not completeness_pass:
        raise SystemExit(1)

    if args.require_fidelity and not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
