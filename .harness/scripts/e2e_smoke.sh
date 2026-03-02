#!/usr/bin/env bash
set -euo pipefail

if [ ! -x ".venv/bin/python" ]; then
  echo "[ERROR] .venv not found. Run .harness/scripts/bootstrap_env.sh first."
  exit 1
fi

.venv/bin/python scripts/e2e_smoke.py --config "configs/default_params.yaml" --output "results/smoke" --figures "figures/smoke"
