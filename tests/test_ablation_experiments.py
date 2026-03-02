from __future__ import annotations

import importlib.util
from pathlib import Path


def load_script_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_all_ablations_report_shape(sample_params_dict: dict[str, float]) -> None:
    module = load_script_module(
        Path("scripts/run_ablation_experiments.py"),
        "run_ablation_experiments",
    )

    module.STRESS_FACTORS = module.np.array([0.8, 1.0, 1.2], dtype=float)

    report = module.run_all_ablations(sample_params_dict)

    assert report["type"] == "ablation-experiments"
    assert isinstance(report["experiments"], list)
    assert len(report["experiments"]) == 4
    ids = {item["id"] for item in report["experiments"]}
    assert ids == {
        "R1_remove_mutualism",
        "R2_weaken_stress_selection",
        "R3_flat_partition",
        "R4_alternative_nonlinearity",
    }
