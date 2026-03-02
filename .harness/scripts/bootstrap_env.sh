#!/usr/bin/env bash
set -euo pipefail

UV_BIN="${UV_BIN:-$HOME/.local/bin/uv}"
if [ ! -x "$UV_BIN" ]; then
  echo "[INFO] uv not found at $UV_BIN, installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

if [ -d ".venv" ]; then
  echo "[INFO] .venv already exists, reusing it"
else
  "$UV_BIN" venv .venv
fi

"$UV_BIN" pip install --python .venv/bin/python -e ".[dev]"

echo "[OK] Python environment ready: .venv"
