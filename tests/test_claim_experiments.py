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


def test_run_all_claims_report_shape(sample_params_dict: dict[str, float]) -> None:
    module = load_script_module(Path("scripts/run_claim_experiments.py"), "run_claim_experiments")

    # Speed up tests with smaller stress grid.
    module.STRESS_FACTORS = module.np.array([0.8, 1.0, 1.2], dtype=float)

    report = module.run_all_claims(sample_params_dict)

    assert report["type"] == "claim-experiments"
    assert isinstance(report["experiments"], list)
    assert len(report["experiments"]) == 5
    ids = {item["id"] for item in report["experiments"]}
    assert ids == {
        "E1_monotonic_X_vs_stress",
        "E2_global_stability_no_hysteresis",
        "E3_growth_function_decoupling",
        "E4_spinodal_crossing",
        "E5_post_seg_acceleration",
    }
