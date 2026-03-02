#!/usr/bin/env python3
"""Generate Fig1-style stability/spinodal visualization."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from rna_llps.analysis import compute_spinodal
from rna_llps.config import load_params


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Fig1 stability map")
    parser.add_argument("--config", default="configs/default_params.yaml")
    parser.add_argument("--out", default="figures/paper")
    args = parser.parse_args()

    params = load_params(args.config)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    spinodal = compute_spinodal(params, n_grid=50)
    rr = spinodal["r_grid"]
    pp = spinodal["p_grid"]
    mask = spinodal["spinodal_mask"]

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.contourf(rr, pp, mask.astype(float), levels=[-0.1, 0.5, 1.1], alpha=0.35, cmap="coolwarm")

    u = np.gradient(rr, axis=0)
    v = np.gradient(pp, axis=1)
    step = 5
    ax.quiver(
        rr[::step, ::step],
        pp[::step, ::step],
        u[::step, ::step],
        v[::step, ::step],
        color="black",
        alpha=0.5,
    )

    ax.set_title("Fig1 Stability / Spinodal map")
    ax.set_xlabel("R")
    ax.set_ylabel("P")
    ax.grid(alpha=0.25)

    png_path = out_dir / "fig1_stability.png"
    pdf_path = out_dir / "fig1_stability.pdf"
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Fig1 saved: {png_path}, {pdf_path}")


if __name__ == "__main__":
    main()
