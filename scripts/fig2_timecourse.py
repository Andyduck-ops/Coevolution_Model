#!/usr/bin/env python3
"""Generate Fig2-style time-course trajectories from full ODE wrapper."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from rna_llps.config import load_params
from rna_llps.solvers import solve_full_ode


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Fig2 timecourse")
    parser.add_argument("--config", default="configs/default_params.yaml")
    parser.add_argument("--out", default="figures/paper")
    parser.add_argument("--t-end", type=float, default=40.0)
    args = parser.parse_args()

    params = load_params(args.config)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    result = solve_full_ode(params=params, t_end=args.t_end)
    if not result.success:
        raise RuntimeError(f"solve_full_ode failed: {result.message}")

    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["R", "P", "x_bar", "y_bar"]
    for i, label in enumerate(labels):
        ax.plot(result.t, result.y[i], label=label)
    ax.set_title("Fig2 Time-course")
    ax.set_xlabel("t")
    ax.set_ylabel("state")
    ax.legend()
    ax.grid(alpha=0.25)

    png_path = out_dir / "fig2_timecourse.png"
    pdf_path = out_dir / "fig2_timecourse.pdf"
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Fig2 saved: {png_path}, {pdf_path}")


if __name__ == "__main__":
    main()
