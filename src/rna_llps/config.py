"""Configuration helpers for RNA LLPS simulations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED_PARAM_KEYS = {
    "mu_x",
    "mu_y",
    "alpha",
    "beta",
    "kappa",
    "K_R",
    "K_P",
    "V_x",
    "V_y",
    "gamma",
    "delta_0",
    "E",
    "n",
    "v_R",
    "v_P",
    "chi_RR",
    "chi_PP",
    "chi_0",
    "epsilon",
    "k_BT",
}


def load_params(config_path: str | Path) -> dict[str, Any]:
    """Load simulation parameters from YAML.

    Args:
        config_path: Path to YAML parameter file.

    Returns:
        Parsed parameter dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If YAML cannot be parsed as a dictionary.
        KeyError: If required parameter keys are missing.
    """
    path = Path(config_path)
    if not path.is_file():
        msg = f"Parameter file not found: {path}"
        raise FileNotFoundError(msg)

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        msg = "Parameter YAML must be a mapping/dictionary."
        raise ValueError(msg)

    missing = sorted(REQUIRED_PARAM_KEYS - set(data.keys()))
    if missing:
        msg = f"Missing required parameter keys: {', '.join(missing)}"
        raise KeyError(msg)

    return data
