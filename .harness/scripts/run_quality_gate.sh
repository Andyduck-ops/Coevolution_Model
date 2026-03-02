#!/usr/bin/env bash
set -euo pipefail

if [ ! -x ".venv/bin/python" ]; then
  echo "[ERROR] .venv not found. Run .harness/scripts/bootstrap_env.sh first."
  exit 1
fi

".venv/bin/python" -m ruff check src tests
".venv/bin/python" -m pytest -q
".venv/bin/python" -m compileall -q src
bash .harness/scripts/e2e_smoke.sh

echo "[OK] quality gate passed"
