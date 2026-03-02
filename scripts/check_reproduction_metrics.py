#!/usr/bin/env python3
"""Check figure reproduction artifacts and emit machine-readable report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_FIGURES = [
    "fig1_stability",
    "fig2_timecourse",
    "fig3_spinodal",
    "fig4_post_segregation",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Check reproduction metrics")
    parser.add_argument("--fig-dir", default="figures/paper")
    parser.add_argument("--out", default="results/repro/repro_report.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    fig_dir = Path(args.fig_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    sizes: dict[str, int] = {}

    for stem in REQUIRED_FIGURES:
        png_file = fig_dir / f"{stem}.png"
        pdf_file = fig_dir / f"{stem}.pdf"
        if not png_file.is_file():
            missing.append(str(png_file))
        if not pdf_file.is_file():
            missing.append(str(pdf_file))
        if png_file.is_file():
            sizes[str(png_file)] = png_file.stat().st_size
        if pdf_file.is_file():
            sizes[str(pdf_file)] = pdf_file.stat().st_size

    passed = len(missing) == 0
    report = {
        "passed": passed,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "figure_dir": str(fig_dir),
        "required_count": len(REQUIRED_FIGURES) * 2,
        "missing": missing,
        "artifact_sizes": sizes,
        "notes": [
            "Current gate validates artifact completeness.",
            "Numerical curve-level fidelity metrics will be added in next iteration.",
        ],
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict and not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
