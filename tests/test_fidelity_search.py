from __future__ import annotations

import importlib.util
import random
from pathlib import Path


def load_script_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sample_params_and_summary(sample_params_dict: dict[str, float]) -> None:
    module = load_script_module(Path("scripts/search_fidelity_params.py"), "search_fidelity_params")

    rng = random.Random(123)
    sampled = module.sample_params(sample_params_dict, rng)
    assert set(sampled.keys()) >= set(sample_params_dict.keys())
    assert sampled["delta_0"] > 0.0
    assert sampled["gamma"] > 0.0

    summary = module.summarize_fidelity(
        {
            "fidelity": {
                "details": {
                    "fig1_stability": {"composite": 0.8, "pass": True},
                    "fig2_timecourse": {"composite": 0.6, "pass": False},
                }
            }
        }
    )
    assert summary["avg_composite"] == 0.7
    assert summary["pass_count"] == 1
    assert summary["total_count"] == 2

