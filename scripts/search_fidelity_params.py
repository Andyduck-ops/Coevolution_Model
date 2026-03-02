#!/usr/bin/env python3
"""Coarse random search for Fig1-4 fidelity-oriented parameter candidates."""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from rna_llps.config import load_params

FIGURE_SCRIPTS = [
    "scripts/fig1_stability.py",
    "scripts/fig2_timecourse.py",
    "scripts/fig3_spinodal.py",
    "scripts/fig4_post_segregation.py",
]

SEARCH_MULTIPLIERS: dict[str, list[float]] = {
    "delta_0": [0.5, 0.8, 1.0, 1.2, 1.5],
    "beta": [0.5, 0.8, 1.0, 1.2, 1.5],
    "kappa": [0.5, 0.8, 1.0, 1.2, 1.5],
    "V_x": [0.5, 0.8, 1.0, 1.2, 1.5],
    "V_y": [0.5, 0.8, 1.0, 1.2, 1.5],
    "gamma": [0.5, 0.8, 1.0, 1.2, 1.5],
    "mu_x": [0.7, 0.9, 1.0, 1.1, 1.3],
    "mu_y": [0.7, 0.9, 1.0, 1.1, 1.3],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sample_params(
    base: dict[str, float],
    rng: random.Random,
    multipliers: dict[str, list[float]] = SEARCH_MULTIPLIERS,
) -> dict[str, float]:
    params = dict(base)
    for key, choices in multipliers.items():
        if key not in params:
            continue
        factor = rng.choice(choices)
        params[key] = float(base[key]) * float(factor)
    return params


def summarize_fidelity(report: dict[str, Any]) -> dict[str, float | int]:
    fidelity = report.get("fidelity", {})
    details = fidelity.get("details", {})
    if not isinstance(details, dict) or not details:
        return {"avg_composite": 0.0, "pass_count": 0, "total_count": 0}

    composites: list[float] = []
    pass_count = 0
    for item in details.values():
        if not isinstance(item, dict):
            continue
        composite = float(item.get("composite", 0.0))
        composites.append(composite)
        if bool(item.get("pass", False)):
            pass_count += 1

    if not composites:
        return {"avg_composite": 0.0, "pass_count": 0, "total_count": 0}
    return {
        "avg_composite": float(sum(composites) / len(composites)),
        "pass_count": int(pass_count),
        "total_count": int(len(composites)),
    }


def run_cmd(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Search fidelity-oriented parameter candidates")
    parser.add_argument("--base-config", default="configs/default_params.yaml")
    parser.add_argument("--metrics-config", default="configs/repro_metrics.yaml")
    parser.add_argument("--reference-dir", default="")
    parser.add_argument("--num-samples", type=int, default=8)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--work-dir", default="results/repro/fidelity_search")
    parser.add_argument("--out", default="results/repro/fidelity_search_report.json")
    parser.add_argument("--emit-configs", action="store_true")
    parser.add_argument("--emit-dir", default="configs/fidelity_candidates")
    args = parser.parse_args()

    root = Path(".").resolve()
    base_config = Path(args.base_config)
    if not base_config.is_file():
        raise SystemExit(f"Base config not found: {base_config}")

    if args.reference_dir:
        reference_dir = Path(args.reference_dir)
    else:
        candidates = sorted(Path(".").glob("COPY1__*"))
        reference_dir = next((c for c in candidates if c.is_dir()), Path(""))
    if not reference_dir or not reference_dir.is_dir():
        raise SystemExit("Reference directory not found. Use --reference-dir explicitly.")

    base_params = load_params(base_config)
    rng = random.Random(args.seed)

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    runs: list[dict[str, Any]] = []
    for idx in range(int(args.num_samples)):
        run_dir = work_dir / f"sample_{idx:03d}"
        fig_dir = run_dir / "figures"
        run_dir.mkdir(parents=True, exist_ok=True)
        fig_dir.mkdir(parents=True, exist_ok=True)

        params = sample_params(base_params, rng)
        cfg_path = run_dir / "params.yaml"
        cfg_path.write_text(yaml.safe_dump(params, sort_keys=True), encoding="utf-8")

        try:
            for script in FIGURE_SCRIPTS:
                run_cmd(
                    [
                        sys.executable,
                        script,
                        "--config",
                        str(cfg_path),
                        "--out",
                        str(fig_dir),
                    ],
                    cwd=root,
                )
            report_path = run_dir / "repro_report.json"
            run_cmd(
                [
                    sys.executable,
                    "scripts/check_reproduction_metrics.py",
                    "--fig-dir",
                    str(fig_dir),
                    "--metrics-config",
                    str(args.metrics_config),
                    "--reference-dir",
                    str(reference_dir),
                    "--out",
                    str(report_path),
                ],
                cwd=root,
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            summary = summarize_fidelity(report)
            runs.append(
                {
                    "sample_id": idx,
                    "params": params,
                    "summary": summary,
                    "repro_report": str(report_path),
                }
            )
        except subprocess.CalledProcessError as exc:
            runs.append(
                {
                    "sample_id": idx,
                    "params": params,
                    "error": f"command failed: {exc.cmd}",
                }
            )

    valid_runs = [r for r in runs if "summary" in r]
    valid_runs.sort(
        key=lambda r: (
            float(r["summary"]["avg_composite"]),
            int(r["summary"]["pass_count"]),
        ),
        reverse=True,
    )
    top_k = valid_runs[: max(int(args.top_k), 0)]

    if args.emit_configs:
        emit_dir = Path(args.emit_dir)
        emit_dir.mkdir(parents=True, exist_ok=True)
        for rank, item in enumerate(top_k, 1):
            path = emit_dir / f"candidate_{rank:02d}.yaml"
            path.write_text(yaml.safe_dump(item["params"], sort_keys=True), encoding="utf-8")
            item["emitted_config"] = str(path)

    output = {
        "type": "fidelity-parameter-search",
        "checked_at_utc": utc_now_iso(),
        "base_config": str(base_config),
        "reference_dir": str(reference_dir),
        "num_samples": int(args.num_samples),
        "top_k": int(args.top_k),
        "seed": int(args.seed),
        "runs": runs,
        "best": top_k,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
