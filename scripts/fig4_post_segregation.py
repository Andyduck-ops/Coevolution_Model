#!/usr/bin/env python3
"""Generate Fig4-style post-segregation trajectories."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from rna_llps.config import load_params
from rna_llps.models.post_segregation import solve_post_segregation


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Fig4 post-segregation dynamics")
    parser.add_argument("--config", default="configs/default_params.yaml")
    parser.add_argument("--out", default="figures/paper")
    parser.add_argument("--t-end", type=float, default=30.0)
    args = parser.parse_args()

    params = load_params(args.config)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    result = solve_post_segregation(params=params, t_end=args.t_end)
    if not result.success:
        raise RuntimeError(f"solve_post_segregation failed: {result.message}")

    labels = ["R_I", "R_II", "P_I", "P_II", "X_I", "X_II"]

    fig, ax = plt.subplots(figsize=(6, 4))
    for i, label in enumerate(labels):
        ax.plot(result.t, result.y[i], label=label)

    ax.set_title("Fig4 Post-segregation")
    ax.set_xlabel("t")
    ax.set_ylabel("state")
    ax.legend(ncol=2, fontsize=8)
    ax.grid(alpha=0.25)

    png_path = out_dir / "fig4_post_segregation.png"
    pdf_path = out_dir / "fig4_post_segregation.pdf"
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Fig4 saved: {png_path}, {pdf_path}")


if __name__ == "__main__":
    main()
