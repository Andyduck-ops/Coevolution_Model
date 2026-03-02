# implement-result

## 本轮实现范围
- [x] I1: `solve_full_ode()` + `jac_full_system()` + 事件检测 + Radau/BDF 回退
- [x] I2: 热力学与标量函数（`B_n`, `Π_P`, `chi_*`, 两相辅助链）
- [x] I3: `solve_post_segregation()` 两相后分离积分包装
- [x] I4: `critical_stress()` / `compute_spinodal()` 稳定性接口
- [x] I5: Fig1-4 独立脚本 + 复现检查脚本

## 关键新增文件
- `src/rna_llps/solvers/ode_wrappers.py`
- `src/rna_llps/thermo/flory_huggins.py`
- `src/rna_llps/models/scalar_dynamics.py`
- `src/rna_llps/models/post_segregation.py`
- `src/rna_llps/analysis/stability.py`
- `scripts/fig1_stability.py`
- `scripts/fig2_timecourse.py`
- `scripts/fig3_spinodal.py`
- `scripts/fig4_post_segregation.py`
- `scripts/check_reproduction_metrics.py`

## 测试补齐
- [x] `tests/test_flory_huggins.py`
- [x] `tests/test_scalar_dynamics.py`
- [x] `tests/test_ode_wrappers.py`
- [x] `tests/test_post_segregation.py`
- [x] `tests/test_stability_analysis.py`
- [x] `tests/test_reproduction_pipeline.py`
