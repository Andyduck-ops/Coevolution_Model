#!/usr/bin/env python3
"""Generate Fig3-style critical stress scan."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from rna_llps.analysis import critical_stress
from rna_llps.config import load_params


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Fig3 critical-stress scan")
    parser.add_argument("--config", default="configs/default_params.yaml")
    parser.add_argument("--out", default="figures/paper")
    args = parser.parse_args()

    params = load_params(args.config)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    r_scan = np.linspace(0.05, 0.95, 60)
    p_scan = np.linspace(0.05, 0.95, 60)
    stress = np.array(
        [
            critical_stress(params, r=float(r), p=float(p))
            for r, p in zip(r_scan, p_scan, strict=True)
        ]
    )

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(r_scan, stress, lw=2.0, color="tab:purple", label="B_c(r,p)")
    ax.set_title("Fig3 Critical stress scan")
    ax.set_xlabel("scan index (R mapped)")
    ax.set_ylabel("critical stress")
    ax.grid(alpha=0.25)
    ax.legend()

    png_path = out_dir / "fig3_spinodal.png"
    pdf_path = out_dir / "fig3_spinodal.pdf"
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Fig3 saved: {png_path}, {pdf_path}")


if __name__ == "__main__":
    main()
