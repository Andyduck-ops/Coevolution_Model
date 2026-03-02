#!/usr/bin/env python3
"""CLI entrypoint for RNA LLPS smoke pipeline."""

from __future__ import annotations

import argparse

from rna_llps.pipeline.smoke import run_smoke


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RNA LLPS E2E smoke simulation.")
    parser.add_argument(
        "--config",
        default="configs/default_params.yaml",
        help="Path to YAML config",
    )
    parser.add_argument("--output", default="results/smoke", help="Output directory for NPZ/JSON")
    parser.add_argument("--figures", default="figures/smoke", help="Output directory for figures")
    parser.add_argument("--t-end", type=float, default=40.0, help="Integration end time")
    args = parser.parse_args()

    artifacts = run_smoke(
        config_path=args.config,
        output_dir=args.output,
        figure_dir=args.figures,
        t_end=args.t_end,
    )

    print("[OK] E2E smoke completed")
    print(f"- npz: {artifacts.npz_path}")
    print(f"- figure: {artifacts.figure_path}")
    print(f"- summary: {artifacts.summary_path}")


if __name__ == "__main__":
    main()
